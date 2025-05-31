# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Employee(Document):
    
	def before_validate(self):
		self.employee_code = self.name

	def on_update(self):
		self.employee_code = self.name

