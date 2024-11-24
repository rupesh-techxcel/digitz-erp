# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, nowtime
from frappe.utils import money_in_words
from digitz_erp.api.project_api import update_progress_entries_for_project

class ProgressEntry(Document):
    
	def before_validate(self):
		self.in_words = money_in_words(self.rounded_total,"AED")

	def validate(self):
		if(self.previous_progress_entry == self.name):
			frappe.throw("Choose a valid Progress Entry !")

	def after_insert(self):
		project = frappe.get_doc("Project", self.project)
		project.append("project_stage_table", {
			"progress_entry": self.name,
			"posting_date": self.posting_date,
			"percentage_of_completion":self.total_completion_percentage

			# "child_table_int_field": 0,
		})  

		project.save()

		update_progress_entries_for_project()
		project.reload()
  
	def on_trash(self):
			
		"""
		Override the on_trash event to remove the progress entry from the associated project first.
		"""
		if self.project:
			# Fetch the linked project
			project_doc = frappe.get_doc('Project', self.project)

			# Remove the progress entry reference from the child table
			project_doc.project_stage_table = [
				stage for stage in project_doc.project_stage_table if stage.progress_entry != self.name
			]

			# Save the project to reflect the changes
			project_doc.save(ignore_permissions=True)

		
