# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class EmployeeHolidayList(Document):
	
	def validate(self):
     
		holiday_list = frappe.get_doc("Holiday List", self.holiday_list)
  
		if holiday_list.default_for_the_leave_period:
			frappe.throw("You cannot assign the default Holiday List for the leave period. To override it, please select a different Holiday List.")
   
		self.check_duplicate_holiday_entry()

	def check_duplicate_holiday_entry(self):
		
		existing_entry = frappe.db.exists(
			"Employee Holiday List",
			{
				"employee": self.employee,
				"leave_period": self.leave_period
			}
		)
		
		# Check if the found entry is not the current document
		if existing_entry and existing_entry != self.name:
			frappe.throw(("Employee {0} already has a holiday list entry for the period {1}.")
							.format(self.employee, self.leave_period))