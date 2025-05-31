# Copyright (c) 2024,   and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class BOQExecution(Document):
    
	def on_trash(self):
		self.update_boq_while_deleting()		
		
	def on_cancel(self):
		# Update the correspoding boq staus 
		self.update_boq_while_deleting()		

	def update_boq_while_deleting(self):
		
		if self.boq:
			boq = frappe.get_doc("BOQ",self.boq)
			boq.execution_status = "Not Started"
			boq.save()
 
 
 
    
    
	
