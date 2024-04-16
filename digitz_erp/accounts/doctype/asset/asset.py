# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe

from frappe.model.document import Document
from datetime import datetime
from dateutil.relativedelta import relativedelta


class Asset(Document):

	def validate_asset(self):
		
		if not self.opening_depreciation and not self.purchase_invoice:
			frappe.throw("Either purchase invoice details or open depreciation is mandatory.")      

	def validate(self):		
		self.validate_asset()
		self.validate_salvage_value()

	def before_validate(self):
		self.value_afer_depreciation = self.gross_amount - (self.opening_depreciation if self.opening_depreciation else 0)

	def on_submit(self):
		self.do_posting_for_asset()
		self.make_depreciations()

	def do_posting_for_asset(self): 

		
		# Create GL Posting with asset_value_after_depreciation

		idx =1
		# Trade Payable - Credit - Against Inventory A/c
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Asset"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = self.asset_account
		gl_doc.debit_amount = self.value_after_depreciation		
		gl_doc.against_account = self.asset_credit_account
		
		gl_doc.remarks = f"Asset valuation for - {self.asset_name}"
		gl_doc.insert()
		idx +=1

		# Trade Payable - Credit - Against Inventory A/c
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Asset"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account =  self.asset_credit_account
		gl_doc.credit_amount = self.value_after_depreciation		
		gl_doc.against_account = self.asset_account		
		gl_doc.remarks = f"Asset valuation for - {self.asset_name}"
		gl_doc.insert()
		idx +=1  
		
		return True

	def validate_salvage_value(self):
		
		life_duration =self.total_number_of_depreciation

		per_month_depreciation = self.gross_amount / life_duration

		if(self.salvage_value > per_month_depreciation):
			frappe.msgprint(f"Salvage value cannot be greater than per month depreciation: {per_month_depreciation}")

	def make_depreciations(self):
		
		frequency = self.doc.frequency_in_months
		rate = self.doc.rate_of_depreciation

		last_book_value =  self.gross_amount - (self.opening_depreciation if self.opening_depreciation else 0)

		life_duration =self.total_number_of_depreciation

		per_month_depreciation = self.gross_amount / life_duration

		depreciation_for_frequency = per_month_depreciation * self.frequency_in_months

		if(last_book_value> self.salvage_value):
			value_exists = True
   
		depreciation_date = self.posting_date
		accumulated_depreciation = 0

		while value_exists:
      
			depreciation_date = self.get_next_depreciation_date(depreciation_date,frequency)
			
			if last_book_value>= depreciation_for_frequency:
       
				opening_deprecation = accumulated_depreciation       
				accumulated_depreciation = accumulated_depreciation + depreciation_for_frequency    
				book_value = last_book_value - depreciation_for_frequency
        
				self.create_a_depreciation_schedule(depreciation_date, opening_depreciation=opening_deprecation, depreciation=depreciation_for_frequency,accumulated_depreciation=accumulated_depreciation, book_value =book_value)
				
				last_book_value = book_value
    
			else: # For last depreciation entry

				if last_book_value> self.salvage_value:        
					  
					opening_deprecation = accumulated_depreciation       
					depreciation = last_book_value - self.salvage_value
					accumulated_depreciation = accumulated_depreciation + depreciation
					book_value = self.salvage_value
          
					self.create_a_depreciation_schedule(depreciation_date, opening_depreciation=opening_deprecation, depreciation=depreciation, accumulated_depreciation=accumulated_depreciation, book_value=book_value)
					last_book_value = book_value     
					value_exists= False
     
				else: #if last_book_value == salvage_value(last book value meets salvage value)
					value_exists = False
		
	def create_a_depreciation_schedule(self, depreciation_date, opening_depreciation,depreciation, accumulated_depreciation,book_value):
		
		depreciation_schedule = frappe.new_doc("Asset Depreciation Schedule")
		depreciation_schedule.asset = self.name
		depreciation_schedule.opening_depreciation = opening_depreciation
		depreciation_schedule.date_of_depreciation = depreciation_date
		depreciation_schedule.depreciation = depreciation
		depreciation_schedule.accumulated_depreciation = accumulated_depreciation
		depreciation_schedule.book_value = book_value
		depreciation_schedule.posting_status = "Scheduled"
		depreciation_schedule.save()

	def get_next_depreciation_date(start_date, frequency):
		
		"""
		Calculate the next depreciation date based on the start date and frequency.

		:param start_date: The start date of depreciation (YYYY-MM-DD format)
		:param frequency: How often (in months) depreciation occurs (e.g., 1 for monthly, 2 for bi-monthly, etc.)
		:return: The next depreciation date as a string in YYYY-MM-DD format
		"""
		# Convert start_date string to datetime object
		depreciation_date = datetime.strptime(start_date, '%Y-%m-%d')

		# Calculate the next depreciation date based on the frequency
		next_depreciation_date = depreciation_date + relativedelta(months=frequency)

		return next_depreciation_date.strftime('%Y-%m-%d')
