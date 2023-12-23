# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.pdf_utils import *
from datetime import *
from frappe.utils import *

class GLPosting(Document):
	pass

	def on_update(self):
		self.ledger_closing_balance_updation()

	@frappe.whitelist()
	def ledger_closing_balance_updation(self):
		''' Method used for updating balance in account'''
		current_date = nowdate()
		current_time = nowtime()
		credit_sum = {}
		debit_sum = {}
		accounts = []
		gl_postings = frappe.db.get_all('GL Posting', filters={'posting_date': ['<=', current_date], 'posting_time': ['<=', current_time]})
		for gl_posting in gl_postings:
			account = frappe.db.get_value('GL Posting', gl_posting.name, 'account')
			if account not in accounts:
				accounts.append(account)
			if credit_sum.get(account):
				credit_sum[account]= credit_sum.get(account) + frappe.db.get_value('GL Posting', gl_posting.name, 'credit_amount')
			else:
				credit_sum[account] = frappe.db.get_value('GL Posting', gl_posting.name, 'credit_amount')

			if debit_sum.get(account):
				debit_sum[account]= debit_sum.get(account) + frappe.db.get_value('GL Posting', gl_posting.name, 'debit_amount')
			else:
				debit_sum[account] = frappe.db.get_value('GL Posting', gl_posting.name, 'debit_amount')

		for account in accounts:
			if credit_sum.get(account) > debit_sum.get(account):
				balance = credit_sum.get(account) - debit_sum.get(account)
				frappe.db.set_value('Account', account, 'balance_dr_cr', 'Cr')
			else:
				balance = debit_sum.get(account) - credit_sum.get(account)
				frappe.db.set_value('Account', account, 'balance_dr_cr', 'Dr')
			frappe.db.set_value('Account', account, 'balance', balance)
			frappe.db.commit()

@frappe.whitelist()
def get_party_balance(party_type, party):
    
	print("party_type")
	print(party_type)
	print("party")
	print(party)
 
	party_balance = 0

	if(party_type == "Customer"):
		
		party_balance = frappe.db.sql("""
		SELECT SUM(rounded_total) - SUM(paid_amount) 
		FROM `tabSales Invoice` 
		WHERE customer=%s and credit_sale =1 and docstatus<2 and rounded_total> paid_amount
		""", ( party))[0][0]
	else:

		party_balance = frappe.db.sql("""
		SELECT SUM(debit_amount) - SUM(credit_amount) 
		FROM `tabGL Posting` 
		WHERE party_type=%s AND party=%s
		""", (party_type, party))[0][0]

		# For customer it automatically shows negative 
		# For supplier, value must be negative, if it is positve that means
		# its negative balance
		if(party_type == "Supplier" and party_balance>0):
			party_balance = party_balance * -1

	return party_balance	

@frappe.whitelist()
def get_voucher_balance(voucher_type, party):
	balance = 0
	if voucher_type == "Sales Invoice":
		data =  frappe.db.sql("""
			SELECT
				SUM(si.rounded_total - IFNULL(si.paid_amount, 0)) AS balance_amount
			FROM
				`tabSales Invoice` si
			WHERE
				si.customer = '{0}' AND
				si.docstatus = 1
		""".format(party), as_dict=True)
  
		if data:
			if data[0].get('balance_amount'):
				balance = data[0].get('balance_amount')

	if voucher_type == "Purchase Invoice":
		data =  frappe.db.sql("""
			SELECT
				SUM(pi.rounded_total - IFNULL(pi.paid_amount, 0)) AS balance_amount
			FROM
				`tabPurchase Invoice` pi
			WHERE
				pi.supplier = '{0}' AND
				pi.docstatus = 1
		""".format(party), as_dict=True)
		if data:
			if data[0].get('balance_amount'):
				balance = data[0].get('balance_amount')
	return balance
