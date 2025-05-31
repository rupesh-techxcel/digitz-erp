# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import calendar
from frappe.utils import getdate

class PayrollEntry(Document):
	
	def before_validate(self):
		
		date_obj = getdate(self.start_date)
		month_name = calendar.month_name[date_obj.month]
		self.payroll_entry_name = f"Payroll entry for the month of {month_name}"
  
		self.check_for_existing_draft()

	def check_for_existing_draft(self):
		# Check for existing drafts
		existing_drafts = frappe.get_all(
			'Payroll Entry',
			filters={
				'docstatus': 0,  # 0 indicates a draft document
				'name': ['!=', self.name]  # Exclude the current document
			}
		)

		if existing_drafts:
			frappe.throw(f'Please submit the previous payroll entry {existing_drafts[0]["name"]} before submitting this payroll entry.')


		
