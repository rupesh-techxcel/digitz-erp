# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MaterialRequest(Document):

	def before_submit(self):
		if not self.approved:
			frappe.throw("You cannot submit this document unless it is approved.")

		any_approved_qty = False
		for item in self.items:  # Replace 'items' with the actual child table field name
			if item.approved_quantity > 0:  # Replace 'approved_qty' with the actual field name in the child table
				any_approved_qty = True
				break

		if not any_approved_qty:
			frappe.throw("No items have approved quantities to allow the document to be submitted.")
