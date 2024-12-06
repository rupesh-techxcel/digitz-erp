# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MaterialRequest(Document):
    
	def validate(self):
		self.validate_items_budget()
		
	def validate_items_budget(self):
		for item in self.items:
			# Check if Material Request validation is enabled in the budget
			budget_settings = frappe.get_all(
				"Budget",
				filters={
					"company": self.company,
					"project": getattr(self, "project", None),
					"cost_center": self.cost_center
				},
				fields=["name", "material_request"]
			)

			if not budget_settings:
				continue

			budget_name = frappe.get_value(
				"Budget",
				filters={
					"company": self.company,
					"project": getattr(self, "project", None),
					"cost_center": self.cost_center
				},
				fieldname="name"
			)

			if not budget_name:
				continue

            # Fetch the material_request checkbox value
            budget_doc = frappe.get_doc("Budget", budget_name)
            if not budget_doc.purchase_request:
                continue  # Skip validation if the checkbox is not enabled

			# Check budget utilization
			budget_utilization = fetch_budget_utilization(
				reference_type="Item",
				reference_value=item.item_code,
				transaction_date=self.transaction_date or self.posting_date,
				company=self.company,
				project=getattr(self, "project", None),
				cost_center=self.cost_center
			)

			# Validate budget utilization
			if budget_utilization["no_budget"]:
				frappe.throw(
					_(f"No budget exists for the item {item.item_code} in the current context.")
				)

			utilized = budget_utilization["utilized"]
			budget = budget_utilization["budget"]

			if utilized > budget:
				frappe.throw(
					_(f"The item {item.item_code} exceeds its allocated budget. "
						f"Utilized: {utilized}, Budget: {budget}")
				)

	def before_submit(self):
		if not self.approved:
			frappe.throw("You cannot submit this document unless it is approved.")

		any_approved_qty = False
		for item in self.items:  # Replace 'items' with the actual child table field name
			if item.qty_approved > 0:  # Replace 'approved_qty' with the actual field name in the child table
				any_approved_qty = True
				break

		if not any_approved_qty:
			frappe.throw("No items have approved quantities to allow the document to be submitted.")
