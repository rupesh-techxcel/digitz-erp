# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ExpenseEntry(Document):

	def on_submit(self):
		frappe.enqueue(self.insert_gl_records, queue="long")
		frappe.enqueue(self.insert_payment_postings, queue="long")

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

	def insert_payment_postings(self):
		if self.credit_expense == 0:
			gl_count = frappe.db.count('GL Posting',{'voucher_type':'Expense Entry', 'voucher_no': self.name})
			default_company = frappe.db.get_single_value("Global Settings","default_company")
			default_accounts = frappe.get_value("Company", default_company,['default_payable_account','default_inventory_account',
			'stock_received_but_not_billed','round_off_account','tax_account'], as_dict=1)
			payment_mode = frappe.get_value("Payment Mode", self.payment_mode, ['account'],as_dict=1)

			idx = gl_count + 1
			for expense_entry in self.expense_entry_details:
				gl_doc = frappe.new_doc('GL Posting')
				gl_doc.voucher_type = "Expense Entry"
				gl_doc.voucher_no = self.name
				gl_doc.idx = idx
				gl_doc.posting_date = self.posting_date
				gl_doc.posting_time = self.posting_time
				gl_doc.account = default_accounts.default_payable_account
				gl_doc.debit_amount = expense_entry.total
				gl_doc.party_type = "Supplier"
				gl_doc.party = expense_entry.supplier
				gl_doc.aginst_account = payment_mode.account
				gl_doc.insert()

			idx= idx + 1
			for expense_entry in self.expense_entry_details:
				gl_doc = frappe.new_doc('GL Posting')
				gl_doc.voucher_type = "Expense Entry"
				gl_doc.voucher_no = self.name
				gl_doc.idx = idx
				gl_doc.posting_date = self.posting_date
				gl_doc.posting_time = self.posting_time
				gl_doc.account = payment_mode.account
				gl_doc.credit_amount = expense_entry.total
				gl_doc.aginst_account = default_accounts.stock_received_but_not_billed
				gl_doc.insert()
