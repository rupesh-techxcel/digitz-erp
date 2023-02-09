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
        

    def before_submit(self):
        self.deduct_stock_for_delivery_note()

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

            if(previous_stock_balance.balance_qty < required_qty):
                frappe.throw("Sufficiant Qty not exists for the item" + docitem.item + " Required Qty=" + str(required_qty) + " Available Qty=" + str(previous_stock_balance.balance_qty) )
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
           