# Copyright (c) 2024,   and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.settings_api import add_seconds_to_time
from digitz_erp.api.settings_api import get_gl_narration
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type

class TimesheetEntry(Document):
    
	def Set_Posting_Time_To_Next_Second(self):
		# Add 12 seconds to self.posting_time and update it
		self.posting_time = add_seconds_to_time(str(self.posting_time), seconds=12)
	
	def before_validate(self):
		
		if(self.Voucher_In_The_Same_Time()):

			self.Set_Posting_Time_To_Next_Second()

			if(self.Voucher_In_The_Same_Time()):
				self.Set_Posting_Time_To_Next_Second()

				if(self.Voucher_In_The_Same_Time()):
					self.Set_Posting_Time_To_Next_Second()

					if(self.Voucher_In_The_Same_Time()):
						frappe.throw("Voucher with same time already exists.")
						
	def Voucher_In_The_Same_Time(self):
		possible_invalid = frappe.db.count(
			"Timesheet Entry",
			{
				"posting_date": ["=", self.posting_date],
				"posting_time": ["=", self.posting_time],
			},
		)
		return possible_invalid   
	
	def on_submit(self):
		self.insert_gl_records()
		self.update_project_and_work_order_labour_cost()
  
	  
	def insert_gl_records(self):
		
		remarks = self.get_narration()

		#print("From insert gl records")

		default_company = frappe.db.get_single_value("Global Settings", "default_company")

		default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account', 'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)

		idx = 1
  
		labour_cost = self.labour_cost

		# Inventory account - Credit - Against Cost Of Goods Sold
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Timesheet Entry"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = self.labour_cost_payable_account
		gl_doc.credit_amount = labour_cost
		gl_doc.against_account = self.work_in_progress_account
		gl_doc.is_for_wip = True
		gl_doc.project = self.project
		gl_doc.remarks = remarks
		gl_doc.insert()

		# Cost Of Goods Sold - Debit - Against Inventory
		idx = 2
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Timesheet Entry"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = self.work_in_progress_account
		gl_doc.debit_amount = labour_cost
		gl_doc.against_account = default_accounts.labour_cost_payable_account
		gl_doc.is_for_wip = True
		gl_doc.remarks = remarks
		gl_doc.project = self.project
		gl_doc.insert()
  
	def get_narration(self):
		
		# Assign supplier, invoice_no, and remarks
		
		project = self.project if self.project else ""
				
		# Get the gl_narration which might be empty
		gl_narration = get_gl_narration('Timesheet Entry')  # This could return an empty string

		# Provide a default template if gl_narration is empty
		if not gl_narration:
			gl_narration = "Timesheet Entry for {project}"

		return gl_narration  

	def on_cancel(self):
		self.update_project_and_work_order_labour_cost(cancelled=True)
		delete_gl_postings_for_cancel_doc_type('Timesheet Entry', self.name)

	def update_project_and_work_order_labour_cost(self, cancelled=False):
		"""
		Updates the labour cost for Project and Work Order based on Timesheet Entry Details.

		Steps:
		1. Get labour cost from timesheet entry details (child table) for submitted timesheets,
		excluding the current timesheet.
		2. If 'cancelled' is False, include the current timesheet's labour cost (from its details).
		3. Sum it up and update the respective fields in Project and Work Order.
		"""

		def get_other_timesheets_labour_cost(for_work_order=False):
			"""
			Fetch the labour cost from Timesheet Entry Details (child table) of submitted Timesheets,
			excluding the current Timesheet.
			
			:param for_work_order: Boolean indicating whether to fetch for Work Order or Project.
			:return: Total labour cost from other timesheets.
			"""
			conditions = ["tse.docstatus = 1", "tse.name != %s"]
			values = [self.name]

			if not for_work_order:
				conditions.append("tse.project = %s")
				values.append(self.project)
			else:
				conditions.extend(["tse.project = %s", "tse.work_order = %s"])
				values.extend([self.project, self.work_order])

			condition_str = " AND ".join(conditions)

			query = f"""
				SELECT SUM(ted.labour_cost)
				FROM `tabTimesheet Entry Detail` ted
				JOIN `tabTimesheet Entry` tse ON ted.parent = tse.name
				WHERE {condition_str}
			"""

			total = frappe.db.sql(query, values)[0][0] or 0   
   
			other_sub_contracting_orders = frappe.db.sql("""
				SELECT 
					SUM(scod.gross_amount) as total_gross					
				FROM `tabSub Contracting Order Item` scod
				JOIN `tabSub Contracting Order` sco ON scod.parent = sco.name
				WHERE sco.docstatus = 1
				AND sco.name != %s
				AND sco.project = %s
			""", (self.name, self.project), as_dict=True)[0]
			sub_contracting_labour_total = other_sub_contracting_orders.total_gross or 0
			return total + sub_contracting_labour_total

		def get_current_timesheet_labour_cost():
			"""Get labour cost from the current Timesheet's details (self.time_sheet_entry_details)."""
			if cancelled:
				return 0
			return sum(row.labour_cost for row in self.time_sheet_entry_details)

		def calculate_total_labour_cost(other_labour_cost):
			current_labour_cost = get_current_timesheet_labour_cost()
			return other_labour_cost + current_labour_cost

		# Update Project labour cost
		if self.project:
			other_project_labour_cost = get_other_timesheets_labour_cost(for_work_order=False)
			total_project_labour_cost = calculate_total_labour_cost(other_project_labour_cost)
			frappe.db.set_value("Project", self.project, "labour_cost", total_project_labour_cost)
			frappe.msgprint(f"Updated Project '{self.project}' labour cost to {total_project_labour_cost}.", alert=1)

		# Update Work Order labour cost
		if self.work_order:
			other_work_order_labour_cost = get_other_timesheets_labour_cost(for_work_order=True)
			total_work_order_labour_cost = calculate_total_labour_cost(other_work_order_labour_cost)
			frappe.db.set_value("Work Order", self.work_order, "labour_cost", total_work_order_labour_cost)
			frappe.msgprint(f"Updated Work Order '{self.work_order}' labour cost to {total_work_order_labour_cost}.", alert=1)
