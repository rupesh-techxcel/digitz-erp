# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Quotation(Document):

	@frappe.whitelist()
	def generate_sale_invoice(self):
		sales_invoice_name = ""  
		
		quotationName =  self.name
		sales_invoice = self.__dict__
		sales_invoice['doctype'] = 'Sales Invoice'
		sales_invoice['name'] = sales_invoice_name
		sales_invoice['naming_series'] = ""
		sales_invoice['posting_date'] = self.posting_date
		sales_invoice['posting_time'] = self.posting_time
		sales_invoice['quotation'] = quotationName
		sales_invoice['auto_save_delivery_note'] = True
		# Change the document status to draft to avoid error while submitting child table
		sales_invoice['docstatus'] = 0
		for item in sales_invoice['items']:            
			item.doctype = "Sales Invoice Item"
			item.delivery_note_item_reference_no = item.name
			item._meta = ""       
			
		sales_invoice_doc = frappe.get_doc(
			sales_invoice).insert(ignore_permissions=True)               
		
		frappe.db.commit()

		si =  frappe.get_doc('Sales Invoice',sales_invoice_doc.name)
		
		frappe.msgprint("Sales Invoice created successfully with draft mode.")