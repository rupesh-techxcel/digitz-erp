# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.sales_invoice_api import get_allocations_for_invoice

class ReceiptEntry(Document):    

	@frappe.whitelist()
	def get_customer_pending_receipts(customer):
		
		receipt_values = frappe.get_list("Sales Invoice", fields=['name', 'rounded_total','paid_amount'], filters =
									{'customer':['=',customer],'is_credit': ['=',True], 'paid_amount':['<', 'rounded_total']}
									)
	
		return {'values': receipt_values}

	def before_save(self):
		# By default allocations are not visisble. So make show_allocations make false
		# to allow user to click on show allocations for the visibility of allocations   
  
		self.show_allocations = False
  
	def validate(self):
     
		self.validate_doc_status()
		self.clean_deleted_allocations()
		self.check_allocations_and_totals()
		self.check_excess_allocation()
    
	def validate_doc_status(self):
		if self.amount == 0:
			frappe.throw("Cannot save the document with out valid inputs.")
            
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
		total =0
		total_allocated = 0
		if(receipt_details):
			for receipt_entry in receipt_details:
				if(receipt_entry.allocated_amount and receipt_entry.allocated_amount>0):
					if(receipt_entry.amount!= receipt_entry.allocated_amount):
						frappe.throw("Allocated amount mismatch.")
				total = total+ receipt_entry.amount
    
				print("total_allocated")
				print(total_allocated)
				print("receipt_entry.allocated_amount")
				print(receipt_entry.allocated_amount)    
				
				total_allocated = total_allocated + (receipt_entry.allocated_amount if receipt_entry.allocated_amount is not None else 0)
    
		if(self.amount != total):
			frappe.throw("Mismatch in total amount. Please check the document inputs")
   
		if(self.allocated_amount != total_allocated):
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

					print("allocation.sales_invoice")
					print(allocation.sales_invoice)
		
					previous_paid_amount = 0
					allocations_exists = get_allocations_for_invoice(allocation.sales_invoice, receipt_no)
		
					for existing_allocation in allocations_exists:
						previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount
		
					if allocation.paying_amount > allocation.invoice_amount-previous_paid_amount:         
						print("throws error")      
						frappe.throw("Excess allocation for the invoice numer " + allocation.sales_invoice )
      
		print("checking control")
      
	def before_submit(self):   
		self.do_posting()
		# frappe.enqueue(self.do_posting, self=self,queue="long")

	def do_posting(self):
		self.check_excess_allocation()
		print("before calliong update_sales_invoices")
		self.update_sales_invoices()
		self.insert_gl_records()


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
					allocations_exists = get_allocations_for_invoice(allocation.sales_invoice, receipt_no)
		
					for existing_allocation in allocations_exists:
						previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount
      
					invoice_total = previous_paid_amount + allocation.paying_amount

					frappe.db.set_value("Sales Invoice", allocation.sales_invoice, {'paid_amount': invoice_total})
    
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
		# gl_doc.party_type = "Customer"
		# gl_doc.party = self.customer
		# gl_doc.aginst_account = default_accounts.default_income_account
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
					gl_doc.aginst_account = self.account
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
					gl_doc.aginst_account = self.account
					gl_doc.insert()