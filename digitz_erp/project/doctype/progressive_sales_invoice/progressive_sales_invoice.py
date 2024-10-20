# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import money_in_words


class ProgressiveSalesInvoice(Document):

	def Voucher_In_The_Same_Time(self):
		possible_invalid= frappe.db.count('Sales Invoice', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time]})
		return possible_invalid

	def Set_Posting_Time_To_Next_Second(self):
		datetime_object = datetime.strptime(str(self.posting_time), '%H:%M:%S')

		# Add one second to the datetime object
		new_datetime = datetime_object + timedelta(seconds=12)

		# Extract the new time as a string
		self.posting_time = new_datetime.strftime('%H:%M:%S')

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
  
	def do_postings_on_submit(self):
     
		self.insert_gl_records()
		self.insert_payment_postings()

	def insert_gl_records(self):
		
		remarks = self.get_narration()

		default_company = frappe.db.get_single_value(
			"Global Settings", "default_company")

		default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
																			'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)

		idx = 1

			# Trade Receivable - Debit
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
		gl_doc.against_account = default_accounts.default_income_account
		gl_doc.remarks = remarks
		gl_doc.insert()
		idx +=1

		# Income account - Credit
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Sales Invoice"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.default_income_account
		gl_doc.credit_amount = self.net_total - self.tax_total
		gl_doc.against_account = default_accounts.default_receivable_account
		gl_doc.remarks = remarks
		gl_doc.insert()
		idx +=1

		if self.tax_total >0:

			# Tax - Credit

			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Sales Invoice"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.tax_account
			gl_doc.credit_amount = self.tax_total
			gl_doc.against_account = default_accounts.default_receivable_account
			gl_doc.remarks = remarks
			gl_doc.insert()
			idx +=1
   
		if self.round_off != 0.00:
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Sales Invoice"
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
			gl_doc.insert()
			idx +=1
			
	def insert_payment_postings(self):
		
		remarks = self.get_narration()

		if self.credit_sale == 0:

			gl_count = frappe.db.count(
				'GL Posting', {'voucher_type': 'Sales Invoice', 'voucher_no': self.name})

			default_company = frappe.db.get_single_value(
				"Global Settings", "default_company")

			default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
																				'stock_received_but_not_billed', 'round_off_account', 'tax_account'], as_dict=1)

			payment_mode = frappe.get_value(
				"Payment Mode", self.payment_mode, ['account'], as_dict=1)

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
			gl_doc.against_account = payment_mode.account
			gl_doc.remarks = remarks
			gl_doc.insert()

			idx = idx + 1

			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Sales Invoice"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = payment_mode.account
			gl_doc.debit_amount = self.rounded_total
			gl_doc.against_account = default_accounts.default_receivable_account
			gl_doc.remarks = remarks
			gl_doc.insert()

			update_posting_status(self.doctype,self.name, 'payment_posted_time',None)


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