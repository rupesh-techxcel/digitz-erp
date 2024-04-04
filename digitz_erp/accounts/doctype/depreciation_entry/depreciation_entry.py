# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type

class DepreciationEntry(Document):
	def on_submit(self):
		# frappe.enqueue(self.insert_gl_records, queue="long")
		self.insert_gl_records()
		update_accounts_for_doc_type('Dereciation Entry',self.name)

	def insert_gl_records(self):
		idx = 1

		for depreciation_entry in self.depreciation_entry_details:
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Depreciation Entry'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = depreciation_entry.account
			gl_doc.debit_amount = depreciation_entry.debit
			gl_doc.credit_amount = depreciation_entry.credit
			gl_doc.remarks = depreciation_entry.narration
			gl_doc.insert()
			idx += 1
