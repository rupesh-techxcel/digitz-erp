# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.accounts_api import calculate_utilization
from digitz_erp.api.accounts_api import get_balance_budget_value
from frappe.utils import flt

class MaterialRequest(Document):
    
	def validate(self):
		
		self.validate_budget_for_items()
	
	def validate_budget_for_items(self):
		"""
		Validate budget for each item in a Material Request.
		"""
		for item in self.items:
			budget_data = get_balance_budget_value(
				reference_type="Item",
				reference_value=item.item,
				doc_type="Material Request",
				doc_name=self.name,
				transaction_date=self.posting_date,
				company=self.company,
				project=self.project,
				cost_center=self.default_cost_center
			)
			
			if budget_data and not budget_data.get("no_budget"):
				details = budget_data.get("details", {})
				budget_amount = flt(details.get("Budget Amount", 0))
				used_amount = flt(details.get("Used Amount", 0))
				available_balance = flt(details.get("Available Balance", 0))
				ref_type = details.get("Reference Type")
				total_map = 0

				for row in self.items:
					qty = flt(row.qty)
					valuation_rate = flt(row.valuation_rate)
					
					if ref_type == "Item" and row.item == item.item:
						total_map += qty * valuation_rate
					elif ref_type == "Item Group" and row.item_group == item.item_group:
						total_map += qty * valuation_rate
				
				used_amount += total_map
				
				if budget_amount < used_amount:
					frappe.throw(f"Exceeding the allocated budget for the item {item.item}!")

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
   
	
	
