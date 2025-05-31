# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EmployeeHolidayException(Document):

	def validate(self):
		
		# Check employee has a holiday list assigned matching for the date		
		holiday_list = frappe.db.sql("""Select holiday_list from `tabEmployee Holiday List` eh where eh.leave_period_from_date<= %s and eh.leave_period_to_date >=%s and eh.employee=%s and docstatus=1 """, (self.date_for_exception, self.date_for_exception, self.employee), as_dict=True)

		# Employee don't have a holiday list assigned
		if(holiday_list):
		
			holiday = frappe.db.sql("""Select date from `tabHoliday` h inner join `tabHoliday List` hl on h.parent= hl.name  where h.date =%s and hl.name=%s and hl.docstatus=1""", (self.date_for_exception, holiday_list[0].holiday_list), as_dict=True)
	
			if not holiday:				
				frappe.throw("Invalid holiday. No holiday found for the employee matching on this date.") 
		else:
			default_holiday_list_for_period_with_the_date =frappe.db.sql("select name from `tabHoliday List` hl where default_for_the_leave_period=1 and from_date<=%s and to_date>=%s and docstatus=1",(self.date_for_exception, self.date_for_exception))
   
			if not default_holiday_list_for_period_with_the_date:  # Not likely to occur
					frappe.throw("No default Holiday List found for the period on which the date belongs.")    
			else:
				holiday = frappe.db.sql("""Select date from `tabHoliday` h inner join `tabHoliday List` hl on h.parent= hl.name  where h.date =%s and hl.name=%s and hl.docstatus=1""", (self.date_for_exception, default_holiday_list_for_period_with_the_date), as_dict=True)
	
				if not holiday:
					frappe.throw("Invalid holiday. No holiday matching on this date.") 
     
	def on_submit(self):
     
		if self.status != "Approved":
			frappe.throw("Please change the status to 'Approved' for submitting the document.")
     