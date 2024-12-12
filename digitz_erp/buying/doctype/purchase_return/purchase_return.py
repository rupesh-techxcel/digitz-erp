# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now
from frappe.model.document import Document
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_stock_balance_in_item
from digitz_erp.api.settings_api import get_gl_narration
from frappe.model.mapper import *
from frappe.utils import money_in_words
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type
from digitz_erp.api.bank_reconciliation_api import create_bank_reconciliation, cancel_bank_reconciliation
from digitz_erp.api.purchase_order_api import check_and_update_purchase_order_status

class PurchaseReturn(Document):

	def before_validate(self):
		self.in_words = money_in_words(self.rounded_total,"AED")
		self.update_purchase_invoice_references()

	def validate(self):
		self.validate_purchase()
		self.validate_stock()

	def validate_purchase(self):

		for docitem in self.items:
			if(docitem.pi_item_reference):

				pi = frappe.get_doc("Purchase Invoice Item", docitem.pi_item_reference)

				total_returned_qty_not_in_this_pr = frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_returned_qty from `tabPurchase Return Item` preti inner join `tabPurchase Return` pret on preti.parent= pret.name WHERE preti.pi_item_reference=%s AND pret.name !=%s and pret.docstatus<2""",(docitem.pi_item_reference, self.name))[0][0]

				pi_item = frappe.get_doc("Purchase Invoice Item", docitem.pi_item_reference)

				#print("total_returned_qty_not_in_this_pr")
				#print(total_returned_qty_not_in_this_pr)
				#print(docitem.qty_in_base_unit)

				if total_returned_qty_not_in_this_pr:
					if(pi_item.qty_in_base_unit < (total_returned_qty_not_in_this_pr + docitem.qty_in_base_unit)):
						frappe.throw("The quantity available for return in the original purchase is less than the quantity specified in the line item {}".format(docitem.idx))
				else:
					if(pi_item.qty_in_base_unit < docitem.qty_in_base_unit):
						frappe.throw("The quantity available for return in the original purchase is less than the quantity specified in the line item {}".format(docitem.idx))

	def validate_stock(self):

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

	def on_submit(self):

		turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

		# if(frappe.session.user == "Administrator" and turn_off_background_job):
		# 	self.do_postings_on_submit()
		# else:
			# frappe.enqueue(self.do_postings_on_submit, queue="long")
		self.do_postings_on_submit()

	def on_update(self):
		self.update_purchase_invoice_quantities_on_update()
		self.update_purchase_order_quantities_on_update()
		self.update_purchase_order_status()
		self.update_payment_schedules()

	def on_cancel(self):

		cancel_bank_reconciliation("Purchase Return", self.name)
		self.update_purchase_invoice_quantities_on_update(for_delete_or_cancel=True)
		self.update_purchase_order_quantities_on_update(for_delete_or_cancel=True)
		self.update_purchase_order_status()
		self.do_postings_for_cancel()


	def on_trash(self):
		# On cancel, the quantities are already deleted.
		if(self.docstatus < 2):
			self.update_purchase_invoice_quantities_on_update(for_delete_or_cancel=True)
			self.update_purchase_order_quantities_on_update(for_delete_or_cancel=True)
			self.update_purchase_order_status()

	def update_payment_schedules(self):
		# Check for existing payment schedules
		existing_entries = frappe.get_all("Payment Schedule", filters={"payment_against": "Return", "document_no": self.name})

    # Delete existing payment schedules if found
		for entry in existing_entries:
			try:
				frappe.delete_doc("Payment Schedule", entry.name)
			except Exception as e:
				frappe.log_error("Error deleting payment schedule: " + str(e))

		# If credit purchase, create/update payment schedules
		if self.credit_purchase and self.payment_schedule:
			for schedule in self.payment_schedule:
				new_payment_schedule = frappe.new_doc("Payment Schedule")
				new_payment_schedule.payment_against = "Return"
				new_payment_schedule.supplier = self.supplier
				new_payment_schedule.document_no = self.name
				new_payment_schedule.document_date = self.posting_date
				new_payment_schedule.scheduled_date = schedule.date
				new_payment_schedule.amount = schedule.amount

				try:
					new_payment_schedule.insert()
				except Exception as e:
					frappe.log_error("Error creating payment schedule: " + str(e))


	def do_postings_on_submit(self):
		self.insert_gl_records()
		self.insert_payment_postings()
		self.do_stock_posting()
		update_accounts_for_doc_type('Purchase Return', self.name)
		create_bank_reconciliation("Purchase Return", self.name)

	def do_stock_posting(self):
		# Note that negative stock checking is handled in the validate method
		stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher.voucher = 'Purchase Return'
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
			maintain_stock = frappe.db.get_value('Item', docitem.item , 'maintain_stock')
			#print('MAINTAIN STOCK :', maintain_stock)
			if(maintain_stock == 1):

   		# Check for more records after this date time exists. This is mainly for deciding whether stock balance needs to update
		# in this flow itself. If more records, exists stock balance will be udpated later
				more_records_count_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
					'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})
				more_records = more_records + more_records_count_for_item
				new_balance_qty = docitem.qty_in_base_unit * -1

				previous_stock_ledger_name = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
	                , 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)

				# Default valuation rate
				valuation_rate = docitem.rate_in_base_unit
				# Default balance value calculating withe the current row only. Note that it holds negative value
				new_balance_value = new_balance_qty * valuation_rate

				# Assigned current stock value to use if previous values not exist
				change_in_stock_value = new_balance_value

				dbCount = frappe.db.count('Stock Ledger',{'item': ['=', docitem.item],'warehouse':['=', docitem.warehouse],
	                                             'posting_date': ['<', posting_date_time]})
				if(dbCount>0):
					# Find out the balance value and valuation rate. Here recalculates the total balance value and valuation rate
					# from the balance qty in the existing rows x actual incoming rate
					last_stock_ledger = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse],
	                                                        'posting_date':['<', posting_date_time]},
	                                            ['balance_qty', 'balance_value', 'valuation_rate'],order_by='posting_date desc', as_dict=True)

					# Note that in the first step new_balance_qty and new_balance_value is negative
					new_balance_qty = last_stock_ledger.balance_qty - abs(new_balance_qty)
					new_balance_value = last_stock_ledger.balance_value - abs(new_balance_value)

					if new_balance_qty!=0:
						# Sometimes the balance_value and balance_qty can be negative, so it is ideal to take the abs value
						valuation_rate = abs(new_balance_value)/abs(new_balance_qty)

					change_in_stock_value = new_balance_value - last_stock_ledger.balance_value

				if docitem.item not in item_stock_ledger:
					new_stock_ledger = frappe.new_doc("Stock Ledger")
					new_stock_ledger.item = docitem.item
					new_stock_ledger.item_name = docitem.item_name
					new_stock_ledger.warehouse = docitem.warehouse
					new_stock_ledger.posting_date = posting_date_time
					new_stock_ledger.qty_out = docitem.qty_in_base_unit
					new_stock_ledger.outgoing_rate = docitem.rate_in_base_unit
					new_stock_ledger.unit = docitem.base_unit
					new_stock_ledger.valuation_rate = valuation_rate
					new_stock_ledger.balance_qty = new_balance_qty
					new_stock_ledger.balance_value = new_balance_value
					new_stock_ledger.change_in_stock_value = change_in_stock_value
					new_stock_ledger.voucher = "Purchase Return"
					new_stock_ledger.voucher_no = self.name
					new_stock_ledger.source = "Purchase Return Item"
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

				sl = frappe.get_doc("Stock Ledger", new_stock_ledger.name)
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
					# item_name = frappe.get_value("Item", docitem.item,['item_name'])
					update_stock_balance_in_item(docitem.item)

				else:
					if previous_stock_ledger_name:
						stock_recalc_voucher.append('records',{'item': docitem.item,
																'warehouse': docitem.warehouse,
																'base_stock_ledger': new_stock_ledger.name
																	})
					else:
						stock_recalc_voucher.append('records',{'item': docitem.item,
	                                                                'warehouse': docitem.warehouse,
	                                                                'base_stock_ledger': "No Previous Ledger"
	                                                                })
		if(more_records>0):
			stock_recalc_voucher.insert()
			recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)

	def do_cancel_stock_posting(self):
		 # Insert record to 'Stock Recalculate Voucher' doc
		stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher.voucher = 'Purchase Return'
		stock_recalc_voucher.voucher_no = self.name
		stock_recalc_voucher.voucher_date = self.posting_date
		stock_recalc_voucher.voucher_time = self.posting_time
		stock_recalc_voucher.status = 'Not Started'
		stock_recalc_voucher.source_action = "Cancel"
		posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))
		more_records = 0

		# Iterate on each item from the cancelling Purchase Return
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
				stock_balance = frappe.get_value('Stock Balance', {'item':docitem.item, 'warehouse':docitem.warehouse}, ['name'] )
				balance_qty =0
				balance_value =0
				valuation_rate  = 0

				if(previous_stock_ledger_name):
					previous_stock_ledger = frappe.get_doc('Stock Ledger',previous_stock_ledger_name)
					balance_qty = previous_stock_ledger.balance_qty
					balance_value = previous_stock_ledger.balance_value
					valuation_rate = previous_stock_ledger.valuation_rate

				stock_balance_for_item = frappe.get_doc('Stock Balance',stock_balance)
				# Add qty because of balance increasing due to cancellation of delivery note
				stock_balance_for_item.stock_qty = balance_qty
				stock_balance_for_item.stock_value = balance_value
				stock_balance_for_item.valuation_rate = valuation_rate
				stock_balance_for_item.save()
				# item_name = frappe.get_value("Item", docitem.item,['item_name'])
				update_stock_balance_in_item(docitem.item)

		# Delete the stock ledger before recalculate, to avoid it to be recalculated again
		frappe.db.delete("Stock Ledger",
		{"voucher": "Purchase Return",
			"voucher_no":self.name
		})

		if(more_records>0):
			stock_recalc_voucher.insert()
			recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)

	def do_postings_for_cancel(self):

		self.do_cancel_stock_posting()

		delete_gl_postings_for_cancel_doc_type('Purchase Return',self.name)

	def get_narration(self):
		
		# Assign supplier, invoice_no, and remarks
		supplier = self.supplier		
		remarks = self.remarks if self.remarks else ""
		payment_mode = ""
		if self.credit_purchase:
			payment_mode = "Credit"
		else:
			payment_mode = self.payment_mode
		
		# Get the gl_narration which might be empty
		gl_narration = get_gl_narration('Purchase Return')  # This could return an empty string

		# Provide a default template if gl_narration is empty
		if not gl_narration:
			gl_narration = "Purchase Return from {supplier}"

		# Replace placeholders with actual values
		narration = gl_narration.format(supplier=supplier)

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
		# Debit Payable A/c
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Purchase Return"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.default_payable_account
		gl_doc.debit_amount = self.rounded_total
		gl_doc.party_type = "Supplier"

		gl_doc.party = self.supplier
		gl_doc.against_account = default_accounts.default_inventory_account
		gl_doc.remarks = remarks
		gl_doc.insert()
		idx +=1

		# # Stock Received But Not Billed
		# idx =2
		# gl_doc = frappe.new_doc('GL Posting')
		# gl_doc.voucher_type = "Purchase Return"
		# gl_doc.voucher_no = self.name
		# gl_doc.idx = idx
		# gl_doc.posting_date = self.posting_date
		# gl_doc.posting_time = self.posting_time
		# gl_doc.account = default_accounts.stock_received_but_not_billed
		# gl_doc.debit_amount =  self.net_total - self.tax_total
		# gl_doc.against_account = self.supplier
		# gl_doc.insert()

		# Credit Tax
		if self.tax_total>0:
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Purchase Return"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.tax_account
			gl_doc.credit_amount = self.tax_total
			gl_doc.against_account = default_accounts.default_payable_account
			gl_doc.remarks = remarks
			gl_doc.insert()
			idx +=1

		# Rounded Total
		if self.round_off!=0.00:
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Purchase Return"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.round_off_account

			# If rounded_total more than net_total debit is more in the payable account
			if self.rounded_total > self.net_total:
				gl_doc.credit_amount = self.round_off
				gl_doc.against_account = default_accounts.default_payable_account
			else:
				gl_doc.debit_amount = self.round_off
				gl_doc.against_account = default_accounts.default_inventory_account
    
			gl_doc.remarks = remarks
			gl_doc.insert()
			idx +=1

		# Credit Inventory A/c

		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Purchase Return"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.default_inventory_account
		gl_doc.credit_amount = self.net_total - self.tax_total
		gl_doc.against_account = default_accounts.default_payable_account
		gl_doc.remarks = remarks
		gl_doc.insert()
		idx +=1

	def insert_payment_postings(self):
	
		remarks = self.get_narration()

		if self.credit_purchase==0:
			gl_count = frappe.db.count('GL Posting',{'voucher_type':'Purchase Return', 'voucher_no': self.name})
			default_company = frappe.db.get_single_value("Global Settings","default_company")
			default_accounts = frappe.get_value("Company", default_company,['default_payable_account','default_inventory_account',
			'stock_received_but_not_billed','round_off_account','tax_account'], as_dict=1)
			payment_mode = frappe.get_value("Payment Mode", self.payment_mode, ['account'],as_dict=1)

			idx = gl_count + 1

			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Purchase Return"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.default_payable_account
			gl_doc.credit_amount = self.rounded_total
			gl_doc.party_type = "Supplier"
			gl_doc.party = self.supplier
			gl_doc.against_account = payment_mode.account
			gl_doc.remarks = remarks
			gl_doc.insert()

			idx= idx + 1

			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Purchase Return"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = payment_mode.account
			gl_doc.debit_amount = self.rounded_total
			gl_doc.against_account = default_accounts.default_payable_account
			gl_doc.remarks = remarks
			gl_doc.insert()

	def update_purchase_invoice_references(self):

		purchase_invoice_item_reference_nos = [
			item.pi_item_reference for item in self.items if item.pi_item_reference
		]

		# Avoid repeated database queries by fetching all parent delivery notes in one go
		if purchase_invoice_item_reference_nos:
			query = """
			SELECT DISTINCT parent
			FROM `tabPurchase Invoice Item`
			WHERE name IN (%s)
			"""
			# Formatting query string for multiple items
			format_strings = ','.join(['%s'] * len(purchase_invoice_item_reference_nos))
			query = query % format_strings

			purchase_invoices = frappe.db.sql(query, tuple(purchase_invoice_item_reference_nos), as_dict=True)
			purchase_invoices = [dn['parent'] for dn in purchase_invoices if dn['parent']]
		else:
			purchase_invoices = []

		# Clear existing entries in the 'delivery_notes' child table
		self.set('invoices', [])  # Assuming 'delivery_notes' is the correct child table field name

		# Append new entries to the 'delivery_notes' child table
		for purchase_invoice in purchase_invoices:
			self.append('invoices', {  # Ensure the fieldname is correct as per your doctype structure
				'purchase_invoice': purchase_invoice
			})

	def update_purchase_invoice_quantities_on_update(self, for_delete_or_cancel=False):

		pi_reference_any = False

		for item in self.items:
			if not item.pi_item_reference:
				continue

			# Retrieve the total returned quantity for the purchase invoice item
			result = frappe.db.sql(
				"""SELECT SUM(qty_in_base_unit) as total_returned_qty
				FROM `tabPurchase Return Item` preti
				INNER JOIN `tabPurchase Return` pret ON preti.parent = pret.name
				WHERE preti.pi_item_reference=%s AND pret.name !=%s AND pret.docstatus < 2""",
				(item.pi_item_reference, self.name)
			)
			total_returned_qty_not_in_this_pr = result[0][0] if result else 0

			# Update the quantity returned in base unit for the purchase invoice item
			pi_item = frappe.get_doc("Purchase Invoice Item", item.pi_item_reference)
			additional_qty = item.qty_in_base_unit if not for_delete_or_cancel else 0
			pi_item.qty_returned_in_base_unit = (total_returned_qty_not_in_this_pr or 0) + additional_qty
			pi_item.save()
			pi_reference_any = True

		if pi_reference_any:
			frappe.msgprint("Returned qty of items in the corresponding purchase invoice updated successfully", indicator="green", alert=True)


	def update_purchase_order_quantities_on_update(self, for_delete_or_cancel=False):
		po_reference_any = False
		po_item_purchased_dict = {}
		po_item_returned_dict_not_in_this_pr = {}

		for item in self.items:
			if not item.pi_item_reference:
				continue

			#print("item.pi_item_reference")
			#print(item.pi_item_reference)
			#print("self.name")
			#print(self.name)

			pi_item = frappe.get_doc("Purchase Invoice Item", item.pi_item_reference)
			po_item_reference = pi_item.po_item_reference

			#print("po_item_reference")
			#print(po_item_reference)

			if po_item_reference:
				if po_item_reference not in po_item_returned_dict_not_in_this_pr:
					total_returned_qty_not_in_this_pr = frappe.db.sql(
						"""SELECT SUM(qty_in_base_unit) as total_returned_qty
						FROM `tabPurchase Return Item` preti
						INNER JOIN `tabPurchase Return` pret ON preti.parent = pret.name
						WHERE preti.pi_item_reference IN
						(SELECT name FROM `tabPurchase Invoice Item` pit WHERE pit.po_item_reference=%s)
						AND pret.name != %s AND pret.docstatus < 2""",
						(po_item_reference, self.name)
					)[0][0] or 0

					po_item_returned_dict_not_in_this_pr[po_item_reference] = total_returned_qty_not_in_this_pr

				current_qty = item.qty_in_base_unit if not for_delete_or_cancel else 0
				po_item_returned_dict_not_in_this_pr[po_item_reference] += current_qty

				if po_item_reference not in po_item_purchased_dict:
					total_qty_purchased_for_the_po_item = frappe.db.sql(
						"""SELECT SUM(qty_in_base_unit) as total_used_qty
						FROM `tabPurchase Invoice Item` pinvi
						INNER JOIN `tabPurchase Invoice` pinv ON pinvi.parent = pinv.name
						WHERE pinvi.po_item_reference=%s AND pinv.docstatus < 2""",
						(po_item_reference,)
					)[0][0] or 0

					po_item_purchased_dict[po_item_reference] = total_qty_purchased_for_the_po_item

				po_reference_any = True

		if po_reference_any:
			for po_item_reference, total_qty_purchased in po_item_purchased_dict.items():
				po_item = frappe.get_doc("Purchase Order Item", po_item_reference)
				qty_returned = po_item_returned_dict_not_in_this_pr.get(po_item_reference, 0)
				po_item.qty_purchased_in_base_unit = total_qty_purchased - qty_returned
				po_item.save()

			frappe.msgprint("Purchased Qty of items in the corresponding purchase Order updated successfully", indicator="green", alert=True)

	def update_purchase_order_status(self):

		purchase_orders = []

		for item in self.items:
			if not item.pi_item_reference:
				continue

			pi_item = frappe.get_doc("Purchase Invoice Item", item.pi_item_reference)
			if pi_item.po_item_reference and pi_item.po_item_reference not in purchase_orders:
				purchase_order_data = frappe.db.sql("""
					SELECT po.name
					FROM `tabPurchase Order` po
					INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
					WHERE poi.name = %s
				""", (pi_item.po_item_reference,), as_dict=True)

				if purchase_order_data:
					purchase_order_name = purchase_order_data[0]['name']
					if purchase_order_name not in purchase_orders:
						purchase_orders.append(purchase_order_name)

		for purchase_order_name in purchase_orders:
			check_and_update_purchase_order_status(purchase_order_name)  # Ensure this function expects the PO name


@frappe.whitelist()
def get_default_payment_mode():
    default_payment_mode = frappe.db.get_value('Company', filters={'name'},fieldname='default_payment_mode_for_purchase')
    #print(default_payment_mode)
    return default_payment_mode

@frappe.whitelist()
def get_stock_ledgers(purchase_return):
    stock_ledgers = frappe.get_all("Stock Ledger",
                                    filters={"voucher_no": purchase_return},
                                    fields=["name", "item", "warehouse", "qty_in", "qty_out", "valuation_rate", "balance_qty", "balance_value"])
    formatted_stock_ledgers = []
    for ledgers in stock_ledgers:
        formatted_stock_ledgers.append({
            "stock_ledger": ledgers.name,
            "item": ledgers.item,
            "warehouse": ledgers.warehouse,
            "qty_in": ledgers.qty_in,
            "qty_out": ledgers.qty_out,
            "valuation_rate": ledgers.valuation_rate,
            "balance_qty": ledgers.balance_qty,
            "balance_value": ledgers.balance_value
        })
    #print(formatted_stock_ledgers)
    return formatted_stock_ledgers
