# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ExpenseEntry(Document):

	def on_submit(self):
		frappe.enqueue(self.insert_gl_records, queue="long")

	def insert_gl_records(self):
		idx = 1
		for expense_entry in self.expense_entry_details:
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Expense Entry'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = expense_entry.account
			gl_doc.debit_amount = expense_entry.expense_amount
			gl_doc.party_type = "Supplier"
			gl_doc.party = expense_entry.supplier
			gl_doc.insert()
			idx += 1
