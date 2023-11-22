# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.payment_entry_api import get_allocations_for_purchase_invoice, get_allocations_for_expense_entry
class PaymentEntry(Document):

	
	temp_payment_allocation = None
	# def before_save(self):
	# 	# By default allocations are not visisble. So make show_allocations make false
	# 	# to allow user to click on show allocations for the visibility of allocations
	#
	# 	self.show_allocations = False
	def validate(self):
		self.validate_doc_status()		
		self.check_reference_numbers()
		self.check_allocations_and_totals()
		self.check_excess_allocation()		

	def validate_doc_status(self):
		if self.amount == 0:
			frappe.throw("Cannot save the document with out valid inputs.")

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

	def check_reference_numbers(self):
		
		if self.mode != "Bank":
			return

		payment_details = self.payment_entry_details
		if(payment_details):
			for payment_detail in payment_details: 
				if not payment_detail.reference_no or not payment_detail.reference_date:
					frappe.throw("Reference No and Date required at line number {}".format(payment_detail.idx))
       
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

				print('Total:', total_amount_in_rows)
				total_allocated_in_rows = total_allocated_in_rows +  payment_detail.allocated_amount
				print('Total:', total_allocated_in_rows)
    
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
			if(self.allocated_amount != total_allocated_in_rows):
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

					if(allocation.reference_type == "Purchase Invoice"):
						
						allocations_exists = get_allocations_for_purchase_invoice(allocation.reference_name, payment_no)
						print('allocations_exists :', allocations_exists)

					if(allocation.reference_type == "Expense Entry"):
						
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
	
		
		self.clean_deleted_allocations()    
		self.update_purchase_invoices()
		self.update_expense_entry()
		self.update_reference_in_payment_allocations()
	
	def before_validate(self):
     
		# There is an error while saving the document with the payment_allocation child table.
		# It is assumed that the error is because of the payment_allocation is being generated 
		# using javascript method. Somehow it throws the error that 'Payment Allocation 9049423 (name of the document)
		# already exists. To resolve it saving the child table to the temporary variable and restore it
		# in the on_update method. And its working fine.
		
		# The issue happens only before the first save.
  
		# Checking self.temp_payment_allocation == None to avoid recurssion (issue fix)
		print("from before_validate method")
		print("self.temp_payment_allocation")
		print(self.temp_payment_allocation)
		print("self.payment_allocation")
		print(self.payment_allocation)	
  
		if(self.temp_payment_allocation is None):
			print("temp_payment_allocation is None")
   
		if(self.payment_allocation is None):
			print("payment_allocation is None")

		if self.is_new() and self.payment_allocation and self.temp_payment_allocation == None:
			# Store the existing payment_allocation in a temporary variable
			self.temp_payment_allocation = self.get("payment_allocation")
			
			# Clear existing payment_allocation entries
			self.set("payment_allocation", [])
	
	def on_submit(self):
		self.call_on_submit()

	def call_on_submit(self):
		frappe.enqueue(self.do_postings, queue ="long")
     
	def do_postings(self):
		self.insert_gl_records()
		self.insert_gl_records_for_expense()
		
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

	def update_expense_entry(self):
		if self.payment_allocation:
			for allocation in self.payment_allocation:
				if allocation.reference_type == "Expense Entry":
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
		gl_doc.credit_amount = self.amount
		gl_doc.insert()

		payment_details = self.payment_entry_details

		if(payment_details):
			for payment_entry in payment_details:
				if(payment_entry.reference_type == "Purchase Invoice"):
					idx = idx + 1
					gl_doc = frappe.new_doc('GL Posting')
					gl_doc.voucher_type = "Payment Entry"
					gl_doc.voucher_no = self.name
					gl_doc.idx = idx
					gl_doc.posting_date = self.posting_date
					gl_doc.posting_time = self.posting_time
					gl_doc.account = payment_entry.account
					gl_doc.debit_amount = payment_entry.amount
					gl_doc.party_type = "Supplier"
					gl_doc.party = payment_entry.supplier
					gl_doc.aginst_account = self.account
					gl_doc.insert()
				else:
					idx = idx + 1
					gl_doc = frappe.new_doc('GL Posting')
					gl_doc.voucher_type = "Payment Entry"
					gl_doc.voucher_no = self.name
					gl_doc.idx = idx
					gl_doc.posting_date = self.posting_date
					gl_doc.posting_time = self.posting_time
					gl_doc.account = payment_entry.account
					gl_doc.debit_amount = payment_entry.amount
					gl_doc.aginst_account = self.account
					gl_doc.insert()


	def insert_gl_records_for_expense(self):
		idx = 1
		# Trade Receivable - Debit
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Payment Entry"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = self.account
		gl_doc.credit_amount = self.amount
		gl_doc.insert()

		payment_details = self.payment_entry_details

		if(payment_details):
			for payment_entry in payment_details:
				if(payment_entry.reference_type == "Expense"):
					idx = idx + 1
					gl_doc = frappe.new_doc('GL Posting')
					gl_doc.voucher_type = "Payment Entry"
					gl_doc.voucher_no = self.name
					gl_doc.idx = idx
					gl_doc.posting_date = self.posting_date
					gl_doc.posting_time = self.posting_time
					gl_doc.account = payment_entry.account
					gl_doc.debit_amount = payment_entry.amount
					gl_doc.party_type = "Supplier"
					gl_doc.party = payment_entry.supplier
					gl_doc.aginst_account = self.account
					gl_doc.insert()

				else:
					idx = idx + 1
					gl_doc = frappe.new_doc('GL Posting')
					gl_doc.voucher_type = "Payment Entry"
					gl_doc.voucher_no = self.name
					gl_doc.idx = idx
					gl_doc.posting_date = self.posting_date
					gl_doc.posting_time = self.posting_time
					gl_doc.account = payment_entry.account
					gl_doc.debit_amount = payment_entry.amount
					gl_doc.aginst_account = self.account
					gl_doc.insert()
