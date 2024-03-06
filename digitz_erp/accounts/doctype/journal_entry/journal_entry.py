# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type

class JournalEntry(Document):
	def on_submit(self):
		# frappe.enqueue(self.insert_gl_records, queue="long")
		self.insert_gl_records()
		update_accounts_for_doc_type('Journal Entry',self.name)

	def insert_gl_records(self):
		idx = 1

		for journal_entry in self.journal_entry_details:
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


		# update_all_account_balances()

		# for account in accounts:
		#   	update_account_balance(account)



@frappe.whitelist()
def get_gl_postings(journal_entry):
    gl_postings = frappe.get_all("GL Posting",
                                  filters={"voucher_no": journal_entry},
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
