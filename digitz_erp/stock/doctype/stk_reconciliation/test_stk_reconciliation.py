# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now
from frappe.model.document import Document
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_item_stock_balance

class StkReconciliation(Document):
    def before_submit(self):
        
        stock_adjustment_value =  self.add_stock_reconciliation()
        print("new stock change value")
        print(stock_adjustment_value)
        if(stock_adjustment_value !=0):
            self.insert_gl_records(stock_adjustment_value)
      

    def add_stock_reconciliation(self):

        more_records = 0

        stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
        stock_recalc_voucher.voucher = 'Stock Reconciliation'
        stock_recalc_voucher.voucher_no = self.name
        stock_recalc_voucher.voucher_date = self.posting_date
        stock_recalc_voucher.voucher_time = self.posting_time
        stock_recalc_voucher.status = 'Not Started'
        stock_recalc_voucher.source_action = "Insert"
        
        stock_adjustment_value = 0
        
        for docitem in self.items:

            change_in_stock_value_for_item = 0
            
            new_balance_qty = docitem.qty_in_base_unit
            # Default valuation rate
            valuation_rate = docitem.rate_in_base_unit

            posting_date_time = get_datetime(
                str(self.posting_date) + " " + str(self.posting_time))

            # Default balance value calculating withe the current row only
            new_balance_value = new_balance_qty * valuation_rate

            # posting_date<= consider because to take the dates with in the same minute
            # dbCount = frappe.db.count('Stock Ledger',{'item_code': ['=', docitem.item_code],'warehouse':['=', docitem.warehouse], 'posting_date':['<=', posting_date_time]})
            dbCount = frappe.db.count('Stock Ledger', {'item_code': ['=', docitem.item_code], 'warehouse': [
                                      '=', docitem.warehouse], 'posting_date': ['<', posting_date_time]})
            
            # In case opening stock entry, assign the qty as qty_in
            qty_in = docitem.qty_in_base_unit
            qty_out =0
            
            if (dbCount > 0):

                # Find out the balance value and valuation rate. Here recalculates the total balance value and valuation rate
                # from the balance qty in the existing rows x actual incoming rate

                last_stock_ledger = frappe.db.get_value('Stock Ledger', {'item_code': ['=', docitem.item_code], 'warehouse': ['=', docitem.warehouse], 'posting_date': [
                                                        '<', posting_date_time]}, ['balance_qty', 'balance_value', 'valuation_rate'], order_by='posting_date desc', as_dict=True)
                
                previous_stock_balance_qty = last_stock_ledger.balance_qty                           
                
                if(previous_stock_balance_qty> new_balance_qty):
                    qty_out = previous_stock_balance_qty - new_balance_qty
                else:
                    qty_in = new_balance_qty - previous_stock_balance_qty
                    
                previous_stock_value = last_stock_ledger.balance_value
                
                if(new_balance_value> previous_stock_value): # stock value raised
                    stock_adjustment_value = stock_adjustment_value + (new_balance_value - previous_stock_value)
                    change_in_stock_value_for_item = (new_balance_value - previous_stock_value)
                elif(previous_stock_value>new_balance_value): # stock value diminished: 
                    stock_adjustment_value = stock_adjustment_value - (previous_stock_value -new_balance_value)                
                    change_in_stock_value_for_item = new_balance_value - previous_stock_value
            else:
                stock_adjustment_value = stock_adjustment_value + new_balance_value
                change_in_stock_value_for_item = new_balance_value
                    
            new_stock_ledger = frappe.new_doc("Stock Ledger")
            new_stock_ledger.item = docitem.item
            new_stock_ledger.warehouse = docitem.warehouse
            new_stock_ledger.posting_date = posting_date_time
            new_stock_ledger.change_in_stock_value = change_in_stock_value_for_item

            new_stock_ledger.qty_in = qty_in
            
            print("qty_in")
            print(qty_in)
            
            new_stock_ledger.qty_out = qty_out            
            new_stock_ledger.unit = docitem.base_unit
            
            if(qty_in >0):
                new_stock_ledger.incoming_rate = valuation_rate
            
            if(qty_out >0):
                new_stock_ledger.outgoing_rate = valuation_rate
            
            new_stock_ledger.valuation_rate = valuation_rate
            new_stock_ledger.balance_qty = new_balance_qty
            new_stock_ledger.balance_value = new_balance_value            
            new_stock_ledger.voucher = "Stock Reconciliation"
            new_stock_ledger.voucher_no = self.name
            new_stock_ledger.source = "Stock Reconciliation Item"
            new_stock_ledger.source_document_id = docitem.name
            new_stock_ledger.insert()
            
            more_records_count_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
				'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})
   
            more_records = more_records + more_records_count_for_item
        
            if(more_records_count_for_item>0):
      
                stock_recalc_voucher.append('records',{'item': docitem.item, 
                                                            'warehouse': docitem.warehouse,                                                        
                                                            'base_stock_ledger': new_stock_ledger.name
                                                            })
                
            else:
                if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):    
                    frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse} )
                    
                new_stock_balance = frappe.new_doc('Stock Balance')	
                new_stock_balance.item = docitem.item
                new_stock_balance.unit = docitem.base_unit
                new_stock_balance.warehouse = docitem.warehouse
                new_stock_balance.stock_qty = new_balance_qty
                new_stock_balance.stock_value = new_balance_value
                new_stock_balance.valuation_rate = valuation_rate

                new_stock_balance.insert()

                item_name = frappe.get_value("Item", docitem.item,['item_name'])
                update_item_stock_balance(item_name)					

        if(more_records>0):
            stock_recalc_voucher.insert()
            recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)
        
        print("from method")
        print(stock_adjustment_value)
        return stock_adjustment_value
    
    def on_cancel(self):        	
        self.cancel_stock_reconciliation()
        
    def cancel_stock_reconciliation(self):
     
        # Insert record to 'Stock Recalculate Voucher' doc
        stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
        stock_recalc_voucher.voucher = 'Purchase Invoice'
        stock_recalc_voucher.voucher_no = self.name
        stock_recalc_voucher.voucher_date = self.posting_date
        stock_recalc_voucher.voucher_time = self.posting_time
        stock_recalc_voucher.status = 'Not Started'
        stock_recalc_voucher.source_action = "Cancel"
        
        posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))					

        more_records = 0

        # Iterate on each item from the cancelling purchase invoice
        for docitem in self.items:	
            more_records_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
                'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})

            more_records = more_records + more_records_for_item

            previous_stock_ledger_name = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
                        , 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)

            # If any items in the collection has more records
            if(more_records_for_item>0):
                
                stock_ledger_items = frappe.get_list('Stock Ledger',{'item':docitem.item,
                'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]}, ['name','qty_in','qty_out','voucher','balance_qty','voucher_no'],order_by='posting_date')

                if(stock_ledger_items):

                    qty_cancelled = docitem.qty_in_base_unit
                    # Loop to verify the sufficiant quantity
                    for sl in stock_ledger_items:					
                        # On each line if outgoing qty + balance_qty (qty before outgonig) is more than the cancelling qty
                        if(sl.qty_out>0 and qty_cancelled> sl.qty_out+ sl.balance_qty):
                            frappe.throw("Cancelling the stock reconciliation is prevented due to sufficiant quantity not available for " + docitem.item +
                        " to fulfil the voucher " + sl.voucher_no)
            
                if(previous_stock_ledger_name):					
                    stock_recalc_voucher.append('records',{'item': docitem.item, 
                                                            'warehouse': docitem.warehouse,
                                                            'base_stock_ledger': previous_stock_ledger_name 
                                                            })
                
                else:
                    stock_recalc_voucher.append('records',{'item': docitem.item, 
															'warehouse': docitem.warehouse,
															'base_stock_ledger': "No Previous Ledger"
															})
            else:
        
                stock_balance = frappe.get_value('Stock Balance', {'item':docitem.item, 'warehouse':docitem.warehouse}, ['name'] )
                balance_qty =0
                balance_value =0
                valuation_rate  = 0

                if(previous_stock_ledger_name):
                    previous_stock_ledger = frappe.get_doc('Stock Ledger',previous_stock_ledger_name) 
                    balance_qty = previous_stock_ledger.balance_qty
                    balance_value = previous_stock_ledger.balance_value
                    valuation_rate = previous_stock_ledger.valuation_rate
        
                stock_balance_for_item = frappe.get_doc('Stock Balance',stock_balance) 
                # Add qty because of balance increasing due to cancellation of delivery note
                stock_balance_for_item.stock_qty = balance_qty
                stock_balance_for_item.stock_value = balance_value
                stock_balance_for_item.valuation_rate = valuation_rate
                stock_balance_for_item.save()                    

                item_name = frappe.get_value("Item", docitem.item,['item_name'])
                update_item_stock_balance(item_name)	
        
        if(more_records>0):
            stock_recalc_voucher.insert()
            recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)

        frappe.db.delete("Stock Ledger",
                {"voucher": "Stock Reconciliation",
                    "voucher_no":self.name
                })

        frappe.db.delete("GL Posting",
                {"Voucher_type": "Stock Reconciliation",
                    "voucher_no":self.name
                })   
                 
    # def recalculate_stock_ledgers(self,stock_recalc_voucher):
            
    #     posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))  		

    #     for record in stock_recalc_voucher.records:
            
    #         new_balance_qty = 0
    #         new_balance_value = 0
    #         new_valuation_rate = 0
            
    #         if record.base_stock_ledger != "No Previous Ledger":
                
    #             base_stock_ledger = frappe.get_doc('Stock Ledger', record.base_stock_ledger)            
    #             new_balance_qty = base_stock_ledger.balance_qty
    #             new_balance_value = base_stock_ledger.balance_value
    #             new_valuation_rate = base_stock_ledger.valuation_rate
            
    #         next_stock_ledgers = frappe.get_list('Stock Ledger',{'item':record.item,
    #         'warehouse':record.warehouse, 'posting_date':['>', posting_date_time]}, 'name',order_by='posting_date')

    #         # Scenario 1- PUrchase Invoice - current row cancelled. For this assigned previous stock ledger balance to 'Stock Recalculate Voucher'

    #         for sl_name in next_stock_ledgers:
                
    #             sl = frappe.get_doc('Stock Ledger', sl_name)
                
    #             qty_in = 0
    #             qty_out = 0
                
    #             # if the control meets a stock reconciliation record, its mandatory that to keep the stock balance in the record
    #             # as it is. So it requires to adjust the qty_in or qty_out to preserve the stock balance. Also the valuation_rate should be
    #             # preserved
    #             if(sl.voucher == "Stock Reconciliation"):
    #                 if(sl.balance_qty > new_balance_qty):
    #                     qty_in = sl.balance_qty - new_balance_qty
    #                 else:
    #                     qty_out = new_balance_qty -sl.balance_qty                    
                
    #                 sl.qty_in = qty_in
    #                 sl.qty_out = qty_out
                    
    #                 # Previous stock value difference
    #                 previous_balance_value = new_balance_value #Assign before change        
    #                 sl.change_in_stock_value =   (sl.balance_value - previous_balance_value) 
                                        
    #                 new_valuation_rate = sl.valuation_rate                    
    #                 new_balance_qty = sl.balance_qty
    #                 new_balance_value = sl.balance_value                    
                                        
                    
    #                 # Once qty adjusted exit for next item, since after manual entry subsequent entries are not considered
    #                 sl.save()
    #                 break;
                
    #             if(sl.voucher == "Delivery Note"):
    #                 previous_balance_value = new_balance_value #Assign before change                    
    #                 new_balance_qty = new_balance_qty - sl.qty_out
    #                 new_balance_value = new_balance_qty * new_valuation_rate
    #                 change_in_stock_value = new_balance_value - previous_balance_value
    #                 sl.change_in_stock_value = change_in_stock_value
                    
    #             if(new_balance_qty<0):
    #                 frappe.throw("Stock availability is not sufficiant to make thistransaction, the delivery note " + sl.voucher_no + " cannot be fulfilled.")
                                        
    #             if (sl.voucher == "Purchase Invoice"):
    #                 previous_balance_value = new_balance_value #Assign before change        
    #                 new_balance_qty = new_balance_qty + sl.qty_in
    #                 new_balance_value = new_balance_value  + (sl.qty_in * sl.incoming_rate)
    #                 change_in_stock_value = new_balance_value - previous_balance_value
    #                 sl.change_in_stock_value = change_in_stock_value

    #                 if(new_balance_qty!=0): #Avoid divisible by zero
    #                     new_valuation_rate = new_balance_value/ new_balance_qty
                
    #             sl.balance_qty = new_balance_qty
    #             sl.balance_value = new_balance_value
    #             sl.valuation_rate = new_valuation_rate
                
    #             sl.save()

    #         if frappe.db.exists('Stock Balance', {'item':record.item,'warehouse': record.warehouse}):    
    #             frappe.db.delete('Stock Balance',{'item': record.item, 'warehouse': record.warehouse} )

    #         item_name,unit = frappe.get_value("Item", record.item,['item_name','base_unit'])
    #         new_stock_balance = frappe.new_doc('Stock Balance')	
    #         new_stock_balance.item = record.item
    #         new_stock_balance.unit = unit
    #         new_stock_balance.warehouse = record.warehouse
    #         new_stock_balance.stock_qty = new_balance_qty
    #         new_stock_balance.stock_value = new_balance_value
    #         new_stock_balance.valuation_rate = new_valuation_rate

    #         new_stock_balance.insert()

    #         item_name = frappe.get_value("Item", record.item,['item_name'])
    #         self.update_item_stock_balance(item_name)

    #         stock_recalc_voucher.status = 'Completed'
    #         stock_recalc_voucher.end_time = now()
    #         stock_recalc_voucher.save()
    
    # def update_item_stock_balance(self, item):
    
    #     item_balances_in_warehouses = frappe.get_list('Stock Balance',{'item': item},['stock_qty','stock_value'])

    #     balance_stock_qty = 0
    #     balance_stock_value = 0

    #     if(item_balances_in_warehouses):
            
    #         for item_stock in item_balances_in_warehouses:
    #             if item_stock.stock_qty:
    #                 balance_stock_qty = balance_stock_qty + item_stock.stock_qty

    #             if item_stock.stock_value:
    #                 balance_stock_value = balance_stock_value + item_stock.stock_value

    #     item_to_update = frappe.get_doc('Item', item)	
                
    #     if(not item_to_update.stock_balance):	
        
    #         item_to_update.stock_balance = 0
    #         item_to_update.stock_value = 0
            
    #     item_to_update.stock_balance = balance_stock_qty
    #     item_to_update.stock_value = balance_stock_value                
    #     item_to_update.save()
    
    def insert_gl_records(self, stock_adjustment_value):

        print("From insert gl records")

        default_company = frappe.db.get_single_value(
            "Global Settings", "default_company")

        default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                            'default_income_account', 'stock_adjustment_account', 'round_off_account', 'tax_account'], as_dict=1)

        idx = 1

        # Inventory account Eg: Stock In Hand
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Delivery Note"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.default_inventory_account
        if stock_adjustment_value > 0: #Value Raised
            gl_doc.debit_amount = stock_adjustment_value
        else:
            gl_doc.credit_amount = stock_adjustment_value            
        
        gl_doc.aginst_account = default_accounts.stock_adjustment_account
        gl_doc.insert()

        # Cost Of Goods Sold
        idx = 2
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Delivery Note"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.stock_adjustment_account
        
        if stock_adjustment_value > 0: # Value diminished
            gl_doc.credit_amount = stock_adjustment_value
        else:
            gl_doc.debit_amount = stock_adjustment_value
            
        gl_doc.aginst_account = default_accounts.default_inventory_account
        gl_doc.insert()