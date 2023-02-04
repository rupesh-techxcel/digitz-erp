# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.model.document import Document
from frappe.utils.data import now


class DeliveryNote(Document):

    # def validate(self):
    #     self.validate_stock()

    def validate_stock(self):
        posting_date_time = get_datetime(self.posting_date + " " + self.posting_time)			
        
        for docitem in self.items:
            available_qty =0
            previous_stocks = frappe.db.get_list('Stock In Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse], 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],order_by='posting_date', as_list=True)
            for stock_for_balance in previous_stocks:
                available_qty = available_qty + stock_for_balance.balance_qty
                if(available_qty< docitem.qty_in_base_unit):
                    frappe.throw("No sufficient qty exists for the item " + docitem.item)

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
                                
            dbCount = frappe.db.count('Stock In Ledger',{'item': ['=', docitem.item],'warehouse':['=', docitem.warehouse], 'posting_date':['<', posting_date_time]})

            if(dbCount>0):

                required_qty = docitem.qty_in_base_unit
                # Check available qty
                available_qty =0
                previous_stocks = frappe.db.get_list('Stock In Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse], 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],order_by='posting_date', as_dict=True)
                for stock_for_balance in previous_stocks:
                    available_qty = available_qty + stock_for_balance.balance_qty
                if(available_qty< required_qty):
                    frappe.throw("No sufficient qty exists for the item " + docitem.item)
                    return

                valuation_rate = 0
                # Get the last record for valuation rate
                last_stock_in_ledger = frappe.db.get_value('Stock In Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse], 'posting_date':['<', posting_date_time]},['balance_qty', 'balance_value','valuation_rate'],order_by='posting_date desc', as_dict=True)
                valuation_rate = last_stock_in_ledger.valuation_rate

                gathered_qty = 0

                for stock in previous_stocks:
                    # If stock in the record is sufficient
                    if stock.balance_qty>= required_qty:
                        gathered_qty= required_qty
                    # since stock is not sufficient take the available stock
                    else:
                        gathered_qty= stock_in_ledger_doc.balance_qty

                    stock_in_ledger_doc = frappe.get_doc('Stock In Ledger', stock.name)
                    stock_in_ledger_doc.used_qty = stock_in_ledger_doc.used_qty + gathered_qty
                    stock_in_ledger_doc.balance_qty = stock_in_ledger_doc.balance_qty - gathered_qty
                    stock_in_ledger_doc.save()

                    stock_out_ledger = frappe.new_doc("Stock Out Ledger")
                    stock_out_ledger.item = docitem.item
                    stock_out_ledger.voucher = "Delivery Note"
                    stock_out_ledger.voucher_no = self.name
                    stock_out_ledger.posting_date = posting_date_time
                    stock_out_ledger.qty =  gathered_qty
                    stock_out_ledger.stock_in_ledger = "Stock In Ledger"
                    stock_out_ledger.stock_in_ledger_id = stock.name
                    stock_out_ledger.qty_used = gathered_qty                    
                    stock_out_ledger.insert()

                    if gathered_qty== required_qty:
                        break
                    
                    required_qty = required_qty - gathered_qty
                    
                balance_qty = balance_qty + last_stock_in_ledger.balance_qty 
                balance_value = balance_value + last_stock_in_ledger.balance_value
                valuation_rate = balance_value/balance_qty

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
                new_stock_ledger.balance_qty = available_qty - docitem.qty_in_base_unit
                new_stock_ledger.balance_value = (available_qty - docitem.qty_in_base_unit) * valuation_rate
                new_stock_ledger.voucher = "Delivery Note"
                new_stock_ledger.voucher_no = self.name
                new_stock_ledger.source = "Delivery Note Item"
                new_stock_ledger.source_document_id = docitem.name
                new_stock_ledger.insert()	

                item = frappe.get_doc('Item', docitem.item)
                item.stock_balance = item.stock_balance + balance_qty
                item.save()

            else:               
                frappe.throw("No stock available for the item " + docitem.item)
