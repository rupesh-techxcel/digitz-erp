# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MaterialRequest(Document):
    
	def validate(self):
		self.validate_item_budgets()
		
	def validate_item_budgets(self):
		"""
		Validate Purchase Order items against the budget values and utilized amounts.

		This method is intended to be called during the validate event of the Purchase Order.
		"""
		for item in self.items:
			# Fetch budget details for the item
			budget_item = frappe.db.get_value(
				"Budget Item",
				{"reference_type": "Item", "reference_value": item.item},
				["parent", "budget_amount"],
				as_dict=True
			)

			if not budget_item:
				# Skip validation if no budget exists for the item
				continue

			# Get the parent budget details
			budget = frappe.get_doc("Budget", budget_item["parent"])

			# Fetch utilized amount
			utilized_amount = calculate_utilization(
				budget_against=budget.budget_against,
				item_budget_against="Purchase",
				budget_against_value=getattr(budget, budget.budget_against.lower()),
				reference_type="Item",
				reference_value=item.item,
				from_date=budget.from_date,
				to_date=budget.to_date,
			)

			# Calculate total utilized
			total_utilized = utilized_amount + item.gross_amount

			# Check if total utilized exceeds budget amount
			if total_utilized > budget_item["budget_amount"]:
				frappe.throw(
					f"Item {item.item} exceeds its budget limit. "
					f"Budget Amount: {budget_item['budget_amount']}, "
					f"Utilized: {utilized_amount}, "
					f"Gross Amount in Purchase Order: {item.gross_amount}, "
					f"Total Utilized: {total_utilized}."
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
