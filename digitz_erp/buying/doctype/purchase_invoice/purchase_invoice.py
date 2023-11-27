# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now
from frappe.model.document import Document
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_item_stock_balance
from digitz_erp.api.purchase_order_api import check_and_update_purchase_order_status
from frappe.model.mapper import *
from digitz_erp.api.item_price_api import update_item_price
from digitz_erp.api.settings_api import get_default_currency
from digitz_erp.api.purchase_invoice_api import check_balance_qty_to_return_for_purchase_invoice
from datetime import datetime
from frappe.model.mapper import get_mapped_doc

class PurchaseInvoice(Document):

	# def before_submit(self):
		# possible_invalid= frappe.db.count('Purchase Invoice', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time], 'docstatus':['=', 1]})
		# When duplicating the voucher user may not remember to change the date and time. So do not allow to save the voucher to be
		# posted on the same time with any of the existing vouchers. This also avoid invalid selection to calculate moving average value
		# Also in add_stock_for_purchase_receipt method only checking for < date_time in order avoid difficulty to get exact last record
		# to get balance qty and balance value.
		# if(possible_invalid >0):
		# 	frappe.throw("There is another purchase invoice exist with the same date and time. Please correct the date and time.")
  
	def before_validate(self):
		if not self.credit_purchase or self.credit_purchase  == False:
			self.paid_amount = self.rounded_total
		else:			
			self.paid_amount = 0	
    
	def validate(self):
		if not self.credit_purchase and self.payment_mode == None:
			frappe.throw("Select Payment Mode")
   
	def on_submit(self):
     
		print("remarks")
		print(self.remarks)
    
		# assign posting_start_time before the background thread start to get the real time
		# because a lagging may happen to start the thread
		self.postings_start_time = datetime.now()		
		frappe.enqueue(self.do_postings_on_submit, queue="long")

	def do_postings_on_submit(self):		

		self.insert_gl_records(self.remarks)
		self.insert_payment_postings()  
		self.add_stock_for_purchase_receipt()  
		self.save()
  
	def on_update(self):
		print("on_update")
		if self.purchase_order:
			self.update_purchase_order_quantities_before_save()
			check_and_update_purchase_order_status(self.purchase_order)   
   
		self.update_item_prices()
		self.update_payment_schedules()

	def before_cancel(self):
		print("before_cancel")
		if self.purchase_order:
			self.update_purchase_order_quantities_before_cancel_or_delete()
			check_and_update_purchase_order_status(self.purchase_order)

	def update_purchase_order_quantities_before_cancel_or_delete(self):

		po_reference_any = False
		for item in self.items:
			if not item.po_item_reference:
				continue
			else:
				total_used_qty_not_in_this_pi = frappe.db.sql(""" SELECT SUM(qty) as total_used_qty from `tabPurchase Invoice Item` pinvi inner join `tabPurchase Invoice` pinv on pinvi.parent= pinv.name WHERE pinvi.po_item_reference=%s AND pinv.name !=%s and pinv.docstatus <2""",(item.po_item_reference, self.name))[0][0]
				po_item = frappe.get_doc("Purchase Order Item", item.po_item_reference)
    
				print("po_item")
				print(po_item)    

				if total_used_qty_not_in_this_pi: 
					po_item.qty_purchased = total_used_qty_not_in_this_pi
				else:
					po_item.qty_purchased = 0

				po_item.save()
				po_reference_any = True
    
		print("po_reference_any")
		print(po_reference_any)

    
		if(po_reference_any):
			frappe.msgprint("Purchased Qty of items in the corresponding purchase Order updated successfully", indicator= "green", alert= True)
	

	def update_purchase_order_quantities_before_save(self):		
  
		po_reference_any = False
		for item in self.items:
			if not item.po_item_reference:
				continue
			else:
				total_used_qty_not_in_this_pi = frappe.db.sql(""" SELECT SUM(qty) as total_used_qty from `tabPurchase Invoice Item` pinvi inner join `tabPurchase Invoice` pinv on pinvi.parent= pinv.name WHERE pinvi.po_item_reference=%s AND pinv.name !=%s and pinv.docstatus<2""",(item.po_item_reference, self.name))[0][0]
				po_item = frappe.get_doc("Purchase Order Item", item.po_item_reference)
				if(total_used_qty_not_in_this_pi):
					po_item.qty_purchased = total_used_qty_not_in_this_pi + item.qty
				else:
					po_item.qty_purchased = item.qty
				po_item.save()
				po_reference_any = True
    
		if(po_reference_any):
			frappe.msgprint("Purchased Qty of items in the corresponding purchase Order updated successfully", indicator= "green", alert= True)

	def add_stock_for_purchase_receipt(self):
		stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher.voucher = 'Purchase Invoice'
		stock_recalc_voucher.voucher_no = self.name
		stock_recalc_voucher.voucher_date = self.posting_date
		stock_recalc_voucher.voucher_time = self.posting_time
		stock_recalc_voucher.status = 'Not Started'
		stock_recalc_voucher.source_action = "Insert"

		more_records = 0
		posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))

		for docitem in self.items:

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


				if new_balance_qty!=0:
					valuation_rate = new_balance_value/new_balance_qty

				change_in_stock_value = new_balance_value - last_stock_ledger.balance_value


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
			new_stock_ledger.voucher = "Purchase Invoice"
			new_stock_ledger.voucher_no = self.name
			new_stock_ledger.source = "Purchase Invoice Item"
			new_stock_ledger.source_document_id = docitem.name
			new_stock_ledger.insert()

			sl = frappe.get_doc("Stock Ledger", new_stock_ledger.name)

			# If no more records for the item, update balances. otherwise it updates in the flow
			if more_records_count_for_item==0:

				if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
					frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse})

				new_stock_balance = frappe.new_doc('Stock Balance')
				new_stock_balance.item = docitem.item
				new_stock_balance.item_name = docitem.item_name
				new_stock_balance.unit = docitem.unit
				new_stock_balance.warehouse = docitem.warehouse
				new_stock_balance.stock_qty = new_balance_qty
				new_stock_balance.stock_value = new_balance_value
				new_stock_balance.valuation_rate = valuation_rate

				new_stock_balance.insert()				


				update_item_stock_balance(docitem.item)

			else:
				stock_recalc_voucher.append('records',{'item': docitem.item,
    													'warehouse': docitem.warehouse,
                                                        'base_stock_ledger': new_stock_ledger.name
                                                            })
		if(more_records>0):
			self.stock_posted = True
			self.stock_posted_time = datetime.now()
			self.stock_recalc_required = True
			
			stock_recalc_voucher.insert()			
			self.stock_recalc_voucher = stock_recalc_voucher.name   
			
			recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)	
						
			self.stock_recalc_done = True
			self.stock_recalc_done_time = datetime.now()   
			
   
		else:
			self.stock_posted = True
			self.stock_posted_time = datetime.now()
			self.stock_recalc_required = False			
   

	def on_cancel(self):
		self.cancel_purchase()
  
	def update_item_prices(self):
     
		if(self.update_rates_in_price_list):				
			currency = get_default_currency()			
			for docitem in self.items:
				print("docitem to update price")
				print(docitem)
				item = docitem.item
				rate = docitem.rate_in_base_unit
				update_item_price(item,self.price_list,currency,rate, self.posting_date)
    
	def update_payment_schedules(self):
		# Check for existing payment schedules
		existing_entries = frappe.get_all("Payment Schedule", filters={"payment_against": "Purchase", "document_no": self.name})
    
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
				new_payment_schedule.payment_against = "Purchase"
				new_payment_schedule.supplier = self.supplier
				new_payment_schedule.document_no = self.name
				new_payment_schedule.document_date = self.posting_date
				new_payment_schedule.scheduled_date = schedule.date
				new_payment_schedule.amount = schedule.amount
				
				try:
					new_payment_schedule.insert()
				except Exception as e:
					frappe.log_error("Error creating payment schedule: " + str(e))

  
	def on_trash(self):
       	
		if self.purchase_order:
			self.update_purchase_order_quantities_before_cancel_or_delete()
			check_and_update_purchase_order_status(self.purchase_order)
     

	def cancel_purchase(self):

        # Insert record to 'Stock Recalculate Voucher' doc
		stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher.voucher = 'Purchase Invoice'
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

				stock_ledger_items = frappe.get_list('Stock Ledger',{'item':docitem.item,
				'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]}, ['name','qty_in','qty_out','voucher','balance_qty','voucher_no'],order_by='posting_date')

				if(stock_ledger_items):

					qty_cancelled = docitem.qty_in_base_unit
					# Loop to verify the sufficiant quantity
					for sl in stock_ledger_items:
						# On each line if outgoing qty + balance_qty (qty before outgonig) is more than the cancelling qty
						if(sl.qty_out>0 and qty_cancelled> sl.qty_out+ sl.balance_qty):
							frappe.throw("Cancelling the purchase is prevented due to sufficiant quantity not available for " + docitem.item +
						" to fulfil the voucher " + sl.voucher_no)

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
				
				update_item_stock_balance(docitem.item)

		if(more_records>0):
			stock_recalc_voucher.insert()
			recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)

		frappe.db.delete("Stock Ledger",
				{"voucher": "Purchase Invoice",
					"voucher_no":self.name
				})

		frappe.db.delete("GL Posting",
				{"Voucher_type": "Purchase Invoice",
					"voucher_no":self.name
				})

	def insert_gl_records(self, remarks):
		default_company = frappe.db.get_single_value("Global Settings","default_company")

		default_accounts = frappe.get_value("Company", default_company,['default_payable_account','default_inventory_account',

		'stock_received_but_not_billed','round_off_account','tax_account'], as_dict=1)

		idx =1
		# Trade Payavble - Debit
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Purchase Invoice"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.default_payable_account
		gl_doc.credit_amount = self.rounded_total
		gl_doc.party_type = "Supplier"
		gl_doc.party = self.supplier
		gl_doc.aginst_account = default_accounts.stock_received_but_not_billed
		gl_doc.remarks = remarks
		gl_doc.insert()


		# Stock Received But Not Billed
		idx =2
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Purchase Invoice"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.stock_received_but_not_billed
		gl_doc.debit_amount =  self.net_total - self.tax_total
		gl_doc.aginst_account = self.supplier
		gl_doc.remarks = remarks
		gl_doc.insert()


		# Tax
		idx =3
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Purchase Invoice"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.tax_account
		gl_doc.debit_amount = self.tax_total
		gl_doc.aginst_account = self.supplier
		gl_doc.remarks = remarks
		gl_doc.insert()

		if self.round_off!=0.00:
			idx = idx + 1
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Purchase Invoice"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.round_off_account

			if self.rounded_total > self.net_total:
				gl_doc.debit_amount = self.round_off
			else:
				gl_doc.credit_amount = self.round_off

			gl_doc.aginst_account = default_accounts.default_payable_account
			gl_doc.remarks = remarks

			gl_doc.insert()

		# Postings for purchase receipt
		idx =idx+1
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Purchase Invoice"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.default_inventory_account
		gl_doc.debit_amount = self.net_total - self.tax_total
		gl_doc.aginst_account = default_accounts.stock_received_but_not_billed
		gl_doc.remarks = remarks
		gl_doc.insert()

		idx =idx + 1
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Purchase Invoice"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.stock_received_but_not_billed
		gl_doc.credit_amount = self.net_total - self.tax_total
		gl_doc.aginst_account = default_accounts.default_inventory_account
		gl_doc.remarks = remarks
		gl_doc.insert()
  
		self.gl_posted_time = datetime.now()		

	def insert_payment_postings(self):

		if self.credit_purchase==0:

			gl_count = frappe.db.count('GL Posting',{'voucher_type':'Purchase Invoice', 'voucher_no': self.name})


			default_company = frappe.db.get_single_value("Global Settings","default_company")

			default_accounts = frappe.get_value("Company", default_company,['default_payable_account','default_inventory_account',
			'stock_received_but_not_billed','round_off_account','tax_account'], as_dict=1)

			payment_mode = frappe.get_value("Payment Mode", self.payment_mode, ['account'],as_dict=1)

			idx = gl_count + 1

			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Purchase Invoice"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.default_payable_account
			gl_doc.debit_amount = self.rounded_total
			gl_doc.party_type = "Supplier"
			gl_doc.party = self.supplier
			gl_doc.aginst_account = payment_mode.account
			gl_doc.insert()

			idx= idx + 1

			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Purchase Invoice"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = payment_mode.account
			gl_doc.credit_amount = self.rounded_total
			gl_doc.aginst_account = default_accounts.stock_received_but_not_billed
			gl_doc.insert()
   
			self.payment_posted_time = datetime.now()

@frappe.whitelist()
def create_purchase_return(source_name):
    
	if(not check_balance_qty_to_return_for_purchase_invoice(source_name)):
		frappe.throw("The chosen purchase invoice lacks the eligible quantity for return.")

	# Get the source and target child table names
	source_child_table = 'Purchase Invoice Item'
	target_child_table = 'Purchase Return Item'

	# Get the field names in the source and target child tables
	source_fields = frappe.get_all('DocField', filters={'parent': source_child_table}, fields=['fieldname'])
	target_fields = frappe.get_all('DocField', filters={'parent': target_child_table}, fields=['fieldname'])

	# Create a field map based on matching field names, other than name field

	field_map = {field['fieldname']: field['fieldname'] for field in source_fields if field['fieldname'] in target_fields and field['fieldname'] != 'name'}


	# Add mapping for the new field (assuming the new field is named 'new_field_name')
	pi_reference_mapping = {
		'pi_item_reference': 'name',
	}
	# field_map.update(pi_reference_mapping)

	for key, value in pi_reference_mapping.items():
		if key not in field_map:
			field_map[key] = value

	
	doc = get_mapped_doc(
	'Purchase Invoice',
	source_name,
	{
		'Purchase Invoice': {
			'doctype': 'Purchase Return',
		},
		source_child_table: {
			'doctype': target_child_table,
			'field_map': field_map,
		},
	}	
	) 
 
	# Remove rows with qty_returned >= qty before returning the document
	for item in doc.get('items', []):
		if item.get('qty_returned', 0) is None or item.get('qty_returned', 0) >= item.get('qty', 0):
			doc.get('items').remove(item)

	# Additional logic using frm if needed
	print("purchase_return_created from PI")
	print(doc)
	return doc	
