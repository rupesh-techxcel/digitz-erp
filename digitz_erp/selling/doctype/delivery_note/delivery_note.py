# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.model.document import Document
from frappe.utils.data import now


class DeliveryNote(Document):

    def before_submit(self):
        self.add_stock_for_purchase_receipt()

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
        sales_invoice['naming_series'] = 'SINV-.YYYY.-'
        sales_invoice['posting_date'] = now()
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

    def add_stock_for_purchase_receipt(self):

        for docitem in self.items:			
			
            delivery_qty = docitem.qty_in_base_unit
            outgoing_rate = docitem.rate_in_base_unit						

            posting_date_time = get_datetime(self.posting_date + " " + self.posting_time)			
                                
            dbCount = frappe.db.count('Stock In Ledger',{'posting_date':['<', posting_date_time], 'item': ['=', docitem.item],'warehouse':['=', docitem.warehouse], 'posting_date':['<', posting_date_time]})

            if(dbCount>100):
                last_stock_in_ledger = frappe.db.get_value('Stock In Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse], 'posting_date':['<', posting_date_time]},['balance_qty', 'balance_value'],order_by='posting_date', as_dict=True)
                print(last_stock_in_ledger)
                balance_qty = balance_qty + last_stock_in_ledger.balance_qty 
                balance_value = balance_value + last_stock_in_ledger.balance_value
                valuation_rate = balance_value/balance_qty
            else:
                item = frappe.get_doc('Item', docitem.item)
               

            frappe.throw("Error for dummy")

            # 	print("New Value")
            # 	print(value)

            new_doc = frappe.new_doc('Stock In Ledger')
            new_doc.item = docitem.item
            new_doc.warehouse = docitem.warehouse
            new_doc.posting_date = posting_date_time
            new_doc.qty = docitem.qty_in_base_unit
            new_doc.unit = docitem.base_unit
            new_doc.incoming_rate = docitem.rate_in_base_unit
            new_doc.balance_qty = balance_qty			
            new_doc.balance_value = balance_value
            new_doc.valuation_rate = valuation_rate			
            new_doc.source = "Purchase Invoice Item"
            new_doc.document_id = docitem.name
            new_doc.insert()

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
            new_stock_ledger.posting_date = self.posting_date
            new_stock_ledger.item_code = docitem.item_code

            new_stock_ledger.qty_in = docitem.qty_in_base_unit
            new_stock_ledger.incoming_rate = docitem.rate_in_base_unit
            new_stock_ledger.unit = docitem.base_unit
            new_stock_ledger.valuation_rate = valuation_rate
            new_stock_ledger.balance_qty = balance_qty
            new_stock_ledger.balance_value = balance_value
            new_stock_ledger.source = "Purchase Invoice Item"
            new_stock_ledger.document_id = docitem.name
            new_stock_ledger.insert()	

            item = frappe.get_doc('Item', docitem.item)
            item.stock_balance = item.stock_balance + balance_qty
            item.save()


    
    
       
