# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.purchase_invoice_api import get_allocations_for_invoice

class PaymentEntry(Document):    

	@frappe.whitelist()
	def get_supplier_pending_payments(supplier):
		
		receipt_values = frappe.get_list("Purchase Invoice", fields=['name', 'rounded_total','paid_amount'], filters =
									{'supplier':['=',supplier],'is_credit': ['=',True], 'paid_amount':['<', 'rounded_total']}
									)
	
		return {'values': receipt_values}

	def before_save(self):
		# By default allocations are not visisble. So make show_allocations make false
		# to allow user to click on show allocations for the visibility of allocations   
  
		self.show_allocations = False
  
	def validate(self):
     
		self.validate_doc_status()
		# self.clean_deleted_allocations()
		self.check_allocations_and_totals()
		self.check_excess_allocation()
    
	def validate_doc_status(self):
		if self.amount == 0:
			frappe.throw("Cannot save the document with out valid inputs.")
            
    # Cleaning the deleted allocations is crucial, so this method should call even though it cleans with the client side javascript code
	def clean_deleted_allocations(self):
		
		allocations = self.payment_allocation
  
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
        
	def check_allocations_and_totals(self):
		payment_details = self.payment_entry_details
		total =0
		total_allocated = 0
		if(payment_details):
			for payment_entry in payment_details:
				if(payment_entry.allocated_amount and payment_entry.allocated_amount>0):
					if(payment_entry.amount!= payment_entry.allocated_amount):
						frappe.throw("Allocated amount mismatch.")
				total = total+ payment_entry.amount
				total_allocated = total_allocated +  payment_entry.allocated_amount
    
		if(self.amount != total):
			frappe.throw("Mismatch in total amount. Please check the document inputs")
   
		if(self.allocated_amount != total_allocated):
			frappe.throw("Mismatch in total allocated amount. Please check the document inputs")
    
      
	def check_excess_allocation(self):
         
		allocations = self.payment_allocation

		if(allocations):
			for allocation in allocations:
				if(allocation.paying_amount>0):					
					is_new = self.is_new()
					print("self.is_new()")
					print(self.is_new())
		
					payment_no = self.name
					if self.is_new():
						payment_no = ""
		
					previous_paid_amount = 0
					allocations_exists = get_allocations_for_invoice(allocation.purchase_invoice, payment_no)
		
					for existing_allocation in allocations_exists:
						previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount
		
					if allocation.paying_amount > allocation.invoice_amount-previous_paid_amount:
						frappe.throw("Excess allocation for the invoice numer " + allocation.purchase_invoice )
      
	def before_submit(self):     
		self.call_before_submit()

	def call_before_submit(self):
     	# Again make sure there is no excess allocation, before during submit
		self.check_excess_allocation()
		self.update_sales_invoices()
		self.insert_gl_records()

	def update_sales_invoices(self):
		
		allocations = self.payment_allocation

		if(allocations):
			for allocation in allocations:
				if(allocation.paying_amount>0):
		
					payment_no = self.name
					if self.is_new():
						payment_no = ""      
		
					previous_paid_amount = 0
					allocations_exists = get_allocations_for_invoice(allocation.purchase_invoice, payment_no)
		
					for existing_allocation in allocations_exists:
						previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount
      
					invoice_total = previous_paid_amount + allocation.paying_amount

					frappe.db.set_value("Purchase Invoice", allocation.purchase_invoice, {'paid_amount': invoice_total})
    
	def insert_gl_records(self):

		print("From insert gl records")

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
		# gl_doc.party_type = "Customer"
		# gl_doc.party = self.customer
		# gl_doc.aginst_account = default_accounts.default_income_account
		gl_doc.insert()
  
		payment_details = self.payment_entry_details
		
		if(payment_details):
			for payment_entry in payment_details:
				if(payment_entry.payment_type == "Supplier"):
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