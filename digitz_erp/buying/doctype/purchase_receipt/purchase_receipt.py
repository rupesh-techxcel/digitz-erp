# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now
from frappe.model.document import Document
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_stock_balance_in_item
from digitz_erp.api.purchase_order_api import check_and_update_purchase_order_status
from frappe.model.mapper import *
from digitz_erp.api.item_price_api import update_item_price,update_supplier_item_price
from digitz_erp.api.settings_api import get_default_currency, get_gl_narration
from digitz_erp.api.purchase_invoice_api import check_balance_qty_to_return_for_purchase_invoice
from digitz_erp.api.document_posting_status_api import init_document_posting_status, update_posting_status
from datetime import datetime,timedelta
from frappe.model.mapper import get_mapped_doc
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type
from digitz_erp.api.bank_reconciliation_api import create_bank_reconciliation, cancel_bank_reconciliation
from frappe import throw, _
from frappe.utils import money_in_words
from digitz_erp.api.settings_api import add_seconds_to_time
from digitz_erp.api.accounts_api import calculate_utilization

class PurchaseReceipt(Document):
    
	def on_update(self):
		
		if self.purchase_order:
			self.update_purchase_order_quantities_on_update()			
		
	def on_cancel(self):
     
		self.cancel_purchase()

		if self.purchase_order:
			#print("Calling update po qties b4 cancel or delete")
			self.update_purchase_order_quantities_on_update(forDeleteOrCancel=True)
	
		self.update_project_purchase_amount(cancel=True)
	
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
    
	def on_submit(self):
		self.do_postings_on_submit()	
		self.update_project_purchase_amount()
  
	def do_postings_on_submit(self):
		self.do_stock_posting()    
		self.insert_gl_records()

	def on_trash(self):		
		if self.purchase_order:
			self.update_purchase_order_quantities_on_update(forDeleteOrCancel=True)

	def update_purchase_order_quantities_on_update(self, forDeleteOrCancel=False):

		po_reference_any = False

		for item in self.items:
			if not item.po_item_reference:
				continue
			else:
				# Get total purchase invoice qty for the mr_item_reference other than in the current purchase invoice.
				total_purchased_qty_not_in_this_pr = frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_used_qty from `tabPurchase Receipt Item` pinvi inner join `tabPurchase Receipt` pinv on pinvi.parent= pinv.name WHERE pinvi.po_item_reference=%s AND pinv.name !=%s and pinv.docstatus<2""",(item.po_item_reference, self.name))[0][0]
    
				po_item = frappe.get_doc("Purchase Order Item", item.po_item_reference)

				# Get Total returned quantity for the po_item, since there can be multiple purchase invoice line items for the same po_item_reference and which could be returned from the purchase invoices as well.

				total_qty_purchased = (total_purchased_qty_not_in_this_pr if total_purchased_qty_not_in_this_pr else 0) 

				po_item.qty_purchased_in_base_unit = total_qty_purchased + (item.qty_in_base_unit if not forDeleteOrCancel else 0)

				po_item.save()
				po_reference_any = True

		if(po_reference_any):
			frappe.msgprint("Purchased Qty of items in the corresponding material request updated successfully", indicator= "green", alert= True)
   
	def do_stock_posting(self):
     
		stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher.voucher = 'Purchase Receipt'
		stock_recalc_voucher.voucher_no = self.name
		stock_recalc_voucher.voucher_date = self.posting_date
		stock_recalc_voucher.voucher_time = self.posting_time
		stock_recalc_voucher.status = 'Not Started'
		stock_recalc_voucher.source_action = "Insert"

		more_records = 0
		posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))

		# Create a dictionary for handling duplicate items. In stock ledger posting it is expected to have only one stock ledger per item per voucher.
		item_stock_ledger = {}

		for docitem in self.items:
			maintain_stock, item_type, asset_category = frappe.db.get_value('Item',
			docitem.item, ['maintain_stock', 'item_type', 'asset_category'])

			if item_type=="Fixed Asset":
				self.do_asset_posting(docitem, asset_category=asset_category)				
				continue
		
			if(maintain_stock == 1):

				# Check for more records after this date time exists. This is mainly for deciding whether stock balance needs to update
				# in this flow itself. If more records, exists stock balance will be udpated lateer
				more_records_count_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
					'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})

				more_records = more_records + more_records_count_for_item

				new_balance_qty = docitem.qty_in_base_unit

				# Default valuation rate
				valuation_rate = docitem.rate_in_base_unit

				# Default balance value calculating withe the current row only
				new_balance_value = new_balance_qty * valuation_rate

				# Assigned current stock value to use if previous values not exist
				change_in_stock_value = new_balance_value

				# posting_date<= consider because to take the dates with in the same minute
				# dbCount = frappe.db.count('Stock Ledger',{'item_code': ['=', docitem.item_code],'warehouse':['=', docitem.warehouse], 'posting_date':['<=', posting_date_time]})
				dbCount = frappe.db.count('Stock Ledger',{'item': ['=', docitem.item],'warehouse':['=', docitem.warehouse],
													'posting_date': ['<', posting_date_time]})

				if(dbCount>0):

					# Find out the balance value and valuation rate. Here recalculates the total balance value and valuation rate
					# from the balance qty in the existing rows x actual incoming rate

					last_stock_ledger = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse],
															'posting_date':['<', posting_date_time]},
												['balance_qty', 'balance_value', 'valuation_rate'],order_by='posting_date desc', as_dict=True)

					new_balance_qty = new_balance_qty + last_stock_ledger.balance_qty

					new_balance_value = new_balance_value + (last_stock_ledger.balance_value)

					#print("new_balance_qty")
					#print(new_balance_qty)

					#print("new_balance_value")
					#print(new_balance_value)

					if new_balance_qty!=0:
						valuation_rate = new_balance_value/new_balance_qty

					change_in_stock_value = new_balance_value - last_stock_ledger.balance_value

				if docitem.item not in item_stock_ledger:

					new_stock_ledger = frappe.new_doc("Stock Ledger")
					new_stock_ledger.item = docitem.item
					new_stock_ledger.item_name = docitem.item_name
					new_stock_ledger.warehouse = docitem.warehouse
					new_stock_ledger.posting_date = posting_date_time

					new_stock_ledger.qty_in = docitem.qty_in_base_unit
					new_stock_ledger.incoming_rate = docitem.rate_in_base_unit
					new_stock_ledger.unit = docitem.base_unit
					new_stock_ledger.valuation_rate = valuation_rate
					new_stock_ledger.balance_qty = new_balance_qty
					new_stock_ledger.balance_value = new_balance_value
					new_stock_ledger.change_in_stock_value = change_in_stock_value
					new_stock_ledger.voucher = "Purchase Receipt"
					new_stock_ledger.voucher_no = self.name
					new_stock_ledger.source = "Purchase Receipt Item"
					new_stock_ledger.source_document_id = docitem.name
					new_stock_ledger.insert()

					sl = frappe.get_doc("Stock Ledger", new_stock_ledger.name)

					item_stock_ledger[docitem.item] = sl.name

				else:
					stock_ledger_name = item_stock_ledger.get(docitem.item)
					stock_ledger = frappe.get_doc('Stock Ledger', stock_ledger_name)

					stock_ledger.qty_in = stock_ledger.qty_in + docitem.qty_in_base_unit
					stock_ledger.balance_qty = stock_ledger.balance_qty + docitem.qty_in_base_unit
					stock_ledger.balance_value = stock_ledger.balance_qty * stock_ledger.valuation_rate
					stock_ledger.change_in_stock_value = stock_ledger.change_in_stock_value + (stock_ledger.balance_qty * stock_ledger.valuation_rate)
					new_balance_qty = stock_ledger.balance_qty
					stock_ledger.save()

				# If no more records for the item, update balances. otherwise it updates in the flow
				if more_records_count_for_item==0:

					if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
						frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse})

					new_stock_balance = frappe.new_doc('Stock Balance')
					new_stock_balance.item = docitem.item
					new_stock_balance.item_name = docitem.item_name
					new_stock_balance.unit = docitem.base_unit
					new_stock_balance.warehouse = docitem.warehouse
					new_stock_balance.stock_qty = new_balance_qty
					new_stock_balance.stock_value = new_balance_value
					new_stock_balance.valuation_rate = valuation_rate

					new_stock_balance.insert()


					update_stock_balance_in_item(docitem.item)

				else:
					stock_recalc_voucher.append('records',{'item': docitem.item,
															'warehouse': docitem.warehouse,
															'base_stock_ledger': new_stock_ledger.name
																})
		# posting_status_doc = frappe.get_doc("Document Posting Status",{'document_type':'Purchase Invoice','document_name':self.name})
		# posting_status_doc.stock_posted_time = datetime.now()
		# posting_status_doc.save()
		update_posting_status(self.doctype, self.name, 'stock_posted_time', None)

		if(more_records>0):
			stock_recalc_voucher.insert()
			# self.stock_recalc_voucher = stock_recalc_voucher.name
			# posting_status_doc = frappe.get_doc("Document Posting Status",{'document_type':'Purchase Invoice','document_name':self.name})
			# posting_status_doc.stock_recalc_required = True
			# posting_status_doc.save()

			update_posting_status(self.doctype, self.name, 'stock_recalc_required', True)

			recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)
			# posting_status_doc = frappe.get_doc("Document Posting Status",{'document_type':'Purchase Invoice','document_name':self.name})
			# posting_status_doc.stock_recalc_time =datetime.now()
			# posting_status_doc.save()

			update_posting_status(self.doctype, self.name, 'stock_recalc_time', None)
	
	def do_asset_posting(self,item, asset_category):
     
		# Get the default company from the Global Settings
		company = frappe.db.get_single_value("Global Settings", "default_company")

		# Get the default asset location for the specified company
		default_asset_location = frappe.get_value("Company", company, 'default_asset_location')

		# Check if the default asset location is not set
		if not default_asset_location:
			# Try to retrieve the 'Default Asset Location' document
			asset_location = frappe.db.exists("Asset Location", "Default Asset Location")

			# If the 'Default Asset Location' document does not exist, create it
			if not asset_location:
				asset_location = frappe.new_doc("Asset Location")
				asset_location.location_name = "Default Asset Location"
				asset_location.insert()  # Save the new asset location document
				default_asset_location = asset_location.name
			else:
				default_asset_location = asset_location

			# You should probably link the default asset location with the company here
			# Assuming 'default_asset_location' is a field in the 'Company' doctype
			frappe.db.set_value("Company", company, "default_asset_location", default_asset_location)
		
		asset = frappe.new_doc("Asset")
		asset.asset_name = item.name
		asset.item = item.item_code
		asset.asset_category = asset_category
		asset.asset_location = default_asset_location
		asset.gross_value = item.gross_amount
		asset.posting_date = self.posting_date
		asset.posting_time = self.posting_time
		asset.insert()
  
	def get_narration(self):
     
				# Assign supplier, invoice_no, and remarks
		supplier = self.supplier
		invoice_no = self.supplier_inv_no
		remarks = self.remarks if self.remarks else ""
		payment_mode = ""
		if self.credit_purchase:
			payment_mode = "Credit"
		else:
			payment_mode = self.payment_mode
		
		# Get the gl_narration which might be empty
		gl_narration = get_gl_narration('Purchase Receipt')  # This could return an empty string

		# Provide a default template if gl_narration is empty
		if not gl_narration:
			gl_narration = "Purchase from {supplier}"

		#print("gl_narration")
		#print(gl_narration)

		# Replace placeholders with actual values
		narration = gl_narration.format(payment_mode=payment_mode, supplier=supplier, invoice_no=invoice_no)

		# Append remarks if they are available
		if remarks:
			narration += f", {remarks}"

		return narration   
  
	def insert_gl_records(self):

		remarks = self.get_narration()
		
		default_company = frappe.db.get_single_value("Global Settings","default_company")

		default_accounts = frappe.get_value("Company", default_company,['default_payable_account','default_inventory_account',

		'stock_received_but_not_billed','round_off_account','tax_account'], as_dict=1)

		idx =1
		# Trade Payable - Credit - Against Inventory A/c
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Purchase Receipt"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.stock_received_but_not_billed
		gl_doc.credit_amount = self.net_total - self.tax_total
		gl_doc.party_type = "Supplier"
		gl_doc.party = self.supplier
		gl_doc.against_account = default_accounts.default_inventory_account
		gl_doc.remarks = remarks
		gl_doc.insert()
		idx +=1

		# Stock Received But Not Billed - Debit - Against Trade Payable A/c
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Purchase Receipt"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.default_inventory_account
		gl_doc.debit_amount =  self.net_total - self.tax_total
		gl_doc.against_account = default_accounts.stock_received_but_not_billed
		gl_doc.remarks = remarks
		gl_doc.insert()
		idx +=1

		update_posting_status(self.doctype,self.name, 'gl_posted_time',None)
   
	def cancel_purchase(self):

        # Insert record to 'Stock Recalculate Voucher' doc
		stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher.voucher = 'Purchase Receipt'
		stock_recalc_voucher.voucher_no = self.name
		stock_recalc_voucher.voucher_date = self.posting_date
		stock_recalc_voucher.voucher_time = self.posting_time
		stock_recalc_voucher.status = 'Not Started'
		stock_recalc_voucher.source_action = "Cancel"

		posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))

		more_records = 0

		# Iterate on each item from the cancelling purchase invoice
		for docitem in self.items:
			more_records_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
            	'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})

			more_records = more_records + more_records_for_item

			previous_stock_ledger_name = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
            		    , 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)

			# If any items in the collection has more records
			if(more_records_for_item>0):

				if(previous_stock_ledger_name):
					stock_recalc_voucher.append('records',{'item': docitem.item,
                                                            'warehouse': docitem.warehouse,
                                                            'base_stock_ledger': previous_stock_ledger_name
                                                            })
				else:
					stock_recalc_voucher.append('records',{'item': docitem.item,
															'warehouse': docitem.warehouse,
															'base_stock_ledger': "No Previous Ledger"
															})

			else:

				balance_qty =0
				balance_value =0
				valuation_rate  = 0

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

		# posting_status_doc = frappe.get_doc("Document Posting Status",{'document_type':'Purchase Invoice','document_name':self.name})
		# posting_status_doc.stock_posted_on_cancel_time = datetime.now()
		# posting_status_doc.save()

		update_posting_status(self.doctype, self.name, 'stock_posted_on_cancel_time', None)

		if(more_records>0):
			# posting_status_doc = frappe.get_doc("Document Posting Status",{'document_type':'Purchase Invoice','document_name':self.name})
			# posting_status_doc.stock_recalc_required_on_cancel = True
			# posting_status_doc.save()

			update_posting_status(self.doctype, self.name, 'stock_recalc_required_on_cancel', True)

			stock_recalc_voucher.insert()
			recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)

			# posting_status_doc = frappe.get_doc("Document Posting Status",{'document_type':'Purchase Invoice','document_name':self.name})
			# posting_status_doc.stock_recalc_on_cancel_time = datetime.now()
			# posting_status_doc.save()
			update_posting_status(self.doctype, self.name, 'stock_recalc_on_cancel_time', None)

		frappe.db.delete("Stock Ledger",
				{"voucher": "Purchase Receipt",
					"voucher_no":self.name
				})

		delete_gl_postings_for_cancel_doc_type('Purchase Receipt', self.name)

		update_posting_status(self.doctype, self.name, 'posting_status', 'Completed')

	def update_project_purchase_amount(self, cancel=False):
		if self.project:
			# Define filters to fetch submitted purchase receipts excluding the current document
			filters = {
				"project": self.project,
				"name": ["!=", self.name],  # Exclude the current document
				"docstatus": 1  # Include only submitted documents
			}

			total_received_amount_gross = 0

			# Fetch all submitted Purchase Receipts related to the project
			purchase_receipts = frappe.get_all(
				"Purchase Receipt",
				filters=filters,
				fields=["rounded_total", "gross_total"]
			)

			# Iterate through Purchase Receipts
			for receipt in purchase_receipts:				
				total_received_amount_gross += receipt.get("gross_total", 0)

			# If not cancelling, add the current document's contribution
			if not cancel:
       
				# Add the current document's gross_total and rounded_total				
				total_received_amount_gross += self.gross_total or 0

			# Update the 'total_received_amount' and 'total_received_amount_gross' fields in the Project
			frappe.db.set_value("Project",self.project,{"purchase_cost_gross": total_received_amount_gross})
			
			# Optional: Feedback or logging
			frappe.msgprint(
				f"The 'Purchase Cost' of project {self.project} have been updated successfully", alert=True
			)

@frappe.whitelist()
def generate_purchase_invoice_for_purchase_receipt(purchase_receipt):

	purchase_doc = frappe.get_doc("Purchase Receipt", purchase_receipt)

	# Create Purchase Invoice
	purchase_invoice = frappe.new_doc("Purchase Invoice")
	purchase_invoice.supplier = purchase_doc.supplier
	purchase_invoice.company = purchase_doc.company
	purchase_invoice.project = purchase_doc.project
	purchase_invoice.default_cost_center = purchase_doc.default_cost_center
	purchase_invoice.supplier_address = purchase_doc.supplier_address
	purchase_invoice.tax_id = purchase_doc.tax_id
	purchase_invoice.posting_date = purchase_doc.posting_date
	purchase_invoice.posting_time = purchase_doc.posting_time
	purchase_invoice.price_list = purchase_doc.price_list
	purchase_invoice.do_no = purchase_doc.do_no
	purchase_invoice.warehouse = purchase_doc.warehouse
	purchase_invoice.supplier_inv_no = purchase_doc.supplier_inv_no
	purchase_invoice.rate_includes_tax = purchase_doc.rate_includes_tax
	purchase_invoice.credit_purchase = purchase_doc.credit_purchase
	
	
	purchase_invoice.credit_days = purchase_doc.credit_days
	purchase_invoice.payment_terms = purchase_doc.payment_terms
 
	purchase_invoice.payment_mode = purchase_doc.payment_mode
	purchase_invoice.payment_account = purchase_doc.payment_account
 
	#print("check credit options")
	#print(purchase_doc.credit_purchase)
	#print(purchase_doc.payment_mode)
	#print(purchase_doc.payment_account)
 
	purchase_invoice.remarks = purchase_doc.remarks
	purchase_invoice.reference_no = purchase_doc.reference_no
	purchase_invoice.reference_date = purchase_doc.reference_date
	purchase_invoice.gross_total = purchase_doc.gross_total
	purchase_invoice.total_discount_in_line_items = purchase_doc.total_discount_in_line_items
	purchase_invoice.tax_total = purchase_doc.tax_total
	purchase_invoice.net_total = purchase_doc.net_total
	purchase_invoice.round_off = purchase_doc.round_off
	purchase_invoice.rounded_total = purchase_doc.rounded_total
	purchase_invoice.paid_amount = purchase_doc.paid_amount
	purchase_invoice.terms = purchase_doc.terms
	purchase_invoice.terms_and_conditions = purchase_doc.terms_and_conditions
	#print("purchase_receipt")
	#print(purchase_receipt)
	purchase_invoice.purchase_receipt = purchase_receipt
	purchase_invoice.purchase_order = purchase_doc.purchase_order

	# pending_item_exists = False
	# pending_item_exists = True

	# Append items from Purchase Order to Purchase Invoice
	for item in purchase_doc.items:

		# if(item.qty_in_base_unit - item.qty_purchased_in_base_unit>0):
		# 	pending_item_exists = True
			invoice_item = frappe.new_doc("Purchase Invoice Item")
			invoice_item.item = item.item
			invoice_item.item_name = item.item_name
			invoice_item.display_name = item.display_name
			invoice_item.qty = item.qty
			invoice_item.unit = item.unit
			invoice_item.rate = item.rate_in_base_unit * item.conversion_factor
			invoice_item.base_unit = item.base_unit
			invoice_item.qty_in_base_unit = item.qty_in_base_unit
			invoice_item.rate_in_base_unit = item.rate_in_base_unit
			invoice_item.conversion_factor = item.conversion_factor
			invoice_item.rate_includes_tax = item.rate_includes_tax
			invoice_item.rate_excluded_tax = item.rate_excluded_tax
			invoice_item.warehouse = item.warehouse
			invoice_item.gross_amount = item.gross_amount
			invoice_item.tax_excluded = item.tax_excluded
			invoice_item.tax = item.tax
			invoice_item.tax_rate = item.tax_rate
			invoice_item.tax_amount = item.tax_amount
			invoice_item.discount_percentage = item.discount_percentage
			invoice_item.discount_amount = item.discount_amount
			invoice_item.net_amount = item.net_amount
			invoice_item.po_item_reference = item.po_item_reference
			purchase_invoice.append("items", invoice_item)

	# if pending_item_exists:
	purchase_invoice.insert()
	frappe.db.commit()
	frappe.msgprint("Purchase Invoice generated in draft mode", alert=True)
	return purchase_invoice.name
	# else:
	# 	frappe.msgprint("Purchase Invoice cannot be created because there are no pending items in the Purchase Order.")
	# 	return "No Pending Items"
	
