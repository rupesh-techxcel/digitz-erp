# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DebitNote(Document):
	def on_submit(self):
		frappe.enqueue(self.insert_gl_records, queue="long")

	def insert_gl_records(self):
		idx = 1
		for debit_note in self.debit_note_details:

			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Debit Note'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.date
			gl_doc.account = debit_note.debit_account
			gl_doc.debit_amount = debit_note.amount
			gl_doc.remarks = self.remarks;
			gl_doc.insert()
