# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProgressEntry(Document):
	def validate(self):
		if(self.previous_progress_entry == self.name):
			frappe.throw("Choose a valid Progress Entry !")


	def after_insert(self):
		project = frappe.get_doc("Project", self.project)
		project.append("project_stage_table", {
			"progress_entry": self.name,
			# "child_table_int_field": 0,
		})

		project.save()
		project.reload()
