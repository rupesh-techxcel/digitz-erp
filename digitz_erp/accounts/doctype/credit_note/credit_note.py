# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type
from frappe.utils import money_in_words
from digitz_erp.api.settings_api import get_gl_narration

class CreditNote(Document):

	def before_validate(self):
		self.in_words = money_in_words(self.grand_total,"AED")

	def on_submit(self):
		# frappe.enqueue(self.do_postings_on_submit, queue="long")
		self.do_postings_on_submit()

	def on_cancel(self):
		self.do_cancel_credit_note()

	def on_update(self):
		self.update_receipt_schedules()

	def do_postings_on_submit(self):
		self.insert_gl_records()
		update_accounts_for_doc_type('Credit Note',self.name)

	def update_receipt_schedules(self):
		existing_entries = frappe.get_all("Receipt Schedule", filters={"receipt_against": "Credit", "document_no": self.name})
		for entry in existing_entries:
			try:
				frappe.delete_doc("Receipt Schedule", entry.name)
			except Exception as e:
				frappe.log_error("Error deleting receipt schedule: " + str(e))
		if self.on_credit and self.receipt_schedule:
			for schedule in self.receipt_schedule:
				new_receipt_schedule = frappe.new_doc("Receipt Schedule")
				new_receipt_schedule.receipt_against = "Credit"
				new_receipt_schedule.customer = self.customer
				new_receipt_schedule.document_no = self.name
				new_receipt_schedule.document_date = self.posting_date
				new_receipt_schedule.scheduled_date = schedule.date
				new_receipt_schedule.amount = schedule.amount
				try:
					new_receipt_schedule.insert()
				except Exception as e:
					frappe.log_error("Error creating receipt schedule: " + str(e))
    
	def get_narration(self):
		
		# Assign supplier, invoice_no, and remarks
		customer = self.customer_name
		remarks = self.remarks if self.remarks else ""
		payment_mode = ""
		if self.on_credit:
			payment_mode = "Credit"
		else:
			payment_mode = self.payment_mode
		
		# Get the gl_narration which might be empty
		gl_narration = get_gl_narration('Credit Note')  # This could return an empty string

		# Provide a default template if gl_narration is empty
		if not gl_narration:
			gl_narration = "Credit Note from {customer}"

		# Replace placeholders with actual values
		narration = gl_narration.format(customer=customer)

		# Append remarks if they are available
		if remarks:
			narration += f", {remarks}"

		return narration  

	def insert_gl_records(self):

		print("from insert gl records")
  
		remarks = self.get_narration()

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
		gl_doc.party_type = "Customer"
		gl_doc.party = self.customer
		gl_doc.remarks = remarks
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
			gl_doc.remarks = remarks
			gl_doc.insert()

			if not credit_note_detail.tax_excluded and credit_note_detail.tax_amount > 0:
				if credit_note_detail.tax_account not in tax_ledgers:
					tax_ledgers[credit_note_detail.tax_account] = credit_note_detail.tax_amount
				else:
					tax_ledgers[credit_note_detail.tax_account] += credit_note_detail.tax_amount

		for tax_account,tax_amount in tax_ledgers.items():

			if tax_amount>0:
				idx = idx + 1
				gl_doc = frappe.new_doc('GL Posting')
				gl_doc.idx = idx
				gl_doc.voucher_type = 'Credit Note'
				gl_doc.voucher_no = self.name
				gl_doc.posting_date = self.posting_date
				gl_doc.account = tax_account
				gl_doc.debit_amount = tax_amount
				gl_doc.against_account = self.receivable_account				
				gl_doc.remarks = remarks
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
			gl_doc.party_type = "Customer"
			gl_doc.party = self.customer
			gl_doc.remarks = remarks
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
			gl_doc.remarks = remarks
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

@frappe.whitelist()
def get_default_payment_mode():
    default_payment_mode = frappe.db.get_value('Company', filters={'name'},fieldname='default_payment_mode_for_sales')
    print(default_payment_mode)
    return default_payment_mode

@frappe.whitelist()
def get_gl_postings(credit_note):
    gl_postings = frappe.get_all("GL Posting",
                                  filters={"voucher_no": credit_note},
                                  fields=["name", "debit_amount", "credit_amount", "against_account", "remarks"])
    formatted_gl_postings = []
    for posting in gl_postings:
        formatted_gl_postings.append({
            "gl_posting": posting.name,
            "debit_amount": posting.debit_amount,
            "credit_amount": posting.credit_amount,
            "against_account": posting.against_account,
            "remarks": posting.remarks
        })

    return formatted_gl_postings
