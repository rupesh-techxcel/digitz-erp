# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Task(Document):
	
	def before_validate(self):
 
		if not self.task_description:
			self.task_description = self.task_name
