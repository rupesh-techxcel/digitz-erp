# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import *
from frappe.utils import *
from datetime import datetime
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type

class PeriodClosingVoucher(Document):
	
	def on_submit(self):
		# frappe.enqueue(self.insert_gl_records, queue="long")
		self.insert_gl_records()
  
	def on_cancel(self):
		self.cancel_period_closing()     

	def insert_gl_records(self):
     
		idx = 1
  
		if(self.amount !=0):
		
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Period Closing Voucher'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.posting_date
			gl_doc.account = self.closing_account_head
			gl_doc.debit_amount = self.amount if self.amount_dr_cr == "Dr" else 0
			gl_doc.credit_amount = self.amount if self.amount_dr_cr == "Cr" else 0
			gl_doc.remarks = self.remarks;
			gl_doc.insert()
			idx +=1
		
		for account in self.closing_accounts:
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Period Closing Voucher'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.posting_date
			gl_doc.account = account.account
			gl_doc.debit_amount = account.debit_amount
			gl_doc.credit_amount = account.credit_amount
			gl_doc.remarks = account.narration;
			gl_doc.insert()
			idx +=1
   
		update_accounts_for_doc_type('Period Closing Voucher',self.name)
   
	def cancel_period_closing(self):
		
		delete_gl_postings_for_cancel_doc_type('Period Closing Voucher',self.name)
		
