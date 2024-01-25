# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.receipt_entry_api import get_allocations_for_sales_invoice ,get_allocations_for_sales_return, get_allocations_for_credit_note
from datetime import datetime, timedelta
from digitz_erp.api.document_posting_status_api import init_document_posting_status, update_posting_status

class ReceiptEntry(Document):

	def Voucher_In_The_Same_Time(self):
		possible_invalid= frappe.db.count('Receipt Entry', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time]})
		return possible_invalid

	def Set_Posting_Time_To_Next_Second(self):
		datetime_object = datetime.strptime(str(self.posting_time), '%H:%M:%S')

		# Add one second to the datetime object
		new_datetime = datetime_object + timedelta(seconds=1)

		# Extract the new time as a string
		self.posting_time = new_datetime.strftime('%H:%M:%S')

	def assign_missing_reference_nos(self):
		if self.payment_mode != "Bank":
				return
		receipt_details = self.receipt_entry_details

		if receipt_details:
			for receipt_detail in receipt_details:
				if not receipt_detail.reference_no:
					if(self.reference_no):
						receipt_detail.reference_no = self.reference_no

				if not receipt_detail.reference_date:
					if(self.reference_date):
						receipt_detail.reference_date = self.reference_date

	def before_validate(self):

		if(self.Voucher_In_The_Same_Time()):

				self.Set_Posting_Time_To_Next_Second()

				if(self.Voucher_In_The_Same_Time()):
					self.Set_Posting_Time_To_Next_Second()

					if(self.Voucher_In_The_Same_Time()):
						self.Set_Posting_Time_To_Next_Second()

						if(self.Voucher_In_The_Same_Time()):
							frappe.throw("Voucher with same time already exists.")

		self.show_allocations = False
		self.assign_missing_reference_nos()
		self.clean_deleted_allocations()
		self.postings_start_time = datetime.now()

	def validate(self):

		self.validate_doc_status()
		self.check_reference_numbers()
		self.check_allocations_and_totals()
		self.check_excess_allocation()

	def clean_deleted_allocations(self):

		allocations = self.receipt_allocation
		print('allocations :', allocations)

		if(allocations):
			for allocation in allocations[:]:

				receipt_details = self.receipt_entry_details
				allocation_exist = False
				if receipt_details:
					for receipt_entry in receipt_details:
						if receipt_entry.customer == allocation.customer and receipt_entry.allocated_amount and receipt_entry.allocated_amount>0:
							allocation_exist= True
					if allocation_exist==False:
						self.receipt_allocation.remove(allocation)

	def check_reference_numbers(self):

		if self.payment_mode != "Bank":
			return

		receipt_details = self.receipt_entry_details

		if receipt_details:
			for receipt_detail in receipt_details:
				if not receipt_detail.reference_no:
					if(not self.reference_no):
						frappe.throw("Reference No is mandatory for Bank receipts")
				if not receipt_detail.reference_date:
					if(not self.reference_date):
						frappe.throw("Reference Date is mandatory for Bank receipts")

	def validate_doc_status(self):

		if self.amount == 0:
			frappe.throw("Cannot save the document with out valid inputs.")

		if not self.receipt_entry_details:
			frappe.throw("No valid receipt entries found to save the document")

		for receipt_entry in self.receipt_entry_details:
			if receipt_entry.receipt_type == "Other" and (receipt_entry.reference_type == "Sales Invoice"):
				messge = """Invalid reference type found at line {0} """.format(receipt_entry.idx)
				frappe.throw(messge)

			if receipt_entry.receipt_type == "Other" and receipt_entry.customer:
				messge = """Customer should not be selected with the payment type 'Other', at line {0} """.format(receipt_entry.idx)
				frappe.throw(messge)

			if receipt_entry.receipt_type == "Customer" and (not receipt_entry.customer):
				messge = """Customer is mandatory for the payment type Customer, at line {0} """.format(receipt_entry.idx)
				frappe.throw(messge)

			if receipt_entry.reference_type == "Sales Invoice"  and (not receipt_entry.customer):
				messge = """Customer is mandatory for the referene type Sales Invoice, at line {0} """.format(receipt_entry.idx)
				frappe.throw(messge)

			if receipt_entry.reference_type == "Sales Invoice" and receipt_entry.customer and receipt_entry.allocated_amount ==0:

				messge = """Allocation not found for the payment at line {0} """.format(receipt_entry.idx)
				frappe.throw(messge)


    # Cleaning the deleted allocations is crucial, so this method should call even though it cleans with the client side javascript code
	def clean_deleted_allocations(self):

		allocations = self.receipt_allocation
		print("len(allocations)")
		print(len(allocations))

		if(allocations):
			for allocation in allocations[:]:
				print("allocation.customer")
				print(allocation.customer)
				receipt_details = self.receipt_entry_details
				allocation_exist = False
				if(receipt_details):
					for receipt_entry in receipt_details:
						if receipt_entry.customer == allocation.customer and receipt_entry.allocated_amount and receipt_entry.allocated_amount>0:
							allocation_exist= True
					if allocation_exist==False:
						self.receipt_allocation.remove(allocation)

	def check_allocations_and_totals(self):
		receipt_details = self.receipt_entry_details
		total_amount_in_rows =0
		total_allocated_in_rows = 0

		if(receipt_details):
			for receipt_detail in receipt_details:

				total_amount_in_rows = total_amount_in_rows+ receipt_detail.amount

				if receipt_detail.receipt_type != "Customer":
					continue

				# If there is an allocation in the lineitem make sure the amount and allocated amount are same
				if(receipt_detail.allocated_amount and receipt_detail.allocated_amount>0):
					if(receipt_detail.amount!= receipt_detail.allocated_amount):
						frappe.throw("Allocated amount mismatch.")

				if(receipt_detail.allocated_amount):
					total_allocated_in_rows = total_allocated_in_rows +  receipt_detail.allocated_amount


		amount = 0
		if self.amount is not None:
			amount = self.amount

		if(amount != total_amount_in_rows):
			frappe.throw("Mismatch in total amount. Please check the document inputs")

		allocated_amount = 0

		if self.allocated_amount is not None:
			allocated_amount = self.allocated_amount

		# Both values are not None, perform the comparison
		if allocated_amount != total_allocated_in_rows:
			frappe.throw("Mismatch in total allocated amount. Please check the document inputs")


	def check_excess_allocation(self):
		print("from check excces allocation")
		allocations = self.receipt_allocation

		if(allocations):
			for allocation in allocations:
				if(allocation.paying_amount>0):
					is_new = self.is_new()
					print("self.is_new()")
					print(self.is_new())

					receipt_no = self.name
					if self.is_new():
						receipt_no = ""
					print("receipt_no")
					print(receipt_no)

					if(allocation.reference_type == "Sales Invoice"):
						previous_paid_amount = 0
						allocations_exists = get_allocations_for_sales_invoice(allocation.reference_name, receipt_no)

					if(allocation.reference_type == "Sales Return"):
						previous_paid_amount = 0
						allocations_exists = get_allocations_for_sales_return(allocation.reference_name, receipt_no)

						for existing_allocation in allocations_exists:
							previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount

						if allocation.paying_amount > allocation.total_amount-previous_paid_amount:
							print("throws error")
							frappe.throw("Excess allocation for the invoice numer " + allocation.reference_name )

	def on_submit(self):
		# self.do_posting()
		init_document_posting_status(self.doctype,self.name)

		turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

		if(frappe.session.user == "Administrator" and turn_off_background_job):
			self.do_postings_on_submit()
		else:
			frappe.enqueue(self.do_postings_on_submit,queue="long")

	def do_postings_on_submit(self):

		self.update_sales_invoices()
		self.update_sales_return()
		self.update_credit_note()
		self.insert_gl_records()
		update_posting_status(self.doctype,self.name, 'gl_posted_time')
		update_posting_status(self.doctype,self.name,'posting_status','Completed')

	def update_sales_invoices(self):
		print("from update_sales_invoices")
		allocations = self.receipt_allocation

		if(allocations):
			for allocation in allocations:
				if(allocation.paying_amount>0):

					receipt_no = self.name
					if self.is_new():
						receipt_no = ""

					previous_paid_amount = 0
					allocations_exists = get_allocations_for_sales_invoice(allocation.reference_name, receipt_no)

					for existing_allocation in allocations_exists:
						previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount

					invoice_total = previous_paid_amount + allocation.paying_amount

					frappe.db.set_value("Sales Invoice", allocation.reference_name, {'paid_amount': invoice_total})
	def update_sales_return(self):
		allocations = self.receipt_allocation

		if(allocations):
			for allocation in allocations:
				if(allocation.paying_amount>0):

					receipt_no = self.name
					if self.is_new():
						receipt_no = ""

					previous_paid_amount = 0
					allocations_exists = get_allocations_for_sales_return(allocation.reference_name, receipt_no)

					for existing_allocation in allocations_exists:
						previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount

					invoice_total = previous_paid_amount + allocation.paying_amount

					frappe.db.set_value("Sales Return", allocation.reference_name, {'paid_amount': invoice_total})
	def update_credit_note(self):
		allocations = self.receipt_allocation

		if(allocations):
			for allocation in allocations:
				if(allocation.paying_amount>0):

					receipt_no = self.name
					if self.is_new():
						receipt_no = ""

					previous_paid_amount = 0
					allocations_exists = get_allocations_for_credit_note(allocation.reference_name, receipt_no)

					for existing_allocation in allocations_exists:
						previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount

					invoice_total = previous_paid_amount + allocation.paying_amount

					frappe.db.set_value("Credit Note", allocation.reference_name, {'grand_total': invoice_total})

	def insert_gl_records(self):

		print("From insert gl records")

		# default_company = frappe.db.get_single_value(
		# 	"Global Settings", "default_company")

		# default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
		# 																	'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)
		idx = 1

		# Trade Receivable - Debit
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Receipt Entry"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = self.account
		gl_doc.debit_amount = self.amount
		gl_doc.against_account = self.GetAccountForTheHighestAmountInPayments()
		gl_doc.remarks = self.remarks
		# gl_doc.party_type = "Customer"
		# gl_doc.party = self.customer
		# gl_doc.against_account = default_accounts.default_income_account
		gl_doc.insert()

		receipt_details = self.receipt_entry_details

		if(receipt_details):
			for receipt_entry in receipt_details:
				if(receipt_entry.receipt_type == "Customer"):
					idx = idx + 1
					gl_doc = frappe.new_doc('GL Posting')
					gl_doc.voucher_type = "Receipt Entry"
					gl_doc.voucher_no = self.name
					gl_doc.idx = idx
					gl_doc.posting_date = self.posting_date
					gl_doc.posting_time = self.posting_time
					gl_doc.account = receipt_entry.account
					gl_doc.credit_amount = receipt_entry.amount
					gl_doc.party_type = "Customer"
					gl_doc.party = receipt_entry.customer
					gl_doc.against_account = self.account
					gl_doc.remarks = self.remarks
					gl_doc.insert()

				else:
					idx = idx + 1
					gl_doc = frappe.new_doc('GL Posting')
					gl_doc.voucher_type = "Receipt Entry"
					gl_doc.voucher_no = self.name
					gl_doc.idx = idx
					gl_doc.posting_date = self.posting_date
					gl_doc.posting_time = self.posting_time
					gl_doc.account = receipt_entry.account
					gl_doc.credit_amount = receipt_entry.amount
					gl_doc.against_account = self.account
					gl_doc.remarks = self.remarks
					gl_doc.insert()

	def on_trash(self):
		self.revert_documents_paid_amount_for_receipt()

	def on_cancel(self):
		print("from on cancel")
		self.revert_documents_paid_amount_for_receipt()

		frappe.db.delete("GL Posting",
				{"Voucher_type": "Receipt Entry",
				"voucher_no": self.name
				})

	def GetAccountForTheHighestAmountInPayments(self):

		highestAmount = 0
		account = ""

		receipt_details = self.receipt_entry_details

		if receipt_details:

			for receipt_entry in receipt_details:

				if receipt_entry.amount > highestAmount:
					highestAmount = receipt_entry.amount
					account = receipt_entry.account

		return account

	def revert_documents_paid_amount_for_receipt(self):
		print("onl here")
		allocations = self.receipt_allocation
		if(allocations):
			for allocation in allocations:
				print("allocation.reference_type")
				print(allocation.reference_type)

				if allocation.reference_type == "Sales Invoice":
					if(allocation.paying_amount>0):
						receipt_no = self.name
						if self.is_new():
							receipt_no = ""

						previous_paid_amount = 0
						allocations_exists = get_allocations_for_sales_invoice(allocation.reference_name, receipt_no)
						for existing_allocation in allocations_exists:
							previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount

						total_paid_Amount = previous_paid_amount
						frappe.db.set_value("Sales Invoice", allocation.reference_name, {'paid_amount': total_paid_Amount})
