# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime
from frappe.utils import get_time

class ShiftAllocation(Document):	
 
	def validate(self):
     
		if frappe.db.exists("Shift Allocation", {
			"employee": self.employee,
			"shift_date": self.shift_date,
			"name": ["!=", self.name]
		}):
			frappe.throw("Shift allocation already exists for the employee for the same date.")
   
		if self.shift_payment_unit == "HRS":
			if not self.expected_end_time:
				frappe.throw("Expected End Time is required.")
		else:
			if not self.expected_no_of_units:
				frappe.throw("Expected No of units is required.")

   
	def before_validate(self):
     
		if self.shift_payment_unit == "HRS":

				expected_end_time_obj = datetime.combine(datetime.min, get_time(self.expected_end_time))
				shift_end_time_obj = datetime.combine(datetime.min, get_time(self.end_time))
		
				if expected_end_time_obj> shift_end_time_obj:
					# Calculate the total hours between from_time and to_time
					total_seconds = (expected_end_time_obj-shift_end_time_obj).total_seconds() 
					total_hours, remainder = divmod(total_seconds, 3600)
					minutes, seconds = divmod(remainder, 60)
			
					mins_to_hours = minutes/60;
			
					total_hours = total_hours + mins_to_hours
					self.expected_ot = round(total_hours,2)       		
		else:
			
			if self.expected_no_of_units > self.payment_units_per_day:
       
				self.expected_ot = self.expected_no_of_units - self.payment_units_per_day
    
def on_submit(self):
    self.update_shift_allocation_count()
    
    
def update_shift_allocation_count(self):
    allocation_count = frappe.db.count('Shift Allocation', {'shift': self.shift, 'docstsatus':1})
    
    frappe.db.set_value('Shift', self.shift, 'allocation_count', allocation_count)