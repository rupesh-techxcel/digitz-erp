# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, nowtime


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

	def on_submit(self):
		self.create_stock_ledger_entries()

	def create_stock_ledger_entries(self):
		sales_order = frappe.get_doc("Sales Order", self.sales_order)
		project = frappe.get_doc("Project", self.project)

		# Fetch the warehouse linked to the project
		warehouse = frappe.get_all(
			"Warehouse",
			filters={"project": self.project},
			fields=["name"],
			limit=1
		)
		
		if not warehouse:
			frappe.throw(f"No warehouse found for project {self.project}")
		
		warehouse_name = warehouse[0].name
	
		for progress_item in self.progress_entry_items:
			if progress_item.total_completion == 100:
				# Find the corresponding item in the Sales Order
				so_item = next((item for item in sales_order.items if item.item == progress_item.item), None)
				
				if so_item:
					stock_ledger = frappe.new_doc("Stock Ledger")
					stock_ledger.item = progress_item.item
					stock_ledger.item_name = progress_item.item_name
					stock_ledger.posting_date = nowdate()
					# stock_ledger.posting_time = nowtime()
					stock_ledger.warehouse = warehouse_name
					# stock_ledger.warehouse = sales_order.warehouse
					stock_ledger.qty_in = so_item.qty  # Use the qty from the Sales Order Item
					
					stock_ledger.voucher = ""
					stock_ledger.voucher_no = self.name
					stock_ledger.company = self.company
					
					stock_ledger.insert()
				else:
					frappe.msgprint(f"Item {progress_item.item} not found in Sales Order {self.sales_order}")

	def after_insert(self):
		project = frappe.get_doc("Project", self.project)
		project.append("project_stage_table", {
			"progress_entry": self.name,
		})
		project.save()
		project.reload()