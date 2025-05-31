# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SalaryGroup(Document):

	def before_validate(self):
     
		self.ensure_default()

	def ensure_default(self):
     
		if self.is_new() and not frappe.db.exists('Salary Group'):
			# No records exist, set is_default to True for the first record
			self.is_default = 1  
		else:
			if self.is_default:
				# If this record is set as default, unset other defaults
				frappe.db.sql("""
					UPDATE `tabSalary Group`
					SET is_default = 0
					WHERE name != %s
				""", (self.name,))	

				frappe.msgprint("This Salary Group has been set as the default.", alert=True)

	def validate(self):
		self.ensure_at_least_one_default()

	def ensure_at_least_one_default(self):
     
			# Check if there are any records with is_default set to True, excluding the current record
			default_record = frappe.db.exists('Salary Group', {'is_default': 1, 'name': ['!=', self.name]})
			
			# If no default record exists and the current record is not set as default, throw an error
			if not default_record and not self.is_default:
				frappe.throw('There must be at least one Salary Group marked as default.')

    