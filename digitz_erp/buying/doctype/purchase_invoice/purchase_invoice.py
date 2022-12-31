# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PurchaseInvoice(Document):

	def before_submit(self):		

		for docitem in self.items:		
			doc = frappe.get_doc({'doctype':'Stock Ledger'})			
			doc.item = docitem.item
			doc.item_code = docitem.item_code
			doc.posting_date = self.posting_date
			doc.posting_time = self.posting_time
			doc.warehouse = docitem.warehouse
			doc.voucher_type = "Purchase Invoice"
			doc.voucher_no = self.name
			doc.qty = docitem.qty
			doc.unit = docitem.unit
			doc.incoming_rate = docitem.rate
			doc.valuation_rate = docitem.rate			
			doc.is_latest = 1
			doc.insert()
		
		self.insert_gl_records()
		

	def before_cancel(self):		

		frappe.db.delete("Stock Ledger",
				{"Voucher_type": "Purchase Invoice",
				 "voucher_no":self.name
				})
	
	def insert_gl_records(self):

		default_company = frappe.db.get_single_value("Global Settings","default_company")
		
		default_accounts = frappe.get_value("Company", default_company,['default_payable_account','default_receivable_account'], as_dict=1)
		





