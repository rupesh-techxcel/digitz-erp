# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.payment_entry_api import get_allocations_for_purchase_invoice, get_allocations_for_expense_entry, get_allocations_for_purchase_return,get_allocations_for_debit_note
from datetime import datetime,timedelta
from digitz_erp.api.document_posting_status_api import init_document_posting_status, update_posting_status
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type
from digitz_erp.api.bank_reconciliation import create_bank_reconciliation, cancel_bank_reconciliation

class PaymentEntry(Document):

	temp_payment_allocation = None
	# def before_save(self):
	# 	# By default allocations are not visisble. So make show_allocations make false
	# 	# to allow user to click on show allocations for the visibility of allocations
	#
	# 	self.show_allocations = False

	def Voucher_In_The_Same_Time(self):
		possible_invalid= frappe.db.count('Payment Entry', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time]})
		return possible_invalid

	def Set_Posting_Time_To_Next_Second(self):
		datetime_object = datetime.strptime(str(self.posting_time), '%H:%M:%S')

		# Add one second to the datetime object
		new_datetime = datetime_object + timedelta(seconds=1)

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

		self.assign_missing_reference_nos()
		self.clean_deleted_allocations()

		# There is an error while saving the document with the payment_allocation child table.
		# It is assumed that the error is because of the payment_allocation is being generated
		# using javascript method. Somehow it throws the error that 'Payment Allocation 9049423 (name of the document)
		# already exists. To resolve it saving the child table to the temporary variable and restore it
		# in the on_update method. And its working fine.

		# The issue happens only before the first save.

		# Checking self.temp_payment_allocation == None to avoid recurssion (issue fix)

		if self.is_new() and self.payment_allocation and self.temp_payment_allocation == None:
			# Store the existing payment_allocation in a temporary variable
			self.temp_payment_allocation = self.get("payment_allocation")

			# Clear existing payment_allocation entries
			self.set("payment_allocation", [])

			print("self.temp_payment_allocation")
			print(self.temp_payment_allocation)

		self.update_reference_in_payment_allocations()

		self.postings_start_time = datetime.now()

	def validate(self):
		print("validation starts..")
		self.validate_doc_status()
		self.check_reference_numbers()
		self.check_allocations_and_totals()
		self.check_excess_allocation()
		print("Validation done")

	def validate_doc_status(self):
		if self.amount == 0:
			frappe.throw("Cannot save the document with out valid inputs.")

		if not self.payment_entry_details:
			frappe.throw("No valid payment entries found to save the document")

		for payment_entry in self.payment_entry_details:
			if payment_entry.payment_type == "Other" and (payment_entry.reference_type == "Purchase Invoice" or payment_entry.reference_type == "Expense Entry"):
				messge = """Invalid reference type found at line {0} """.format(payment_entry.idx)
				frappe.throw(messge)

			if payment_entry.payment_type == "Other" and payment_entry.supplier:
				messge = """Supplier should not be selected with the payment type 'Other', at line {0} """.format(payment_entry.idx)
				frappe.throw(messge)

			print("supplier")
			print(payment_entry.supplier)

			if payment_entry.payment_type == "Supplier" and (not payment_entry.supplier):
				messge = """Supplier is mandatory for the payment type Supplier, at line {0} """.format(payment_entry.idx)
				frappe.throw(messge)

			if (payment_entry.reference_type == "Purchase Invoice" or payment_entry.reference_type=="Expense Entry" or payment_entry.reference_type=="Purchase Return" or payment_entry.reference_type=="Debit Note") and (not payment_entry.supplier):
				messge = """Supplier is mandatory for the referene type Purchase Invoice/ Expense Entry/ Purchase Return/ Debit Note, at line {0} """.format(payment_entry.idx)
				frappe.throw(messge)

			if (payment_entry.reference_type == "Purchase Invoice" or payment_entry.reference_type=="Expense Entry" or payment_entry.reference_type=="Purchase Return" or payment_entry.reference_type=="Debit Note") and payment_entry.supplier and payment_entry.allocated_amount ==0:
				messge = """Allocation not found for the payment at line {0} """.format(payment_entry.idx)
				frappe.throw(messge)


    # Cleaning the deleted allocations is crucial, so this method should call even though it cleans with the client side javascript code
	def clean_deleted_allocations(self):

		allocations = self.payment_allocation
		print('allocations :', allocations)

		if(allocations):
			for allocation in allocations[:]:

				payment_details = self.payment_entry_details
				allocation_exist = False
				if payment_details:
					for payment_entry in payment_details:
						if payment_entry.supplier == allocation.supplier and payment_entry.allocated_amount and payment_entry.allocated_amount>0:
							allocation_exist= True
					if allocation_exist==False:
						self.payment_allocation.remove(allocation)

	def assign_missing_reference_nos(self):
		if self.payment_mode != "Bank":
				return
		payment_details = self.payment_entry_details

		if payment_details:
			for payment_detail in payment_details:
				if not payment_detail.reference_no:
					if(self.reference_no):
						payment_detail.reference_no = self.reference_no

				if not payment_detail.reference_date:
					if(self.reference_date):
						payment_detail.reference_date = self.reference_date

	def check_reference_numbers(self):

		if self.payment_mode != "Bank":
			return

		payment_details = self.payment_entry_details
		if(payment_details):
			for payment_detail in payment_details:
				if not payment_detail.reference_no or not payment_detail.reference_date:
					frappe.throw("Reference No and Reference Date are mandatory for bank payment, at line number {} in Payment Entry Details".format(payment_detail.idx))

	def check_allocations_and_totals(self):
		payment_details = self.payment_entry_details
		total_amount_in_rows = 0
		total_allocated_in_rows = 0
		if(payment_details):
			for payment_detail in payment_details:

				total_amount_in_rows = total_amount_in_rows+ payment_detail.amount

				if payment_detail.payment_type != "Supplier":
					continue

				# If there is an allocation in the lineitem make sure the amount and allocated amount are same
				if(payment_detail.allocated_amount and payment_detail.allocated_amount>0):
					if(payment_detail.amount!= payment_detail.allocated_amount):
						frappe.throw("Allocated amount mismatch.")

				if(payment_detail.allocated_amount):
					total_allocated_in_rows = total_allocated_in_rows +  payment_detail.allocated_amount


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

		allocations = self.payment_allocation

		if(allocations):
			for allocation in allocations:
				if(allocation.paying_amount>0):

					payment_no = self.name
					if self.is_new():
						payment_no = ""

					allocations_exists = None
					previous_paid_amount = 0
					if(allocation.reference_type == "Purchase Return"):

						allocations_exists = get_allocations_for_purchase_return(allocation.reference_name, payment_no)
						print('allocations_exists :', allocations_exists)

					if(allocation.reference_type == "Debit Note"):

						allocations_exists = get_allocations_for_debit_note(allocation.reference_name, payment_no)
						print('allocations_exists :', allocations_exists)

					if(allocation.reference_type == "Purchase Invoice"):

						allocations_exists = get_allocations_for_purchase_invoice(allocation.reference_name, payment_no)
						print('allocations_exists :', allocations_exists)

					if(allocation.reference_type == "Expense Entry Details"):

						allocations_exists = get_allocations_for_expense_entry(allocation.reference_name, payment_no)
						print('allocations_exists :', allocations_exists)

					for existing_allocation in allocations_exists:
						previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount

					if allocation.paying_amount > allocation.total_amount-previous_paid_amount:
						frappe.throw("Excess allocation for the invoice number " + allocation.reference_name )

	# def on_trash(self):
		# Delete allocations
		# frappe.db.delete('Payment Allocation',{'item': docitem.item, 'warehouse': docitem.warehouse})

	def on_update(self):
		# Restore the child table payment_allocation from the temporary variable.
		# The reason to do this is mentioned in the comment section of  before_validate
		# if self.is_new():

		# Checking for, not self.payment_allocation to not to execute the code again since
  		# the issue happens only one time and need to execute it only after self.payment_allocation made

		print("from on_update")

		if self.temp_payment_allocation and not self.payment_allocation:

			for  data in self.temp_payment_allocation:
				row = self.append("payment_allocation", {})
				row.reference_type = data.reference_type
				row.reference_name  = data.reference_name
				row.supplier = data.supplier
				row.total_amount = data.total_amount
				row.paid_amount = data.paid_amount
				row.paying_amount = data.paying_amount
				row.balance_amount = data.balance_amount
				row.payment_entry_detail = data.payment_entry_detail

			self.save()	# This will call the before_validate method again.


		self.update_purchase_invoices()
		self.update_expense_entry()
		self.update_purchase_returns()
		self.update_debit_note()

	def on_submit(self):

		init_document_posting_status(self.doctype,self.name)

		turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

		# if(frappe.session.user == "Administrator" and turn_off_background_job):
		# 	self.do_postings_on_submit()
		# else:
		# 	frappe.enqueue(self.do_postings_on_submit, queue ="long")
   
		self.do_postings_on_submit()

	def on_trash(self):
		self.revert_documents_paid_amount_for_payment()

	def on_cancel(self):
		cancel_bank_reconciliation("Sales Invoice", self.name)
		print("from on cancel")
		self.revert_documents_paid_amount_for_payment()

		delete_gl_postings_for_cancel_doc_type('Payment Entry',self.name)

		# frappe.db.delete("GL Posting",
        #                  {"Voucher_type": "Payment Entry",
        #                   "voucher_no": self.name
        #                   })

	def do_postings_on_submit(self):
		self.insert_gl_records()		
		update_posting_status(self.doctype,self.name, 'gl_posted_time')
		update_accounts_for_doc_type('Payment Entry', self.name)
		update_posting_status(self.doctype,self.name,'posting_status','Completed')
		create_bank_reconciliation("Payment Entry", self.name)

	def update_purchase_returns(self):
		allocations = self.payment_allocation
		if(allocations):
			for allocation in allocations:
				if allocation.reference_type == "Purchase Return":
					if(allocation.paying_amount>0):
						payment_no = self.name
						if self.is_new():
							payment_no = ""
						previous_paid_amount = 0
						allocations_exists = get_allocations_for_purchase_return(allocation.reference_name, payment_no)
						for existing_allocation in allocations_exists:
							previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount
						invoice_total = previous_paid_amount + allocation.paying_amount
						frappe.db.set_value("Purchase Return", allocation.reference_name, {'paid_amount': invoice_total})

	def update_debit_note(self):
		allocations = self.payment_allocation
		if(allocations):
			for allocation in allocations:
				if allocation.reference_type == "Debit Note":
					if(allocation.paying_amount>0):
						payment_no = self.name
						if self.is_new():
							payment_no = ""
						previous_paid_amount = 0
						allocations_exists = get_allocations_for_debit_note(allocation.reference_name, payment_no)
						for existing_allocation in allocations_exists:
							previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount
						invoice_total = previous_paid_amount + allocation.paying_amount
						frappe.db.set_value("Debit Note", allocation.reference_name, {'grand_total': invoice_total})


	def update_purchase_invoices(self):
		allocations = self.payment_allocation
		if(allocations):
			for allocation in allocations:
				if allocation.reference_type == "Purchase Invoice":
					if(allocation.paying_amount>0):
						payment_no = self.name
						if self.is_new():
							payment_no = ""
						previous_paid_amount = 0
						allocations_exists = get_allocations_for_purchase_invoice(allocation.reference_name, payment_no)
						for existing_allocation in allocations_exists:
							previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount
						invoice_total = previous_paid_amount + allocation.paying_amount
						frappe.db.set_value("Purchase Invoice", allocation.reference_name, {'paid_amount': invoice_total})

	def revert_documents_paid_amount_for_payment(self):
		allocations = self.payment_allocation
		if(allocations):
			for allocation in allocations:
				print("allocation.reference_type")
				print(allocation.reference_type)

				if allocation.reference_type == "Purchase Return":
					if(allocation.paying_amount>0):
						payment_no = self.name
						if self.is_new():
							payment_no = ""
						previous_paid_amount = 0
						allocations_exists = get_allocations_for_purchase_return(allocation.reference_name, payment_no)
						for existing_allocation in allocations_exists:
							previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount
						total_paid_Amount = previous_paid_amount
						frappe.db.set_value("Purchase Return", allocation.reference_name, {'paid_amount': total_paid_Amount})
				elif allocation.reference_type == "Purchase Invoice":
					if(allocation.paying_amount>0):
						payment_no = self.name
						if self.is_new():
							payment_no = ""
						previous_paid_amount = 0
						allocations_exists = get_allocations_for_purchase_invoice(allocation.reference_name, payment_no)
						for existing_allocation in allocations_exists:
							previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount
						total_paid_Amount = previous_paid_amount
						frappe.db.set_value("Purchase Invoice", allocation.reference_name, {'paid_amount': total_paid_Amount})

				elif allocation.reference_type == "Debit Note":
					if(allocation.paying_amount>0):
						payment_no = self.name
						if self.is_new():
							payment_no = ""
						previous_paid_amount = 0
						allocations_exists = get_allocations_for_debit_note(allocation.reference_name, payment_no)
						for existing_allocation in allocations_exists:
							previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount
						total_paid_Amount = previous_paid_amount
						frappe.db.set_value("Debit Note", allocation.reference_name, {'grand_total': total_paid_Amount})

				elif allocation.reference_type == "Expense Entry Details":
					if(allocation.paying_amount>0):
						payment_no = self.name
						if self.is_new():
							payment_no = ""
						previous_paid_amount = 0
						allocations_exists = get_allocations_for_expense_entry(allocation.reference_name, payment_no)
						for existing_allocation in allocations_exists:
							previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount
						total_paid_Amount = previous_paid_amount
						frappe.db.set_value("Expense Entry Details", allocation.reference_name, {'paid_amount': total_paid_Amount})

	def update_expense_entry(self):
		if self.payment_allocation:
			for allocation in self.payment_allocation:
				if allocation.reference_type == "Expense Entry Details":
					if(allocation.paying_amount>0):
							payment_no = self.name
							if self.is_new():
								payment_no = ""
							previous_paid_amount = 0
							allocations_exists = get_allocations_for_expense_entry(allocation.reference_name, payment_no)
							for existing_allocation in allocations_exists:
								previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount
							invoice_total = previous_paid_amount + allocation.paying_amount
							frappe.db.set_value("Expense Entry Details", allocation.reference_name, {'paid_amount': invoice_total})

	def update_reference_in_payment_allocations(self):
		if self.payment_entry_details and self.payment_allocation:
			for payment_entry in self.payment_entry_details:
				for allocation in self.payment_allocation:
					if payment_entry.supplier == allocation.supplier and payment_entry.reference_type== allocation.reference_type :
						allocation.payment_entry_detail = payment_entry.name


	def insert_gl_records(self):
		# default_company = frappe.db.get_single_value(
		# 	"Global Settings", "default_company")

		# default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
		# 																	'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)
		idx = 1

		# Trade Receivable - Debit
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Payment Entry"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = self.account
		gl_doc.against_account = self.GetAccountForTheHighestAmountInPayments()
		gl_doc.credit_amount = self.amount
		gl_doc.remarks = self.remarks
		gl_doc.insert()

		payment_details = self.payment_entry_details

		if(payment_details):
			for payment_entry in payment_details:

				if(payment_entry.reference_type == "Purchase Invoice") or (payment_entry.reference_type == "Expense Entry") or (payment_entry.reference_type == "Purchase Return") or (payment_entry.reference_type == "Debit Note") :
					idx = idx + 1
					gl_doc = frappe.new_doc('GL Posting')
					gl_doc.voucher_type = "Payment Entry"
					gl_doc.voucher_no = self.name
					gl_doc.idx = idx
					gl_doc.posting_date = self.posting_date
					gl_doc.posting_time = self.posting_time
					gl_doc.account = payment_entry.account
					gl_doc.against_account = self.account
					gl_doc.debit_amount = payment_entry.amount
					gl_doc.party_type = "Supplier"
					gl_doc.party = payment_entry.supplier
					gl_doc.remarks = payment_entry.remarks
					print("payment_entry.remarks")
					print(payment_entry.remarks)
					gl_doc.insert()
				else:
					# Case when there is no allocation, but supplier may or may not selected
					# or payment_type ='Other'
					idx = idx + 1
					gl_doc = frappe.new_doc('GL Posting')
					gl_doc.voucher_type = "Payment Entry"
					gl_doc.voucher_no = self.name
					gl_doc.idx = idx
					gl_doc.posting_date = self.posting_date
					gl_doc.posting_time = self.posting_time
					gl_doc.account = payment_entry.account
					gl_doc.against_account = self.account
					gl_doc.debit_amount = payment_entry.amount
					gl_doc.remarks = payment_entry.remarks
					if payment_entry.supplier:
						gl_doc.party_type = "Supplier"
						gl_doc.party = payment_entry.supplier
					gl_doc.insert()
	
	def GetAccountForTheHighestAmountInPayments(self):

		highestAmount = 0
		account = ""

		payment_details = self.payment_entry_details

		if(payment_details):
			for payment_entry in payment_details:

				if payment_entry.amount > highestAmount:
					highestAmount = payment_entry.amount
					account = payment_entry.account

		return account
