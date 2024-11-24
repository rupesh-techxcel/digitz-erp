# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import money_in_words
from digitz_erp.api.project_api import update_progress_entries_for_project


class ProformaInvoice(Document):

	def before_validate(self):
		self.in_words = money_in_words(self.rounded_total,"AED")

	def on_submit(self):
		
		if not self.client_approved:
			frappe.throw("Client approval pending to submit the Proforma Invoice.")
   
	def on_update(self):		
		update_progress_entries_for_project(self.project)

	def on_trash(self):		
		update_progress_entries_for_project(self.project)
  
	def on_cancel(self):
		update_progress_entries_for_project(self.project)
		
     
		
