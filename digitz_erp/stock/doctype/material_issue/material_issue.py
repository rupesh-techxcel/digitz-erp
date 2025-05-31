# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt
import frappe
from frappe.utils import get_datetime
from datetime import datetime
from frappe.model.document import Document
from frappe.utils.data import now
from datetime import datetime, timedelta
from digitz_erp.api.stock_update import (
    recalculate_stock_ledgers,
    update_stock_balance_in_item,
)
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type
from frappe import throw, _
from digitz_erp.api.settings_api import add_seconds_to_time
from digitz_erp.api.settings_api import get_gl_narration
from digitz_erp.api.items_api import get_item_valuation_rate

class MaterialIssue(Document):
    
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
      
		for row in self.items:  # Replace 'child_table_fieldname' with your actual child table fieldname
			
			 if row.item and (not row.rate or row.rate == 0):
						
					# Call the existing Python method directly
					valuation_rate = get_item_valuation_rate(
						item=row.item,
						posting_date=self.posting_date,
						posting_time=self.posting_time
					)
				
					# Update the rate if a valuation rate is returned
					if valuation_rate:
						row.rate = valuation_rate
						
	def Voucher_In_The_Same_Time(self):
		possible_invalid = frappe.db.count(
			"Material Issue",
			{
				"posting_date": ["=", self.posting_date],
				"posting_time": ["=", self.posting_time],
			},
		)
		return possible_invalid   
		
	def validate(self):
		self.validate_items()

	def validate_items(self):
		items = set()  # Initialize an empty set to keep track of unique combinations

		for item in self.items:
			# Create a unique identifier by concatenating item, warehouse, and project
			unique_id = (
				f"{item.item}-{item.warehouse}-{item.project}"
			)

			if unique_id in items:
				frappe.throw(
					_("Item {0} from {1} to {2} is already added in the list").format(
						item.item, item.warehouse, item.project
					)
				)
				
			items.add(unique_id)  # Add the unique identifier to the set for tracking
   
			if item.rate == 0:
				frappe.throw(f"Rate cannot be zero in the item {item.item}")
   
		self.validate_item()
   
	def validate_item(self):

        #print("DN validate item")

		posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))

		default_company = frappe.db.get_single_value("Global Settings", "default_company")

		company_info = frappe.get_value("Company",default_company,['allow_negative_stock'], as_dict = True)

		allow_negative_stock = company_info.allow_negative_stock

		if not allow_negative_stock:
			allow_negative_stock = False

		if allow_negative_stock == False:
			for docitem in self.items:
				# previous_stocks = frappe.db.get_value('Stock Ledger', {'item':docitem.item,'warehouse': docitem.warehouse , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],order_by='posting_date desc', as_dict=True)

				previous_stock_balance = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
				, 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
				order_by='posting_date desc', as_dict=True)

				if(not previous_stock_balance):
					frappe.throw("No stock exists for" + docitem.item )

				if(previous_stock_balance.balance_qty< docitem.qty_in_base_unit):
					frappe.throw("Sufficiant qty does not exists for the item " + docitem.item + " required Qty= " + str(docitem.qty_in_base_unit) +
					" " + docitem.base_unit + " and available Qty=" + str(previous_stock_balance.balance_qty) + " " + docitem.base_unit )

	def on_update(self):
		if self.purpose == "Project Consumption":
			self.update_project_and_work_order_material_cost()
		elif self.purpose == "Sub Contracting":
			self.update_sub_contracting_order_items()
			self.update_sub_contracting_order_status()
   
	def on_trash(self):
		if self.purpose == "Project Consumption":
			self.update_project_and_work_order_material_cost(cancelled=True)
   
		elif self.purpose == "Sub Contracting":
			self.update_sub_contracting_order_items(cancelled=True)
			self.update_sub_contracting_order_status()        
  
	def on_cancel(self):
     
		self.do_cancel_material_issue()

		if self.purpose == "Project Consumption":
			self.update_project_and_work_order_material_cost(cancelled=True)
   
		elif self.purpose == "Sub Contracting":
			self.update_sub_contracting_order_items(cancelled=True)
			self.update_sub_contracting_order_status()
			
		
	def do_cancel_material_issue(self):

		self.do_stock_posting_on_cancel()

		frappe.db.delete("Stock Ledger",
			{"voucher": "Material Issue",
				"voucher_no":self.name
			})

		delete_gl_postings_for_cancel_doc_type('Material Issue', self.name)
  
	def get_narration(self):
		
		# Assign supplier, invoice_no, and remarks		
		project = self.project if self.project else ""
				
		# Get the gl_narration which might be empty
		gl_narration = get_gl_narration('Material Issue')  # This could return an empty string

		# Provide a default template if gl_narration is empty
		if not gl_narration:
			gl_narration = "Material Issue  Note for {project}"

		return gl_narration  

	def do_stock_posting_on_cancel(self):

        # Insert record to 'Stock Recalculate Voucher' doc
		stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')

		stock_recalc_voucher.voucher = 'Material Issue'
		stock_recalc_voucher.voucher_no = self.name
		stock_recalc_voucher.voucher_date = self.posting_date
		stock_recalc_voucher.voucher_time = self.posting_time
		stock_recalc_voucher.status = 'Not Started'
		stock_recalc_voucher.source_action = "Cancel"

		posting_date_time =  get_datetime(str(self.posting_date) + " " + str(self.posting_time))

		more_records = 0

		for docitem in self.items:
      
			balance_qty = 0
			balance_value = 0
			valuation_rate = 0

			# For cancel delivery note balance qty logic is safe because it only add the qty back to the stock.
			more_record_for_item = frappe.db.count('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
				, 'posting_date':['>', posting_date_time]})

			more_records = more_records + more_record_for_item

			previous_stock_ledger_name = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
				, 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)

			if(more_record_for_item == 0):

				if(previous_stock_ledger_name):
					previous_stock_ledger = frappe.get_doc('Stock Ledger',previous_stock_ledger_name)
					balance_qty = previous_stock_ledger.balance_qty
					balance_value = previous_stock_ledger.balance_value
					valuation_rate = previous_stock_ledger.valuation_rate

				if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
					frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse} )

				unit = frappe.get_value("Item", docitem.item,['base_unit'])

				new_stock_balance = frappe.new_doc('Stock Balance')
				new_stock_balance.item = docitem.item
				new_stock_balance.item_name = docitem.item_name
				new_stock_balance.unit = unit
				new_stock_balance.warehouse = docitem.warehouse
				new_stock_balance.stock_qty = balance_qty
				new_stock_balance.stock_value = balance_value
				new_stock_balance.valuation_rate = valuation_rate

				new_stock_balance.insert()
				update_stock_balance_in_item(docitem.item)


			else:
				if previous_stock_ledger_name:
				# Previous stock ledger assigned to base stock ledger
					stock_recalc_voucher.append('records',{'item': docitem.item,
															'warehouse': docitem.warehouse,
															'base_stock_ledger': previous_stock_ledger_name
															})
				else:
					stock_recalc_voucher.append('records',{'item': docitem.item,
															'warehouse': docitem.warehouse,
															'base_stock_ledger': "No Previous Ledger"
															})

		if more_records:            
			stock_recalc_voucher.insert()
			recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)

	def on_submit(self):        
		self.do_postings_on_submit()

	def do_postings_on_submit(self):
		self.do_stock_posting()
		self.insert_gl_records()
  
	def insert_gl_records(self):
		
		remarks = self.get_narration()

		#print("From insert gl records")

		default_company = frappe.db.get_single_value("Global Settings", "default_company")

		default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account', 'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)

		idx = 1
  
		material_cost = self.net_total

		# Inventory account - Credit - Against Cost Of Goods Sold
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Material Issue"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.default_inventory_account
		gl_doc.credit_amount = material_cost
		gl_doc.against_account = self.work_in_progress_account
		gl_doc.is_for_wip = True
		gl_doc.project = self.project
		gl_doc.remarks = remarks
		gl_doc.insert()

		# Cost Of Goods Sold - Debit - Against Inventory
		idx = 2
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Material Issue"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = self.work_in_progress_account
		gl_doc.debit_amount = material_cost
		gl_doc.against_account = default_accounts.default_inventory_account
		gl_doc.is_for_wip = True
		gl_doc.remarks = remarks
		gl_doc.project = self.project
		gl_doc.insert()

	def do_stock_posting(self):

		stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher.voucher = 'Material Issue'
		stock_recalc_voucher.voucher_no = self.name
		stock_recalc_voucher.voucher_date = self.posting_date
		stock_recalc_voucher.voucher_time = self.posting_time
		stock_recalc_voucher.status = 'Not Started'
		stock_recalc_voucher.source_action = "Insert"

		cost_of_goods_sold = 0

		more_records = 0

		# Create a dictionary for handling duplicate items. In stock ledger posting it is expected to have only one stock ledger per item per voucher.
		item_stock_ledger = {}

		for docitem in self.items:
			maintain_stock = frappe.db.get_value('Item', docitem.item , 'maintain_stock')
			#print('MAINTAIN STOCK :', maintain_stock)
			if(maintain_stock == 1):

				posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))

				# Check for more records after this date time exists. This is mainly for deciding whether stock balance needs to update
				# in this flow itself. If more records, exists stock balance will be udpated lateer
				more_records_count_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
					'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})

				more_records = more_records + more_records_count_for_item

				# Check available qty
				previous_stock_balance = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
				, 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
				order_by='posting_date desc', as_dict=True)
    
				print("docitem.item")
				print(docitem.item)
				print()
				print("previous_stock_balance")
				print(previous_stock_balance)

				previous_stock_balance_value = 0
    
				if previous_stock_balance:

					new_balance_qty = previous_stock_balance.balance_qty - docitem.qty_in_base_unit
					valuation_rate = previous_stock_balance.valuation_rate
					previous_stock_balance_value = previous_stock_balance.balance_value

				else:

					new_balance_qty = 0 - docitem.qty_in_base_unit
					# Here valuation rate is manually inputing if it is not found in the above scenario
					valuation_rate = docitem.rate
					# valuation_rate = frappe.get_value("Item", docitem.item, ['standard_buying_price'])

				new_balance_value = previous_stock_balance_value - (docitem.qty_in_base_unit * valuation_rate)

				# if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
				#     frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse})

				change_in_stock_value = new_balance_value - previous_stock_balance_value

				new_stock_ledger = None

				# Allows to post the item only once to the stock ledger.
				if docitem.item not in item_stock_ledger:

					new_stock_ledger = frappe.new_doc("Stock Ledger")
					new_stock_ledger.item = docitem.item
					new_stock_ledger.item_name = docitem.item_name
					new_stock_ledger.warehouse = docitem.warehouse or self.warehouse
					new_stock_ledger.posting_date = posting_date_time

					new_stock_ledger.qty_out = docitem.qty_in_base_unit
					new_stock_ledger.outgoing_rate = docitem.rate_in_base_unit
					new_stock_ledger.unit = docitem.base_unit
					new_stock_ledger.valuation_rate = valuation_rate
					new_stock_ledger.balance_qty = new_balance_qty
					new_stock_ledger.balance_value = new_balance_value
					new_stock_ledger.change_in_stock_value = change_in_stock_value
					new_stock_ledger.voucher = "Material Issue"
					new_stock_ledger.voucher_no = self.name
					new_stock_ledger.source = "Material Issue Item"
					new_stock_ledger.source_document_id = docitem.name
					new_stock_ledger.insert()

					sl = frappe.get_doc("Stock Ledger", new_stock_ledger.name)

					item_stock_ledger[docitem.item] = sl.name

				else:
					stock_ledger_name = item_stock_ledger.get(docitem.item)
					stock_ledger = frappe.get_doc('Stock Ledger', stock_ledger_name)

					stock_ledger.qty_out = stock_ledger.qty_out + docitem.qty_in_base_unit
					stock_ledger.balance_qty = stock_ledger.balance_qty - docitem.qty_in_base_unit
					stock_ledger.balance_value = stock_ledger.balance_qty * stock_ledger.valuation_rate
					stock_ledger.change_in_stock_value = stock_ledger.change_in_stock_value - (stock_ledger.balance_qty * stock_ledger.valuation_rate)
					new_balance_qty = stock_ledger.balance_qty
					stock_ledger.save()

				# If no more records for the item, update balances. otherwise it updates in the flow
				if more_records_count_for_item==0:

					if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
						frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse} )

					unit = frappe.get_value("Item", docitem.item,['base_unit'])

					new_stock_balance = frappe.new_doc('Stock Balance')
					new_stock_balance.item = docitem.item
					new_stock_balance.unit = unit
					new_stock_balance.warehouse = docitem.warehouse
					new_stock_balance.stock_qty = new_balance_qty
					new_stock_balance.stock_value = new_balance_value
					new_stock_balance.valuation_rate = valuation_rate

					new_stock_balance.insert()

					# item_name = frappe.get_value("Item", docitem.item,['item_name'])
					# #print("item_name")
					# #print(item_name)
					update_stock_balance_in_item(docitem.item)
				else:
					stock_recalc_voucher.append('records',{'item': docitem.item,
															'item_name': docitem.item_name,
																'warehouse': docitem.warehouse,
																'base_stock_ledger': new_stock_ledger.name
																})

		if(more_records>0):

			# update_posting_status(self.doctype,self.name, 'stock_recalc_required', True)

			stock_recalc_voucher.insert()
			recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)

			# update_posting_status(self.doctype, self.name, 'stock_recalc_time')
   
	def update_project_and_work_order_material_cost(self, cancelled=False):
		"""
		Updates the material cost for Project and Work Order based on Material Issue entries.

		Steps:
		1. Get material cost from other Material Issue entries for the same project or work order, excluding the current document.
		2. If 'cancelled' is False, include the current document's material cost.
		3. Sum it up and update the respective fields.
		"""

		def get_other_material_issues_cost(for_work_order=False):
			"""
			Fetch the material cost from other Material Issue entries excluding the current document.

			:param for_work_order: Boolean indicating whether to fetch for Work Order (True) or Project (False).
			:return: Total material cost from other Material Issue entries.
			"""
			base_query = """
				SELECT SUM(net_total)
				FROM `tabMaterial Issue`
				WHERE docstatus < 2 
				AND name != %(current_name)s
			"""

			conditions = []
			params = {"current_name": self.name}

			# Add conditions based on the context (project or work order)
			if self.project:
				conditions.append("project = %(project)s")
				params["project"] = self.project

			if for_work_order and self.work_order:
				conditions.append("work_order = %(work_order)s")
				params["work_order"] = self.work_order

			# Combine the query
			if conditions:
				base_query += " AND " + " AND ".join(conditions)

			# Execute the query
			total_cost = frappe.db.sql(base_query, params)
			return total_cost[0][0] if total_cost and total_cost[0][0] else 0


		def calculate_total_material_cost(other_material_cost):
			"""Calculate total material cost by summing other entries and current entry if not cancelled."""
   
			if self.purpose == "Project Consumption":
				current_material_cost = self.net_total if not cancelled else 0
				return other_material_cost + current_material_cost

		# Update material cost for Project
		if self.project:
			# Step 1: Get material cost from other Material Issue entries for the same project
			other_project_material_cost = get_other_material_issues_cost(for_work_order=False)


			# Step 2 & 3: Calculate total project material cost
			total_project_material_cost = calculate_total_material_cost(other_project_material_cost)

			# Update the project's material cost field
			frappe.db.set_value("Project", self.project, "material_cost", total_project_material_cost)
			frappe.msgprint(f"Updated Project '{self.project}' material cost to {total_project_material_cost}.", alert=1)

		# Update material cost for Work Order
		if self.work_order:
			# Step 1: Get material cost from other Material Issue entries for the same work order
			other_work_order_material_cost = get_other_material_issues_cost(for_work_order=True)

			# Step 2 & 3: Calculate total work order material cost
			total_work_order_material_cost = calculate_total_material_cost(other_work_order_material_cost)

			# Update the work order's material cost field
			frappe.db.set_value("Work Order", self.work_order, "material_cost", total_work_order_material_cost)
			frappe.msgprint(f"Updated Work Order '{self.work_order}' material cost to {total_work_order_material_cost}.", alert=1)

	def update_sub_contracting_order_items(self, cancelled=False):
		# Fetch the Sub Contracting Order from the current document
		sub_contracting_order = self.sub_contracting_order

		if not sub_contracting_order:
			frappe.throw(_("Sub Contracting Order is not available in the Material Issue document."))

		# Fetch all items in the Sub Contracting Order
		sub_contracting_items = frappe.get_all(
			"Sub Contracting Order Item",
			filters={"parent": sub_contracting_order},
			fields=["name", "source_item", "qty"]
		)

		# Create a mapping for quick lookup of Sub Contracting Order Items
		item_map = {item["name"]: item for item in sub_contracting_items}

		# Initialize a dictionary to track recalculated issued quantities for each Sub Contracting Order Item
		recalculated_quantities = {item["name"]: 0 for item in sub_contracting_items}

		# Fetch all Material Issue documents linked to this Sub Contracting Order except the current document
		material_issues = frappe.get_all(
			"Material Issue",
			filters={"sub_contracting_order": sub_contracting_order, "docstatus": ["in", [0, 1]], "name": ["!=", self.name]},
			fields=["name"]
		)

		# Iterate through all Material Issue documents and their items to recalculate quantities
		for material_issue in material_issues:
			material_issue_doc = frappe.get_doc("Material Issue", material_issue["name"])
			for material_issue_item in material_issue_doc.items:
				if material_issue_item.sub_contracting_order_item in recalculated_quantities:
					recalculated_quantities[material_issue_item.sub_contracting_order_item] += material_issue_item.qty

		# Include the current document's quantities unless cancelled is True
		if not cancelled:
			for current_item in self.items:
				if current_item.sub_contracting_order_item in recalculated_quantities:
					recalculated_quantities[current_item.sub_contracting_order_item] += current_item.qty

		# Validate and update the recalculated quantities in Sub Contracting Order Items
		for sub_order_item_name, total_issued_qty in recalculated_quantities.items():
			sub_order_item = item_map[sub_order_item_name]

			# Validate if the recalculated issued quantity exceeds the available quantity
			if total_issued_qty > sub_order_item["qty"]:
				frappe.throw(
					_(
						"Cannot issue quantity for item {0} as it exceeds the remaining available quantity in the Sub Contracting Order Item. Available: {1}, Calculated Issue: {2}"
					).format(
						sub_order_item["source_item"],
						sub_order_item["qty"] - total_issued_qty,
						total_issued_qty
					)
				)

			# Update the qty_issued and issued_date in the Sub Contracting Order Item
			frappe.db.set_value(
				"Sub Contracting Order Item",
				sub_order_item_name,
				{
					"qty_issued": total_issued_qty,
					"issued_date": self.posting_date if not cancelled else None
				}
			)

		# Commit the changes
		frappe.db.commit()


	# This method supposed to call only after the child table updation with update_sub_contracting_order_items method
	def update_sub_contracting_order_status(self):
		# Fetch the linked Sub Contracting Order
		subcontracting_order = self.sub_contracting_order
		
		# Check the items linked to the Sub Contracting Order
		items = frappe.get_all('Sub Contracting Order Item', 
								filters={'parent': subcontracting_order}, 
								fields=['qty', 'qty_issued', 'qty_returned'])

		all_completed = True
		for item in items:
			# Check if the conditions are met to set the status to 'Completed'
			if item.qty > item.qty_issued and item.qty != item.qty_returned:
				all_completed = False
				break

		# Update the status of the Sub Contracting Order based on the item conditions
		if all_completed:
			frappe.db.set_value('Sub Contracting Order', subcontracting_order, 'status', 'Completed')
		else:
			frappe.db.set_value('Sub Contracting Order', subcontracting_order, 'status', 'In Process')