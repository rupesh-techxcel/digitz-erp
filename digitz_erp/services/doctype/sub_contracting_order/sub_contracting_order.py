# Copyright (c) 2025,   and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
class SubContractingOrder(Document):
    
	def validate(self):
     
		# Initialize sets to track unique entries for target_item and source_item
		target_items = set()
		source_items = set()
		
		for item in self.items:
			# Check for duplicates in target_item
			if item.target_item in target_items:
				frappe.throw(
					f"Duplicate Target Item '{item.target_item}' found in the Items table. Please ensure each Target Item is unique."
				)
			target_items.add(item.target_item)
			
			# Check for duplicates in source_item
			if item.source_item in source_items:
				frappe.throw(
					f"Duplicate Source Item '{item.source_item}' found in the Items table. Please ensure each Source Item is unique."
				)
			source_items.add(item.source_item)
   
		self.check_duplicate_sub_contracting_order()
  
	def on_submit(self):
		self.update_project_labour_cost()
  
	def on_cancel(self):
		self.update_project_labour_cost(for_cancel= True)
   
	def check_duplicate_sub_contracting_order(self):
     
		"""
		Check if another active Sub Contracting Order exists for the same Purchase Order.
		Raise an error if a duplicate is found.
		"""
  
		if self.purchase_order:
			# Query for another Sub Contracting Order with the same Purchase Order
			existing_order = frappe.db.get_value(
				"Sub Contracting Order",
				{
					"purchase_order": self.purchase_order,
					"docstatus": ["!=", 2],  # Exclude cancelled orders
					"name": ["!=", self.name],  # Exclude the current document
				},
				"name"
			)
			
			# Raise an error if a duplicate is found
			if existing_order:
				frappe.throw(
					_("A Sub Contracting Order ({0}) already exists for the Purchase Order {1}.")
					.format(existing_order, self.purchase_order)
				)
    
	def update_project_labour_cost(self, for_cancel=False):
		if self.project:
			# Calculate current gross total from self.items if not cancelling
			current_gross_total = 0
			if not for_cancel:
				current_gross_total = sum(row.gross_amount for row in self.items)

			# SQL query to sum labour_cost and gross_amount from Timesheet Entry Detail
			result = frappe.db.sql("""
			SELECT 
			SUM(ted.labour_cost) as total_labour_cost					
			FROM `tabTimesheet Entry Detail` ted
			JOIN `tabTimesheet Entry` tse ON ted.parent = tse.name
			WHERE tse.docstatus = 1				
			AND tse.project = %s
			""", (self.project,), as_dict=True)[0]


			timesheet_labour_cost = result.total_labour_cost or 0
   
			other_sub_contracting_orders = frappe.db.sql("""
				SELECT 
					SUM(scod.gross_amount) as total_gross					
				FROM `tabSub Contracting Order Item` scod
				JOIN `tabSub Contracting Order` sco ON scod.parent = sco.name
				WHERE sco.docstatus = 1
				AND sco.name != %s
				AND sco.project = %s
			""", (self.name, self.project), as_dict=True)[0]
			
			other_order_gross = other_sub_contracting_orders.total_gross or 0

			total_project_labour_cost = current_gross_total + timesheet_labour_cost + other_order_gross

			frappe.db.set_value("Project", self.project, "labour_cost", total_project_labour_cost)
   
			frappe.msgprint(f"Labour cost has been successfully updated for the project: {self.project}", alert=1)

