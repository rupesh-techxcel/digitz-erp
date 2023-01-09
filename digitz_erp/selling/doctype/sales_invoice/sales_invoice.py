# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt
from frappe.utils import now

import frappe
from frappe.model.document import Document

class SalesInvoice(Document):
	
	def before_submit(self):		

		for docitem in self.items:		
			doc = frappe.get_doc({'doctype':'Stock Ledger'})			
			doc.item = docitem.item
			doc.item_code = docitem.item_code
			doc.posting_date = self.posting_date
			doc.posting_time = self.posting_time
			doc.warehouse = docitem.warehouse
			doc.voucher_type = "Sales Invoice"
			doc.voucher_no = self.name
			doc.qty_out = docitem.qty
			doc.unit = docitem.unit
			doc.outgoing_rate = docitem.rate
			doc.valuation_rate = docitem.rate			
			doc.is_latest = 1
			doc.insert()

		self.created_by = frappe.user
		self.submitted_date = now()

		self.insert_gl_records()
		self.insert_payment_postings()

	def before_cancel(self):

		frappe.db.delete("Stock Ledger",
				{"Voucher_type": "Sales Invoice",
				 "voucher_no":self.name
				})
	
		frappe.db.delete("GL Posting",
				{"Voucher_type": "Sales Invoice",
				 "voucher_no":self.name
				})

	def insert_gl_records(self):

		default_company = frappe.db.get_single_value("Global Settings","default_company")
		
		default_accounts = frappe.get_value("Company", default_company,['default_receivable_account','default_inventory_account',
		
		'default_income_account','cost_of_goods_sold_account','round_off_account','tax_account'], as_dict=1)
		
		idx =1
		
		# Trade Payavble - Debit
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Sales Invoice"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.default_receivable_account
		gl_doc.debit_amount = self.rounded_total
		gl_doc.party_type = "Customer"
		gl_doc.party = self.customer
		gl_doc.aginst_account = default_accounts.default_income_account
		gl_doc.insert()


		# Stock Received But Not Billed 
		idx =2
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Sales Invoice"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.default_income_account
		gl_doc.credit_amount =  self.net_total - self.tax_total		
		gl_doc.aginst_account =  default_accounts.default_receivable_account
		gl_doc.insert()


		# Tax
		idx =3
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Sales Invoice"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.tax_account
		gl_doc.credit_amount = self.tax_total		
		gl_doc.insert()


		# Round Off
		
		if self.round_off!=0.00:
			idx =4
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Sales Invoice"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.round_off_account

			if self.rounded_total > self.net_total:
				gl_doc.credit_amount = self.round_off
			else:
				gl_doc.debit_amount = self.round_off		

			gl_doc.insert()

	def insert_payment_postings(self):
		
		if self.credit_purchase==0:

			gl_count = frappe.db.count('GL Posting',{'voucher_type':'Sales Invoice', 'voucher_no': self.name})


			default_company = frappe.db.get_single_value("Global Settings","default_company")
		
			default_accounts = frappe.get_value("Company", default_company,['default_receivable_account','default_inventory_account',		
			'stock_received_but_not_billed','round_off_account','tax_account'], as_dict=1)
			
			payment_mode = frappe.get_value("Payment Mode", self.payment_mode, ['account'],as_dict=1)

			idx = gl_count + 1
		
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Sales Invoice"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.default_receivable_account
			gl_doc.credit_amount = self.rounded_total
			gl_doc.party_type = "Customer"
			gl_doc.party = self.customer
			gl_doc.aginst_account = payment_mode.account
			gl_doc.insert()
			
			idx= idx + 1

			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Sales Invoice"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = payment_mode.account
			gl_doc.debit_amount = self.rounded_total
			gl_doc.aginst_account = default_accounts.default_receivable_account				
			gl_doc.insert()