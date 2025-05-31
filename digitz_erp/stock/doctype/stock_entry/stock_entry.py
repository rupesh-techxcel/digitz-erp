# Copyright (c) 2025,   and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime
from digitz_erp.api.stock_update import (
    recalculate_stock_ledgers,
    update_stock_balance_in_item,
)

class StockEntry(Document):
	
	def on_update(self):
		self.update_material_issue_finished_qty()
		self.update_qty_returned_in_sub_contracting_order()
		self.update_sub_contracting_order_status_from_stock_entry()
  
	def on_trash(self):
		self.update_material_issue_finished_qty(cancelled=True)
		self.update_qty_returned_in_sub_contracting_order()
		self.update_sub_contracting_order_status_from_stock_entry()
     
	def on_submit(self):
		self.do_stock_posting()
  
	def on_cancel(self):		
		self.do_cancel_stock_entry()		
  
	def do_cancel_stock_entry(self):
          
		self.do_stock_posting_on_cancel()
		
		frappe.db.delete("Stock Ledger",
			{"voucher": "Stock Entry",
				"voucher_no":self.name
			})

		self.update_material_issue_finished_qty(cancelled=True)
		self.update_qty_returned_in_sub_contracting_order()
		self.update_sub_contracting_order_status_from_stock_entry()  
		
	def do_stock_posting(self):

		stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher.voucher = 'Stock Entry'
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
      
			print(docitem.item)
			print(docitem.warehouse)
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

				previous_stock_balance_value = 0
    
				if previous_stock_balance:

					new_balance_qty = previous_stock_balance.balance_qty + docitem.qty
					# valuation_rate = previous_stock_balance.valuation_rate
					previous_stock_balance_value = previous_stock_balance.balance_value

				else:

					new_balance_qty = docitem.qty
					
					# valuation_rate = frappe.get_value("Item", docitem.item, ['standard_buying_price'])

				# Valuation rate is not considering in this case.
				new_balance_value = previous_stock_balance_value + (docitem.qty * docitem.rate)

				# if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
				#     frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse})

				change_in_stock_value = new_balance_value + previous_stock_balance_value

				new_stock_ledger = None

				# Allows to post the item only once to the stock ledger.
				if docitem.item not in item_stock_ledger:

					new_stock_ledger = frappe.new_doc("Stock Ledger")
					new_stock_ledger.item = docitem.item
					new_stock_ledger.item_name = docitem.item_name
					new_stock_ledger.warehouse = docitem.warehouse
					new_stock_ledger.posting_date = posting_date_time

					new_stock_ledger.qty_in = docitem.qty
					new_stock_ledger.incoming_rate = docitem.rate
					new_stock_ledger.unit = docitem.unit
					new_stock_ledger.valuation_rate = docitem.rate
					new_stock_ledger.balance_qty = new_balance_qty
					new_stock_ledger.balance_value = new_balance_value
					new_stock_ledger.change_in_stock_value = change_in_stock_value
					new_stock_ledger.voucher = "Stock Entry"
					new_stock_ledger.voucher_no = self.name
					new_stock_ledger.source = "Stock Entry Item"
					new_stock_ledger.source_document_id = docitem.name
					new_stock_ledger.insert()

					sl = frappe.get_doc("Stock Ledger", new_stock_ledger.name)

					item_stock_ledger[docitem.item] = sl.name

				else:
					stock_ledger_name = item_stock_ledger.get(docitem.item)
					stock_ledger = frappe.get_doc('Stock Ledger', stock_ledger_name)

					stock_ledger.qty_in = stock_ledger.qty_in + docitem.qty
					stock_ledger.balance_qty = stock_ledger.balance_qty + docitem.qty
					stock_ledger.balance_value = stock_ledger.balance_qty * docitem.rate
					stock_ledger.change_in_stock_value = stock_ledger.change_in_stock_value + (stock_ledger.balance_qty * stock_ledger.valuation_rate)
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
					new_stock_balance.valuation_rate = docitem.rate

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
   
	def do_stock_posting_on_cancel(self):
     
		print("from do_stock_posting_on_cancel")

        # Insert record to 'Stock Recalculate Voucher' doc
		stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')

		stock_recalc_voucher.voucher = 'Stock Entry'
		stock_recalc_voucher.voucher_no = self.name
		stock_recalc_voucher.voucher_date = self.posting_date
		stock_recalc_voucher.voucher_time = self.posting_time
		stock_recalc_voucher.status = 'Not Started'
		stock_recalc_voucher.source_action = "Cancel"

		posting_date_time =  get_datetime(str(self.posting_date) + " " + str(self.posting_time))
  
		print(posting_date_time)

		more_records = 0

		for docitem in self.items:
      
			print("docitem.item")
			print(docitem.item)
			
			balance_qty = 0
			balance_value = 0
			valuation_rate = 0

			# For cancel delivery note balance qty logic is safe because it only add the qty back to the stock.
			more_record_for_item = frappe.db.count('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
				, 'posting_date':['>', posting_date_time]})

			more_records = more_records + more_record_for_item
   
			print(more_records)

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

	def update_material_issue_finished_qty(self, cancelled=False):
		"""
		Updates the `finished_qty` field in Material Issue Items based on the items in the Stock Entry document.
		Includes the current Stock Entry's quantities only if it is not cancelled.
		"""
		if not self.material_issue:
			frappe.throw("Material Issue is not linked to this Stock Entry.")

		# Initialize a dictionary to track recalculated finished quantities for each Material Issue Item
		recalculated_finished_qty = {}

		# Step 1: Fetch Stock Entry documents linked to the same Material Issue
		linked_stock_entries = frappe.get_all(
			"Stock Entry",
			filters={
				"material_issue": self.material_issue,  # Filter by Material Issue
				"name": ["!=", self.name],  # Exclude the current Stock Entry
				"docstatus": ["in", [0, 1]],  # Only include non-cancelled and submitted entries
			},
			fields=["name"],
		)
		linked_stock_entry_names = [entry["name"] for entry in linked_stock_entries]

		# Step 2: Fetch Stock Entry Items from the linked Stock Entries
		stock_entry_items = frappe.get_all(
			"Stock Entry Item",
			filters={
				"parent": ["in", linked_stock_entry_names],
			},
			fields=["material_issue_item", "qty"],
		)

		# Step 3: Accumulate quantities from valid Stock Entry items
		for item in stock_entry_items:
			if not item["material_issue_item"]:
				continue  # Skip if the item isn't linked to a Material Issue Item

			recalculated_finished_qty[item["material_issue_item"]] = (
				recalculated_finished_qty.get(item["material_issue_item"], 0) + item["qty"]
			)

		# Step 4: Include quantities from the current Stock Entry if not cancelled
		if not cancelled:
			for stock_entry_item in self.items:
				if not stock_entry_item.material_issue_item:
					continue  # Skip if the item isn't linked to a Material Issue Item

				recalculated_finished_qty[stock_entry_item.material_issue_item] = (
					recalculated_finished_qty.get(stock_entry_item.material_issue_item, 0) + stock_entry_item.qty
				)

		# Step 5: Get all Material Issue Items linked to the Material Issue and ensure zero default
		material_issue_items = frappe.get_all(
			"Material Issue Item",
			filters={"parent": self.material_issue},
			fields=["name"],
		)
		for material_issue_item in material_issue_items:
			recalculated_finished_qty.setdefault(material_issue_item["name"], 0)  # Default to zero if not found

		# Step 6: Update the finished_qty field in Material Issue Items
		for material_issue_item, finished_qty in recalculated_finished_qty.items():
			if finished_qty < 0:
				frappe.throw(
					f"Finished quantity cannot be negative for Material Issue Item {material_issue_item}."
				)

			# Update the finished_qty in the Material Issue Item
			frappe.db.set_value(
				"Material Issue Item",
				material_issue_item,
				"qty_finished",
				finished_qty,
			)

		# Commit the changes to the database
		frappe.db.commit()

	def update_qty_returned_in_sub_contracting_order(self):
		"""
		Resets the `qty_returned` field to zero for all items in the Sub Contracting Order,
		and recalculates it based on the `finished_qty` of all Material Issue items linked to the order.

		:param self: The current Stock Entry document.
		"""
		if not self.sub_contracting_order:
			frappe.throw("Sub Contracting Order is required.")

		# Step 1: Fetch all items in the Sub Contracting Order
		sub_contracting_order_items = frappe.get_all(
			"Sub Contracting Order Item",
			filters={"parent": self.sub_contracting_order},
			fields=["name", "qty_issued"]
		)

		# Step 2: Initialize `qty_returned` to zero for all items
		for item in sub_contracting_order_items:
			frappe.db.set_value("Sub Contracting Order Item", item["name"], "qty_returned", 0)

		# Step 3: Fetch all Material Issue documents linked to the Sub Contracting Order
		material_issues = frappe.get_all(
			"Material Issue",
			filters={"sub_contracting_order": self.sub_contracting_order, "docstatus": ["in", [0, 1]]},
			fields=["name"],
		)

		# Step 4: Recalculate `qty_returned` based on Material Issue items
		recalculated_qty_returned = {item["name"]: 0 for item in sub_contracting_order_items}
		for material_issue in material_issues:
			material_issue_doc = frappe.get_doc("Material Issue", material_issue["name"])
			for material_issue_item in material_issue_doc.items:
				if not material_issue_item.sub_contracting_order_item:
					continue  # Skip items not linked to Sub Contracting Order Items

				# Add `finished_qty` to the corresponding Sub Contracting Order Item
				if material_issue_item.sub_contracting_order_item in recalculated_qty_returned:
					recalculated_qty_returned[material_issue_item.sub_contracting_order_item] += material_issue_item.qty_finished

		# Step 5: Update the `qty_returned` field in Sub Contracting Order Items
		for item in sub_contracting_order_items:
			item_name = item["name"]
			updated_qty_returned = recalculated_qty_returned.get(item_name, 0)

			# Update the `qty_returned` field in the database
			frappe.db.set_value("Sub Contracting Order Item", item_name, "qty_returned", updated_qty_returned)

		# Commit changes to the database
		frappe.db.commit()


	
	def update_sub_contracting_order_status_from_stock_entry(self):
		"""
		Updates the status of the linked Sub Contracting Order based on the quantities
		issued and returned in the Sub Contracting Order Items, triggered from a Stock Entry.
		"""
		# Fetch the linked Sub Contracting Order
		subcontracting_order = self.sub_contracting_order

		if not subcontracting_order:
			frappe.throw("Sub Contracting Order is required to update its status.")

		# Fetch the items linked to the Sub Contracting Order
		items = frappe.get_all(
			'Sub Contracting Order Item',
			filters={'parent': subcontracting_order},
			fields=['qty', 'qty_issued', 'qty_returned']
		)

		# Initialize a flag to determine if all items are completed
		all_completed = True
		for item in items:
			# Check if the conditions are met to set the status to 'Completed'
			if item.qty > item.qty_issued or item.qty != item.qty_returned:
				all_completed = False
				break

		# Update the status of the Sub Contracting Order based on the item conditions
		new_status = 'Completed' if all_completed else 'In Process'
		frappe.db.set_value('Sub Contracting Order', subcontracting_order, 'status', new_status)

