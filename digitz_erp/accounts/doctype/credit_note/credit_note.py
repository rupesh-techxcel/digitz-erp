# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type

class CreditNote(Document):
	def on_submit(self):
		frappe.enqueue(self.do_postings_on_submit, queue="long")
		# self.do_postings_on_submit()

	def on_cancel(self):
		self.do_cancel_credit_note()
  
	def do_postings_on_submit(self):
		self.insert_gl_records()
		update_accounts_for_doc_type('Credit Note',self.name)		

	def insert_gl_records(self):

		print("from insert gl records")

		idx = 1

		highestAccount = self.GetAccountForTheHighestAmount()

		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.idx = idx
		gl_doc.voucher_type = 'Credit Note'
		gl_doc.voucher_no = self.name
		gl_doc.posting_date = self.posting_date
		gl_doc.account = self.receivable_account
		gl_doc.credit_amount = self.grand_total
		gl_doc.against_account = highestAccount
		gl_doc.remarks = self.remarks
		gl_doc.party_type = "Customer"
		gl_doc.party = self.customer
		gl_doc.insert()

		tax_ledgers = {}

		for credit_note_detail in self.credit_note_details:

			idx = idx + 1
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Credit Note'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.posting_date
			gl_doc.account = credit_note_detail.account
			gl_doc.debit_amount = credit_note_detail.amount_excluded_tax
			gl_doc.against_account = self.receivable_account
			gl_doc.remarks = credit_note_detail.narration
			gl_doc.insert()

			if not credit_note_detail.tax_excluded and credit_note_detail.tax_amount > 0:
				if credit_note_detail.tax_account not in tax_ledgers:
					tax_ledgers[credit_note_detail.tax_account] = credit_note_detail.tax_amount
				else:
					tax_ledgers[credit_note_detail.tax_account] += credit_note_detail.tax_amount

		for tax_account,tax_amount in tax_ledgers.items():

			idx = idx + 1
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Credit Note'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.posting_date
			gl_doc.account = tax_account
			gl_doc.debit_amount = tax_amount
			gl_doc.against_account = self.receivable_account
			gl_doc.remarks = ""
			gl_doc.insert()

		# For payments
		if not self.on_credit:
			idx = idx + 1
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Credit Note'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.posting_date
			gl_doc.account = self.receivable_account
			gl_doc.debit_amount = self.grand_total
			gl_doc.against_account = self.payment_account
			gl_doc.remarks = self.remarks
			gl_doc.party_type = "Customer"
			gl_doc.party = self.customer
			gl_doc.insert()

			idx = idx + 1
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Credit Note'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.posting_date
			gl_doc.account = self.payment_account
			gl_doc.credit_amount = self.grand_total
			gl_doc.against_account = self.receivable_account
			gl_doc.remarks = self.remarks
			gl_doc.insert()

	def GetAccountForTheHighestAmount(self):

		highestAmount = 0
		account = ""

		payment_details = self.credit_note_details

		for detail in self.credit_note_details:

			if detail.amount > highestAmount:
				highestAmount = detail.amount
				account = detail.account

		return account

	def do_cancel_credit_note(self):
     
		delete_gl_postings_for_cancel_doc_type('Credit Note',self.name)

		# frappe.db.delete("GL Posting",
        #                  {"Voucher_type": "Credit Note",
        #                   "voucher_no": self.name
        #                   })
