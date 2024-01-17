# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DebitNote(Document):
	def on_submit(self):
		frappe.enqueue(self.insert_gl_records, queue="long")
  
	def on_cancel(self):
		self.do_cancel_debit_note()		

	def insert_gl_records(self):
     
		idx = 1
  
		highestAccount = self.GetAccountForTheHighestAmount()
  
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.idx = idx
		gl_doc.voucher_type = 'Debit Note'
		gl_doc.voucher_no = self.name
		gl_doc.posting_date = self.date
		gl_doc.account = self.payable_account
		gl_doc.debit_amount = self.grand_total
		gl_doc.against_account = highestAccount
		gl_doc.remarks = self.remarks
		gl_doc.party_type = "Supplier"
		gl_doc.party = self.supplier
		gl_doc.insert()
  
		tax_ledgers = {}
  
		for debit_note_detail in self.debit_note_details:
      
			idx = idx + 1
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Debit Note'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.date
			gl_doc.account = debit_note_detail.account
			gl_doc.credit_amount = debit_note_detail.amount_excluded_tax
			gl_doc.against_account = self.payable_account
			gl_doc.remarks = debit_note_detail.narration
			gl_doc.insert()
   
			if not debit_note_detail.tax_excluded and debit_note_detail.tax_amount > 0:
				if debit_note_detail.tax_account not in tax_ledgers:
					tax_ledgers[debit_note_detail.tax_account] = debit_note_detail.tax_amount
				else:
					tax_ledgers[debit_note_detail.tax_account] += debit_note_detail.tax_amount
     
		for tax_account,tax_amount in tax_ledgers.items():
      
			idx = idx + 1
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Debit Note'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.date
			gl_doc.account = tax_account
			gl_doc.credit_amount = tax_amount
			gl_doc.against_account = self.payable_account
			gl_doc.remarks = ""
			gl_doc.insert()
   
		# For payments
		if not self.on_credit:
			idx = idx + 1
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Debit Note'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.date
			gl_doc.account = self.payable_account
			gl_doc.credit_amount = self.grand_total
			gl_doc.against_account = self.payment_account
			gl_doc.remarks = self.remarks
			gl_doc.party_type = "Supplier"
			gl_doc.party = self.supplier
			gl_doc.insert()
   
			idx = idx + 1
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Debit Note'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.date
			gl_doc.account = self.payment_account
			gl_doc.debit_amount = self.grand_total
			gl_doc.against_account = self.payable_account
			gl_doc.remarks = self.remarks
			gl_doc.insert()
   
	def GetAccountForTheHighestAmount(self):
     
		highestAmount = 0
		account = ""
  
		payment_details = self.debit_note_details

		for detail in self.debit_note_details:
	
			if detail.amount > highestAmount:
				highestAmount = detail.amount
				account = detail.account

		return account

	def do_cancel_debit_note(self):
     
		frappe.db.delete("GL Posting",
                         {"Voucher_type": "Debit Note",
                          "voucher_no": self.name
                          })