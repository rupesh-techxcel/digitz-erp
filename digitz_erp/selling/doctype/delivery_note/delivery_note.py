# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from datetime import datetime
from frappe.model.document import Document
from frappe.utils.data import now

class DeliveryNote(Document):

    # def validate(self):
    #     self.validate_stock()

    def validate_stock(self):
        posting_date_time = get_datetime(self.posting_date + " " + self.posting_time)			

    def before_cancel(self):
        print("before cancel in DN")  
        
     
    def on_cancel(self):
        print("on cancel in DN")
        self.cancel_delivery_note()
        
        frappe.db.delete("Stock Ledger",
				{"voucher": "Delivery Note",
				 "voucher_no":self.name
				})
	
        frappe.db.delete("GL Posting",
				{"Voucher_type": "Delivery Note",
				 "voucher_no":self.name
				})
    

    def before_submit(self):        
        
        possible_invalid= frappe.db.count('Delivery Note', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time], 'docstatus':['=', 1]})
        
        if(possible_invalid >0):
            frappe.throw("There is another delivery note exist with the same date and time. Please correct the date and time.")

        self.validate_item()
        
        if self.docstatus <2 :
            print("before - deduct stock for delivery note")
            cost_of_goods_sold = self.deduct_stock_for_delivery_note_add()
            self.insert_gl_records(cost_of_goods_sold)

    def validate_item(self):

        print("From validate item, DN")
         
        posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))		        	
      
        for docitem in self.items:

            print(docitem.item)
            
            # previous_stocks = frappe.db.get_value('Stock Ledger', {'item':docitem.item,'warehouse': docitem.warehouse , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],order_by='posting_date desc', as_dict=True)
            
            previous_stock_balance = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
            , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
            order_by='posting_date desc', as_dict=True)

            if(not previous_stock_balance): 
                frappe.throw("No stock exists for" + docitem.item )
        
            if(previous_stock_balance.balance_qty< docitem.qty_in_base_unit):
                frappe.throw("Sufficiant qty does not exists for the item " + docitem.item + " required Qty= " + str(docitem.qty_in_base_unit) + 
                " " + docitem.base_unit + " and available Qty=" + str(previous_stock_balance.balance_qty) + " " + docitem.base_unit )
    

    # def validate_item_for_existing_transactions(self, item, warehouse,posting_date_time, qty):
    #     balance_list = frappe.get_list('Stock Ledger',{'item':item,'warehouse':warehouse,'posting_date':['>', posting_date_time],'qty_out':['>',0]},['balance_qty'])

    #     for balance in balance_list:
    
    def before_delete(self):
        print("Before Delete From DN")        

    def on_trash(self):
        print("On Trash from DN")        
        # frappe.delete_doc("Stock Ledger",{'voucher_no':['=', self.name]})

    @frappe.whitelist()
    def generate_sale_invoice(self):
        sales_invoice_name = ""
        # do_exists = 0
        # if frappe.db.exists('Sales Invoice', {"against_sales_invoice": self.name}):
        #     sales_invoice_doc = frappe.get_doc(
        #         'Sales Invoice', {"against_sales_invoice": self.name})
        #     sales_invoice_name = sales_invoice_doc.name
        #     sales_invoice_doc.delete()
        #     do_exists = 1
        
        deliveryNoteName =  self.name
        sales_invoice = self.__dict__
        sales_invoice['doctype'] = 'Sales Invoice'
        sales_invoice['name'] = sales_invoice_name
        sales_invoice['naming_series'] = ""
        sales_invoice['posting_date'] = self.posting_date
        sales_invoice['posting_time'] = self.posting_time
        sales_invoice['delivery_note'] =deliveryNoteName
        # Change the document status to draft to avoid error while submitting child table
        sales_invoice['docstatus'] = 0
        for item in sales_invoice['items']:            
            item.doctype = "Sales Invoice Item"
            item.delivery_note_item_reference_no = item.name
            item._meta = ""       
         
        sales_invoice_doc = frappe.get_doc(
            sales_invoice).insert(ignore_permissions=True)               
        
        frappe.db.commit()        
        
        print(sales_invoice_doc.name)

        si =  frappe.get_doc('Sales Invoice',sales_invoice_doc.name)

        # Add reference link to the 'Sales Invoice Delivery NOtes' child doctype
        
        si.append('delivery_notes', {'delivery_note': deliveryNoteName})

        si.docstatus = 1

        si.save()
        
        frappe.msgprint("Sales Invoice created successfully.")

    def cancel_delivery_note(self):
        
        # posting_date_time =  get_datetime(str(self.posting_date) + " " + str(self.posting_time))

        # any_for_more = False

        # for docitem in self.items:

        #     # For cancel delivery note balance qty logic is safe because it only add the qty back to the stock.
        #     next_ledger_name = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
        #         , 'posting_date':['>', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)
            
        #     if next_ledger_name:
        #         any_for_more = True        
                
        #     previous_stock_ledger_name = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
        #         , 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)
            

        #     stock_balance = frappe.get_value('Stock Balance', {'item':docitem.item, 'warehouse':docitem.warehouse}, ['name'] )
            
        #     # Not likely to occur
        #     if(not stock_balance):
        #         frappe.throw("Stock Balance record not found for the item in the warehouse")
        #     else: 
        #         if(not any_for_more):
        #             previous_stock_ledger = frappe.get_doc('Stock Ledger',previous_stock_ledger_name) 
        #             stock_balance_for_item = frappe.get_doc('Stock Balance',stock_balance) 
        #             # Add qty because of balance increasing due to cancellation of delivery note
        #             stock_balance_for_item.stock_qty = previous_stock_ledger.balance_qty
        #             stock_balance_for_item.stock_value = previous_stock_ledger.balance_value
        #             stock_balance_for_item.save()
                    
        #             item_name = frappe.get_value("Item", docitem.item,['item_name'])
        #             self.update_item_stock_balance(item_name)					

        # if(any_for_more):
        self.recalculate_stock_ledgers("Cancel","")      
    

    def recalculate_stock_ledgers(self, operation, new_stock_ledger_name):

        # Insert record to 'Stock Recalculate Voucher' doc
        stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
        stock_recalc_voucher.voucher = 'Delivery Note'
        stock_recalc_voucher.voucher_no = self.name
        stock_recalc_voucher.voucher_date = self.posting_date
        stock_recalc_voucher.voucher_time = self.posting_time
        stock_recalc_voucher.status = 'Not Started'
        stock_recalc_voucher.source_action = operation
        stock_recalc_voucher.insert()

        voucher_name = stock_recalc_voucher.name

        posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))	

        # Stock Recalculate Voucher holds the entry, and records to help the calculation in the subsequent stock ledgers
        stock_recalc_voucher = frappe.get_doc('Stock Recalculate Voucher', voucher_name)

        for docitem in self.items:

        # more_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
        # 	'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})

        # # Do not continue if more items is nto exists for the item
        # if(more_for_item ==0):
        # 	continue   

            balance_qty = 0
            valuation_rate = 0
            balance_value = 0
            qty_in = 0
            qty_out =0
            rate_in = 0
            rate_out = 0

            if(operation == "Cancel"):	
                
                # For cancel purchase invoice , fetch the previous stock ledger balance. since the stock ledger corresponding to the 
                # cancelling invoice is not valid
                posting_date_time = get_datetime(str(stock_recalc_voucher.voucher_date) + " " + str(stock_recalc_voucher.voucher_time))
                previous_ledger_name = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
                    , 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)
                    
                if(previous_ledger_name):					
                    previous_stock_ledger = frappe.get_doc('Stock Ledger',previous_ledger_name.name)
                    qty_in = previous_stock_ledger.qty_in
                    qty_out = previous_stock_ledger.qty_out
                    rate_in = previous_stock_ledger.incoming_rate
                    rate_out = previous_stock_ledger.outgoing_rate 
                    balance_qty = previous_stock_ledger.balance_qty
                    balance_value = previous_stock_ledger.balance_value
                    valuation_rate = balance_value / balance_qty

                stock_recalc_voucher.append('records',{'item': docitem.item, 
                                                            'warehouse': docitem.warehouse,                                                        
                                                            'qty_in': qty_in,      
                                                            'incoming_rate': rate_in,
                                                            'qty_out': qty_out,
                                                            'outgoing_rate':rate_out,
                                                            'balance_qty':balance_qty,
                                                            'balance_value':balance_value,
                                                            'valuation_rate':valuation_rate,
                                                            'unit': docitem.unit
                                                            })
                    
            if(operation == "Insert"):
                
                # When adding Delivery Note, take the corresponding stock ledger values(newly added stock ledger in the parent method)
                stock_ledger = frappe.get_doc("Stock Ledger", new_stock_ledger_name)				
                stock_recalc_voucher.append('records',{'item': docitem.item, 
                                                        'warehouse': docitem.warehouse,                                                        
                                                        'qty_in': stock_ledger.qty_in,      
                                                        'incoming_rate': stock_ledger.incoming_rate,
                                                        'qty_out': stock_ledger.qty_out,
                                                        'outgoing_rate':stock_ledger.outgoing_rate,
                                                        'balance_qty':stock_ledger.balance_qty,
                                                        'balance_value':stock_ledger.balance_value,
                                                        'valuation_rate':stock_ledger.valuation_rate,
                                                        'unit': docitem.unit
                                                        })			

        recalc_voucher = stock_recalc_voucher.insert()		

        # stock_recalc_voucher.save()
        self.recalculate_subsequent_stock_ledgers(recalc_voucher)         


    def recalculate_subsequent_stock_ledgers(self,recalc_voucher):
     
        stock_recalc_voucher = frappe.get_doc("Stock Recalculate Voucher", recalc_voucher.name)
		
        if(stock_recalc_voucher):
            print("No Error")
        
            print(stock_recalc_voucher)			
        else:
            print("Error")
  
  
		# stock_recalc_voucher = frappe.get_doc("Stock Recalculate Voucher", stock_recalc_voucher_name)      
        stock_recalc_voucher.status = 'Started'
        stock_recalc_voucher.start_time = now()
        print(stock_recalc_voucher)
        print(stock_recalc_voucher.records)

        posting_date_time = get_datetime(str(stock_recalc_voucher.voucher_date) + " " + str(stock_recalc_voucher.voucher_time))			

        for record in stock_recalc_voucher.records:
        	
            balance_qty = record.balance_qty
            balance_value = record.balance_value
            valuation_rate = record.valuation_rate
            qty_in = record.qty_in
            incoming_rate = record.incoming_rate
            qty_out = record.qty_out
            outgoing_rate = record.outgoing_rate			
            
            stock_ledger_items = frappe.get_list('Stock Ledger',{'item':record.item,
			'warehouse':record.warehouse, 'posting_date':['>', posting_date_time]}, 'name',order_by='posting_date')
   
			# Scenario 1- PUrchase Invoice - current row cancelled. For this assigned previous stock ledger balance to 'Stock Recalculate Voucher'

            for sl_name in stock_ledger_items:
                sl = frappe.get_doc('Stock Ledger', sl_name)
                print(sl)
				
                if(sl.voucher == "Delivery Note"):
                    balance_qty = balance_qty - sl.qty_out
                    balance_value = balance_qty * valuation_rate
                    
                if (sl.voucher == "Purchase Invoice"):
                    balance_qty = balance_qty + sl.qty_in
                    balance_value = balance_value  + (sl.qty_in * sl.incoming_rate)
     
                if(balance_qty!=0): #Avoid divisible by zero
                    valuation_rate = balance_value/ balance_qty						
				
                sl.balance_qty = balance_qty
                sl.balance_value = balance_value
                sl.valuation_rate = valuation_rate
                
                sl.save()
    
            if frappe.db.exists('Stock Balance', {'item':record.item,'warehouse': record.warehouse}):    
                frappe.db.delete('Stock Balance',{'item': record.item, 'warehouse': record.warehouse} )

            new_stock_balance = frappe.new_doc('Stock Balance')	
            new_stock_balance.item = record.item
            new_stock_balance.unit = record.unit
            new_stock_balance.warehouse = record.warehouse
            new_stock_balance.stock_qty = balance_qty
            new_stock_balance.stock_value = balance_value
            new_stock_balance.valuation_rate = valuation_rate

            new_stock_balance.insert()

            item_name = frappe.get_value("Item", record.item,['item_name'])
            self.update_item_stock_balance(item_name)					

        stock_recalc_voucher.status = 'Completed'
        stock_recalc_voucher.end_time = now()
        stock_recalc_voucher.save()

    def deduct_stock_for_delivery_note_add(self):

        cost_of_goods_sold = 0

        more_records = 0

        for docitem in self.items:			

            posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))  		
   
     		# Check for more records after this date time exists. This is mainly for deciding whether stock balance needs to update
	    	# in this flow itself. If more records, exists stock balance will be udpated lateer
            more_records_count_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
				'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})
   
            more_records = more_records + more_records_count_for_item
            
            required_qty = docitem.qty_in_base_unit
            
            # Check available qty
            previous_stock_balance = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
            , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
            order_by='posting_date desc', as_dict=True)

            if(not previous_stock_balance): 
                frappe.throw("No stock exists for" + docitem.item )

            if(previous_stock_balance.balance_qty < required_qty):
                frappe.throw("Sufficiant qty does not exists for the item " + docitem.item + " Required Qty= " + str(required_qty) + " " +
                 docitem.base_unit + "and available Qty= " + str(previous_stock_balance.balance_qty) + " " + docitem.base_unit)
                return
                
            new_balance_qty = previous_stock_balance.balance_qty - docitem.qty_in_base_unit
            valuation_rate = previous_stock_balance.valuation_rate

            new_balance_value = previous_stock_balance.balance_value - (docitem.qty_in_base_unit * valuation_rate) 
            cost_of_goods_sold = cost_of_goods_sold + (docitem.qty_in_base_unit * valuation_rate) 


            if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):    
                frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse} )

            new_stock_ledger = frappe.new_doc("Stock Ledger")
            new_stock_ledger.item = docitem.item
            new_stock_ledger.warehouse = docitem.warehouse
            new_stock_ledger.posting_date = posting_date_time                

            new_stock_ledger.qty_out = docitem.qty_in_base_unit
            new_stock_ledger.outgoing_rate = docitem.rate_in_base_unit
            new_stock_ledger.unit = docitem.base_unit
            new_stock_ledger.valuation_rate = valuation_rate
            new_stock_ledger.balance_qty = new_balance_qty
            new_stock_ledger.balance_value = new_balance_value
            new_stock_ledger.voucher = "Delivery Note"
            new_stock_ledger.voucher_no = self.name
            new_stock_ledger.source = "Delivery Note Item"
            new_stock_ledger.source_document_id = docitem.name
            new_stock_ledger.insert()	

            # If no more records for the item, update balances. otherwise it updates in the flow
            if more_records_count_for_item==0: 
                if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):    
                    frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse} )

                new_stock_balance = frappe.new_doc('Stock Balance')	
                new_stock_balance.item = docitem.item
                new_stock_balance.unit = docitem.unit
                new_stock_balance.warehouse = docitem.warehouse
                new_stock_balance.stock_qty = new_balance_qty
                new_stock_balance.stock_value = new_balance_value
                new_stock_balance.valuation_rate = valuation_rate

                new_stock_balance.insert()
                
                item_name = frappe.get_value("Item", docitem.item,['item_name'])
                self.update_item_stock_balance(item_name)

        if(more_records>0):
            self.recalculate_stock_ledgers("Insert",new_stock_ledger.name)
        
        return cost_of_goods_sold
    
    def update_item_stock_balance(self, item):
     
        item_balances_in_warehouses = frappe.get_list('Stock Balance',{'item': item},['stock_qty','stock_value'])
  
        balance_stock_qty = 0
        balance_stock_value = 0

        if(item_balances_in_warehouses):
            for item_stock in item_balances_in_warehouses:
                if item_stock.stock_qty:
                    balance_stock_qty = balance_stock_qty + item_stock.stock_qty

                if item_stock.stock_value:
                    balance_stock_value = balance_stock_value + item_stock.stock_value
	
		
        item_to_update = frappe.get_doc('Item', item)	
                
        if(not item_to_update.stock_balance):	
        
            item_to_update.stock_balance = 0
            item_to_update.stock_value = 0
            
        item_to_update.stock_balance = balance_stock_qty
        item_to_update.stock_value = balance_stock_value                
        item_to_update.save()	

    def insert_gl_records(self, cost_of_goods__sold):

        print("From insert gl records")

        default_company = frappe.db.get_single_value(
            "Global Settings", "default_company")

        default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                         'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)

        idx = 1

        # Inventory account Eg: Stock In Hand
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Delivery Note"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.default_inventory_account
        gl_doc.debit_amount = cost_of_goods__sold
        gl_doc.party_type = "Customer"
        gl_doc.party = self.customer
        gl_doc.aginst_account = default_accounts.cost_of_goods_sold_account
        gl_doc.insert()

        # Cost Of Goods Sold
        idx = 2
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Delivery Note"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.cost_of_goods_sold_account
        gl_doc.credit_amount = cost_of_goods__sold
        gl_doc.aginst_account = default_accounts.default_inventory_account
        gl_doc.insert()
              
