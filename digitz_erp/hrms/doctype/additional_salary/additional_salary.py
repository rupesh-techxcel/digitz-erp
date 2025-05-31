# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AdditionalSalary(Document):
    
	def before_validate(self):
     
		# Assign pending status when the user adding the additional salary. And while creating the salary slp the status will be assigned directly in the db to "Processed"
		self.status = "Pending"

		if self.valuation_type == "Qty and Rate":  			
			self.amount = self.qty * self.rate
