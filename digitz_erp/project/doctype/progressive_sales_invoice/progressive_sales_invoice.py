# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import money_in_words
from digitz_erp.api.settings_api import add_seconds_to_time
from digitz_erp.api.settings_api import get_default_currency, get_gl_narration
from frappe.utils import money_in_words
from digitz_erp.api.project_api import update_progress_entries_for_project
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type

class ProgressiveSalesInvoice(Document):

	def Voucher_In_The_Same_Time(self):
		possible_invalid= frappe.db.count('Sales Invoice', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time]})
		return possible_invalid

	def Set_Posting_Time_To_Next_Second(self):
		# Add 12 seconds to self.posting_time and update it
		self.posting_time = add_seconds_to_time(str(self.posting_time), seconds=12)

	def on_submit(self):
		self.do_postings_on_submit()
  
	def on_cancel(self):
		update_progress_entries_for_project(self.project)
		delete_gl_postings_for_cancel_doc_type('Progressive Sales Invoice',self.name)
  
	def on_trash(self):
		update_progress_entries_for_project(self.project)
  
	def on_update(self):
		update_progress_entries_for_project(self.project)
  
	def before_validate(self):

		if(self.Voucher_In_The_Same_Time()):

				self.Set_Posting_Time_To_Next_Second()

				if(self.Voucher_In_The_Same_Time()):
					self.Set_Posting_Time_To_Next_Second()

					if(self.Voucher_In_The_Same_Time()):
						self.Set_Posting_Time_To_Next_Second()

						if(self.Voucher_In_The_Same_Time()):
							frappe.throw("Voucher with same time already exists.")

		# Fix for paid_amount copies while duplicating the document
		if self.is_new():
			self.paid_amount = 0

		if self.credit_sale == 0:
			self.paid_amount = self.rounded_total
			self.payment_status = "Cheque" if self.payment_mode == "Bank" else self.payment_mode
		else:
			self.payment_status = "Credit"
			self.payment_mode = ""
			self.payment_account = ""
			self.meta.get_field("payment_mode").hidden = 1
			self.meta.get_field("payment_account").hidden = 1
			# For submitted invoice only paid_amount is filling up with allocation.
			# So its safe to make paid_amount 0 to avoid the issue below
			# Issue - First save the invoie not as credit sale, it will fill up the paid_amount
			# equal to rounded_total. Make it as credit sale in the draft mode and then save.
			# In this case its required to make the paid_amount zero
			self.paid_amount = 0
		# self.in_words = money_in_words(self.rounded_total,"AED")
  
		if self.rounded_total>0:
			self.in_words = money_in_words(self.rounded_total, "AED")
  
	def do_postings_on_submit(self):
          
		self.insert_gl_records()
		self.insert_payment_postings()

	def insert_gl_records(self):
		
		remarks = self.get_narration()

		default_company = frappe.db.get_single_value(
			"Global Settings", "default_company")

		default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account','default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account','project_advance_received_account','retention_receivable_account'], as_dict=1)

		idx = 1

			# Trade Receivable
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Progressive Sales Invoice"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.default_receivable_account
		gl_doc.debit_amount = self.rounded_total 

		# + self.deduction_against_advance + self.deduction_for_retention
		gl_doc.party_type = "Customer"
		gl_doc.party = self.customer_name
		gl_doc.against_account = self.revenue_account
		gl_doc.remarks = remarks
		gl_doc.project = self.project
		gl_doc.cost_center = self.cost_center
  
		gl_doc.insert()
		idx +=1

		# Reduce the liability against advance received
		if self.deduction_against_advance>0:
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Progressive Sales Invoice"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.project_advance_received_account
			gl_doc.debit_amount = self.deduction_against_advance
			# + self.deduction_against_advance + self.deduction_for_retention
			gl_doc.party_type = "Customer"
			gl_doc.party = self.customer_name
			gl_doc.against_account = self.revenue_account
			gl_doc.remarks = remarks
			gl_doc.project = self.project
			gl_doc.cost_center = self.cost_center
			gl_doc.insert()
			idx +=1


		# Reduce the liability against advance received
		if self.deduction_for_retention > 0:
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Progressive Sales Invoice"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.retention_receivable_account
			gl_doc.debit_amount = self.deduction_for_retention
			# + self.deduction_against_advance + self.deduction_for_retention
			gl_doc.party_type = "Customer"
			gl_doc.party = self.customer_name
			gl_doc.against_account = self.revenue_account
			gl_doc.remarks = remarks
			gl_doc.project = self.project
			gl_doc.cost_center = self.cost_center
			gl_doc.insert()
			idx +=1

		# Income account - Credit (Accounts Receivable + Retention Receivable)
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Progressive Sales Invoice"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = self.revenue_account
		gl_doc.credit_amount = (self.net_total - self.tax_total) + self.deduction_against_advance + self.deduction_for_retention
		gl_doc.against_account = default_accounts.default_receivable_account
		gl_doc.remarks = remarks
		gl_doc.project = self.project
		gl_doc.cost_center = self.cost_center
		gl_doc.insert()
		idx +=1

		if self.tax_total >0:

			# Tax - Credit

			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Progressive Sales Invoice"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.tax_account
			gl_doc.credit_amount = self.tax_total
			gl_doc.against_account = default_accounts.default_receivable_account
			gl_doc.remarks = remarks
			gl_doc.project = self.project
			gl_doc.cost_center = self.cost_center
			gl_doc.insert()
			idx +=1

		if self.round_off != 0.00:
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Progressive Sales Invoice"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.round_off_account

			if self.rounded_total > self.net_total:
				gl_doc.credit_amount = abs(self.round_off)
			else:
				gl_doc.debit_amount = abs(self.round_off)
			
			gl_doc.remarks = remarks
			gl_doc.project = self.project
			gl_doc.cost_center = self.cost_center
			gl_doc.insert()
			idx +=1
			
	def insert_payment_postings(self):
		remarks = self.get_narration()

		if self.credit_sale == 0:
			# Retrieve GL count for voucher entries
			gl_count = frappe.db.count('GL Posting', {'voucher_type': 'Sales Invoice', 'voucher_no': self.name})

			# Fetch default accounts from Global Settings
			default_company = frappe.db.get_single_value("Global Settings", "default_company")
			default_accounts = frappe.get_value(
				"Company", 
				default_company, 
				[
					'default_receivable_account', 
					'default_inventory_account',
					'stock_received_but_not_billed', 
					'round_off_account', 
					'tax_account'
				], 
				as_dict=True
			)
			if not default_accounts:
				frappe.throw(_("Default accounts not set in company settings."))

			# Get payment mode account
			payment_mode = frappe.get_value("Payment Mode", self.payment_mode, ['account'], as_dict=True)
			if not payment_mode:
				frappe.throw(_("Payment mode account not found."))

			idx = gl_count + 1  # Start index based on GL count

			# Template for base fields in GL Posting
			base_gl_posting = {
				"voucher_type": self.doctype,
				"voucher_no": self.name,
				"posting_date": self.posting_date,
				"posting_time": self.posting_time,
				"remarks": remarks
			}

			# First GL Posting entry (credit entry)
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.update(base_gl_posting)
			gl_doc.idx = idx
			gl_doc.account = default_accounts.default_receivable_account
			gl_doc.credit_amount = self.rounded_total
			gl_doc.party_type = "Customer"
			gl_doc.party = self.customer
			gl_doc.against_account = payment_mode.account
			self.fill_cost_centers(gl_doc)
			gl_doc.insert()

			# Second GL Posting entry (debit entry)
			idx += 1
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.update(base_gl_posting)
			gl_doc.idx = idx
			gl_doc.account = payment_mode.account
			gl_doc.debit_amount = self.rounded_total
			gl_doc.against_account = default_accounts.default_receivable_account
			self.fill_cost_centers(gl_doc)
			gl_doc.insert()

	def fill_cost_centers(self,gl_doc):
 
		gl_doc.project = self.project
		gl_doc.cost_center = self.cost_center
  
	def get_narration(self):
		
		# Assign supplier, invoice_no, and remarks
		customer_name = self.customer_name		
		remarks = self.remarks if self.remarks else ""
		payment_mode = ""
		if self.credit_sale:
			payment_mode = "Credit"
		else:
			payment_mode = self.payment_mode
		
		# Get the gl_narration which might be empty
		gl_narration = get_gl_narration('Sales Invoice')  # This could return an empty string

		# Provide a default template if gl_narration is empty
		if not gl_narration:
			gl_narration = "Sales to {customer_name}"

		# Replace placeholders with actual values
		narration = gl_narration.format(payment_mode=payment_mode, customer_name=customer_name)

		# Append remarks if they are available
		if remarks:
			narration += f", {remarks}"

		return narration    