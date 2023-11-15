# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime

class ExpenseEntry(Document):

	def on_submit(self):  
		print("from on submit")		
		self.postings_start_time = datetime.now()		
		frappe.enqueue(self.do_postings_on_submit, queue="long")

	def do_postings_on_submit(self):
		print("from do_postings_on_submit")
		self.insert_gl_records()
		self.gl_posted_time = datetime.now()		
		self.insert_payment_postings()
		self.payment_posted_time = datetime.now()
		self.save()

	def insert_gl_records(self):
     
		idx = 1
		
		# Debit Expenses
		for expense_entry in self.expense_entry_details:
   
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Expense Entry'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = expense_entry.expense_date			
			gl_doc.account = expense_entry.expense_account
			gl_doc.debit_amount = expense_entry.amount
			gl_doc.remarks = self.remarks;
			gl_doc.insert()
   
			idx += 1
   
		# Debit Tax Amounts
		taxes = self.get_tax_totals()
		print("taxes")
		print(taxes)

		for key, tax_amount  in taxes.items():
			
			print("key")
			print(key)
   
			tax_for_expense, expense_date = key.split('_')   
   
			print("tax_for_expense")
			print(tax_for_expense)
   
			tax = frappe.get_doc("Tax", tax_for_expense)
		
			if(tax.tax_rate >0):
				gl_doc = frappe.new_doc('GL Posting')
				gl_doc.idx = idx
				gl_doc.voucher_type = 'Expense Entry'
				gl_doc.voucher_no = self.name
				gl_doc.posting_date = expense_date
				gl_doc.account = tax.account
				gl_doc.debit_amount = tax_amount
				gl_doc.remarks = self.remarks;
				gl_doc.insert()
   
		# Credit Payable Accounts, supplier  
		payable_items = self.get_payable_totals()

		for key, amount  in payable_items.items():
      
			payable_account, supplier, expense_date = key.split('_') 
   
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Expense Entry'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = expense_date			
			gl_doc.account = payable_account
			gl_doc.party_type = "Supplier"
			gl_doc.party = supplier
			gl_doc.credit_amount = amount
			gl_doc.remarks = self.remarks;
			gl_doc.insert()
	
	def get_payable_totals(self):
     
		payable_account_dictionary = {}
  
		for expense_entry in self.expense_entry_details:	
      
			payable_account = expense_entry.get("payable_account")
			supplier = expense_entry.get("supplier")
			expense_date = expense_entry.get("expense_date") 
			total = expense_entry.get("total")
			key = f"{payable_account}_{supplier}_{expense_date}"
   
			if key in payable_account_dictionary:
				payable_account_dictionary[key] += total
			else:
				payable_account_dictionary[key] = total
    
		return payable_account_dictionary

	# Need to consider the payment account for each expense date
	def get_payment_totals(self):
     
		payment_account_dictionary = {}
  
		for expense_entry in self.expense_entry_details:	
      
			payment_account = self.payment_account

			expense_date = expense_entry.get("expense_date") 
			
			key = f"{payment_account}_{expense_date}"
   
			if key in payment_account_dictionary:
				payment_account_dictionary[key] += expense_entry.total
			else:
				payment_account_dictionary[key] = expense_entry.total
    
		return payment_account_dictionary
   
	def get_tax_totals(self):
		tax_dictionary = {}

		for expense_entry in self.expense_entry_details:
			tax_amount = expense_entry.get("tax_amount")
   
			if(tax_amount>0):
				tax = expense_entry.get("tax")
				tax_amount = expense_entry.get("tax_amount")
				expense_date = expense_entry.get("expense_date") 

				print("tax from get_tax_totals")
				print(tax)

				# Use the expense_date in the key along with tax, separated by an underscore
				key = f"{tax}_{expense_date}"
				print("key from get_tax_totals")
				print(key)

				if key in tax_dictionary:
					tax_dictionary[key] += tax_amount
				else:
					tax_dictionary[key] = tax_amount
    
		print("tax_dictionary")
		print(tax_dictionary)
		return tax_dictionary

	def insert_payment_postings(self):
     
		if self.credit_expense == 0:
	
			gl_count = frappe.db.count('GL Posting',{'voucher_type':'Expense Entry', 'voucher_no': self.name})

			idx= gl_count + 1
			payable_items = self.get_payable_totals()

			for key, amount  in payable_items.items():
		
				payable_account, supplier,expense_date = key.split('_') 
	
				gl_doc = frappe.new_doc('GL Posting')
				gl_doc.idx = idx
				gl_doc.voucher_type = 'Expense Entry'
				gl_doc.voucher_no = self.name
				gl_doc.posting_date = expense_date			
				gl_doc.account = payable_account
				gl_doc.party_type = "Supplier"
				gl_doc.party = supplier
				gl_doc.debit_amount = amount
				gl_doc.remarks = self.remarks;
				gl_doc.insert()
   
		payment_items = self.get_payment_totals()

		for key,amount in payment_items.items():
			payment_account,expense_date = key.split('_') 
   
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Expense Entry'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = expense_date			
			gl_doc.account = payment_account			
			gl_doc.credit_amount = amount
			gl_doc.remarks = self.remarks;
			gl_doc.insert()
       
	def on_update(self):
		self.update_payment_schedules()

	def update_payment_schedules(self):
     
		existing_entries = frappe.get_all("Payment Schedule", filters={"payment_against": "Expense", "document_no": self.name})
  
		
		# Delete existing payment schedules if found
		for entry in existing_entries:
			try:
				frappe.delete_doc("Payment Schedule", entry.name)
			except Exception as e:
				frappe.log_error("Error deleting payment schedule: " + str(e))		
    

		print("self.payment_schedule")
		print(self.payment_schedule)

		for payment_schedule in self.payment_schedule:
   
			new_payment_schedule = frappe.new_doc("Payment Schedule")
			new_payment_schedule.payment_against = "Expense"
			new_payment_schedule.supplier = payment_schedule.supplier
			new_payment_schedule.document_no = self.name
			new_payment_schedule.document_date = self.posting_date
			new_payment_schedule.scheduled_date = payment_schedule.date
			new_payment_schedule.amount = payment_schedule.amount
			
			try:
				new_payment_schedule.insert()
				frappe.msgprint("payment schedule added successfully",indicator="green", alert = True)
			except Exception as e:
				frappe.log_error("Error creating payment schedule: " + str(e))
				frappe.msgprint("An error occured while inserting payment schedule",indicator="red", alert = True)


		frappe.db.commit()

