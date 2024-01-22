# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.gl_posting_api import update_account_balance 

class JournalEntry(Document):
	def on_submit(self):
		# frappe.enqueue(self.insert_gl_records, queue="long")
		self.insert_gl_records()

	def insert_gl_records(self):
		idx = 1
  
		accounts = []
  
		for journal_entry in self.journal_entry_account:
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Journal Entry'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = journal_entry.account
			gl_doc.debit_amount = journal_entry.debit
			gl_doc.credit_amount = journal_entry.credit
			gl_doc.remarks = journal_entry.narration
			gl_doc.insert()
			idx += 1
			if journal_entry.account not in accounts:
				accounts.append(journal_entry.account)
    
		print(accounts)
    
		for account in accounts:
			update_account_balance(account)
			
