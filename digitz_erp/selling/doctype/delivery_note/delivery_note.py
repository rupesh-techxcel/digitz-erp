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
        self.adjust_stock_for_cancel_delivery_note()

    def before_submit(self):
        print("Before submit reached in DN.")
        
        possible_invalid= frappe.db.count('Delivery Note', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time], 'docstatus':['=', 1]})
        
        if(possible_invalid >0):
            frappe.throw("There is another delivery note exist with the same date and time. Please correct the date and time.")

        print(self.docstatus)

        if self.docstatus <2 :
            print("before - deduct stock for delivery note")
            self.deduct_stock_for_delivery_note()
    
    def before_delete(self):
        print("Before Delete From DN")
        frappe.delete_doc("Stock Ledger",{'voucher_no':['=', self.name]})

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
        
        si.append('delivery_notes', {'delivery_note': deliveryNoteName})

        si.docstatus = 1

        si.save()
        
        frappe.msgprint("Sales Invoice created successfully.")

    def adjust_stock_for_cancel_delivery_note(self):

         stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
         stock_recalc_voucher.voucher = 'Delivery Note'
         stock_recalc_voucher.voucher_no = self.name
         stock_recalc_voucher.voucher_date = self.posting_date
         stock_recalc_voucher.voucher_time = self.posting_time
         stock_recalc_voucher.status = 'Not Started'
         stock_recalc_voucher.source_action = 'Cancel'
         stock_recalc_voucher.insert()

         voucher_name = stock_recalc_voucher.name
         stock_recalc_voucher = frappe.get_doc('Stock Recalculate Voucher', voucher_name)

         for docitem in self.items:
            # Adjust stock balance 
            if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}): 
                docName = frappe.get_value('Stock Balance', {'item':docitem.item, 'warehouse':docitem.warehouse}, ['name'] )
                stock_balance_for_item = frappe.get_doc('Stock Balance',docName)
                valuation_rate = stock_balance_for_item.stock_value / stock_balance_for_item.stock_qty

                stock_balance_for_item.stock_qty = stock_balance_for_item.stock_qty + docitem.qty_in_base_unit
                stock_balance_for_item.stock_value = stock_balance_for_item.stock_qty * valuation_rate
                stock_balance_for_item.save()

            stock_ledger_list =frappe.get_list('Stock Ledger', {'voucher':'Delivery Note', 'voucher_no': self.name}, ['name',
                                                                                                                       'item',
                                                                                                                       'warehouse',
                                                                                                                       'qty_in',
                                                                                                                       'incoming_rate',
                                                                                                                       'qty_out',
                                                                                                                       'outgoing_rate',
                                                                                                                       'balance_qty',
                                                                                                                       'balance_value',
                                                                                                                       'valuation_rate',
                                                                                                                       'unit'
                                                                                                                       ])
            print(stock_ledger_list)
            for sl in stock_ledger_list:
                print(sl.name)
                stock_recalc_voucher.append('records',{'item': sl.item, 
                                                        'warehouse': sl.warehouse,
                                                        'qty_in':sl.qty_in,
                                                        'incoming_rate': sl.incoming_rate,
                                                        'qty_out': sl.qty_out,
                                                        'outgoing_rate':sl.outgoing_rate,
                                                        'balance_qty':sl.balance_qty,
                                                        'balance_value':sl.balance_value,
                                                        'valuation_rate':sl.valuation_rate,
                                                        'unit': sl.unit
                    })
                stock_recalc_voucher.save()
                stock_recalc_voucher = frappe.get_doc('Stock Recalculate Voucher', voucher_name)
                frappe.delete_doc('Stock Ledger', sl.name)                
                print(sl.name)


            stock_recalc_voucher.save()
            
            print("stock reclc voucher")
            # print(stock_recalc.name)
            print(str(now))            

         self.recalculate_stock_ledger(stock_recalc_voucher)
         
         frappe.msgprint("Stock balances adjusted successfully.")

        #  frappe.enqueue('digitz_erp.selling.delivery_note.recalculate_stock_ledger','long', stock_recalc_voucher=stock_recalc)

    def recalculate_stock_ledger(self,stock_recalc_voucher_name):

        stock_recalc_voucher = frappe.get_doc("Stock Recalculate Voucher", stock_recalc_voucher_name.name)    
        print(stock_recalc_voucher)
        print(stock_recalc_voucher)

        print("From recalculate_stock_ledger")
        print(stock_recalc_voucher)
        stock_recalc_voucher.status = 'Started'
        stock_recalc_voucher.start_time = now()

        posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))			

        for record in stock_recalc_voucher.records:
            stock_ledger_items = frappe.get_list('Stock Ledger',{'item':record.item,
            'warehouse':record.warehouse, 'posting_date':['>', posting_date_time]},'name')

            print("record")
            print(record)

            for sl_name in stock_ledger_items:
                sl = frappe.get_doc('Stock Ledger', sl_name)
                print(sl)
                sl.balance_qty = sl.balance_qty + record.qty_out
                sl.balance_value = sl.balance_value + (record.qty_out * sl.valuation_rate)
                sl.save()

        stock_recalc_voucher.status = 'Completed'
        stock_recalc_voucher.end_time = now()
        stock_recalc_voucher.save()


    def deduct_stock_for_delivery_note(self):

        for docitem in self.items:			
			
            delivery_qty = docitem.qty_in_base_unit
            outgoing_rate = docitem.rate_in_base_unit						

            post_date_time =  str(self.posting_date) + " " + str(self.posting_time)

            print(post_date_time)

            posting_date_time = get_datetime(post_date_time)
                                            
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
                
            balance_qty = previous_stock_balance.balance_qty - docitem.qty_in_base_unit
            valuation_rate = previous_stock_balance.valuation_rate

            balance_value = previous_stock_balance.balance_value - (docitem.qty * valuation_rate) 


            if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):    
                frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse} )

            new_stock_balance = frappe.new_doc('Stock Balance')	
            new_stock_balance.item = docitem.item
            new_stock_balance.unit = docitem.unit
            new_stock_balance.warehouse = docitem.warehouse
            new_stock_balance.stock_qty = balance_qty
            new_stock_balance.stock_value = balance_value
            new_stock_balance.insert()

            new_stock_ledger = frappe.new_doc("Stock Ledger")
            new_stock_ledger.item = docitem.item
            new_stock_ledger.warehouse = docitem.warehouse
            new_stock_ledger.posting_date = posting_date_time                

            new_stock_ledger.qty_out = docitem.qty_in_base_unit
            new_stock_ledger.outgoing_rate = docitem.rate_in_base_unit
            new_stock_ledger.unit = docitem.base_unit
            new_stock_ledger.valuation_rate = valuation_rate
            new_stock_ledger.balance_qty = balance_qty
            new_stock_ledger.balance_value = balance_value
            new_stock_ledger.voucher = "Delivery Note"
            new_stock_ledger.voucher_no = self.name
            new_stock_ledger.source = "Delivery Note Item"
            new_stock_ledger.source_document_id = docitem.name
            new_stock_ledger.insert()	

            item = frappe.get_doc('Item', docitem.item)
            item.stock_balance = item.stock_balance - docitem.qty_in_base_unit
            item.save()
           