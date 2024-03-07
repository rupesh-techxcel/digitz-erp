# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now
from frappe.model.document import Document
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_stock_balance_in_item
from digitz_erp.api.purchase_order_api import check_and_update_purchase_order_status
from frappe.model.mapper import *
from digitz_erp.api.item_price_api import update_item_price,update_supplier_item_price
from digitz_erp.api.settings_api import get_default_currency
from digitz_erp.api.purchase_invoice_api import check_balance_qty_to_return_for_purchase_invoice
from digitz_erp.api.document_posting_status_api import init_document_posting_status, update_posting_status
from datetime import datetime,timedelta
from frappe.model.mapper import get_mapped_doc
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type
from digitz_erp.api.bank_reconciliation_api import create_bank_reconciliation, cancel_bank_reconciliation
from frappe import throw, _

class PurchaseInvoice(Document):

	# def before_submit(self):
		# possible_invalid= frappe.db.count('Purchase Invoice', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time], 'docstatus':['=', 1]})
		# When duplicating the voucher user may not remember to change the date and time. So do not allow to save the voucher to be
		# posted on the same time with any of the existing vouchers. This also avoid invalid selection to calculate moving average value
		# Also in add_stock_for_purchase_receipt method only checking for < date_time in order avoid difficulty to get exact last record
		# to get balance qty and balance value.
		# if(possible_invalid >0):
		# 	frappe.throw("There is another purchase invoice exist with the same date and time. Please correct the date and time.")

	def Voucher_In_The_Same_Time(self):
		possible_invalid= frappe.db.count('Purchase Invoice', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time]})
		return possible_invalid

	def Set_Posting_Time_To_Next_Second(self):
		datetime_object = datetime.strptime(str(self.posting_time), '%H:%M:%S')

		# Add one second to the datetime object
		new_datetime = datetime_object + timedelta(seconds=1)

		# Extract the new time as a string
		self.posting_time = new_datetime.strftime('%H:%M:%S')


	def before_validate(self):

		print("before_validate")
		if not self.credit_purchase or self.credit_purchase  == False:

			self.paid_amount = self.rounded_total
		else:
			self.paid_amount = 0

		# When duplicating the voucher user may not remember to change the date and time. So do not allow to save the voucher to be
		# posted on the same time with any of the existing vouchers. This also avoid invalid selection to calculate moving average value

		if(self.Voucher_In_The_Same_Time()):

			self.Set_Posting_Time_To_Next_Second()

			if(self.Voucher_In_The_Same_Time()):
				self.Set_Posting_Time_To_Next_Second()

				if(self.Voucher_In_The_Same_Time()):
					self.Set_Posting_Time_To_Next_Second()

					if(self.Voucher_In_The_Same_Time()):
						frappe.throw("Voucher with same time already exists.")

	def validate(self):
		self.validate_supplier_inv_no()
		if not self.credit_purchase and self.payment_mode == None:
			frappe.throw("Select Payment Mode")

	def validate_supplier_inv_no(self):
		existing_invoice = frappe.db.get_value("Purchase Invoice",{"supplier": self.supplier, "supplier_inv_no": self.supplier_inv_no,"name": ("!=", self.name) if self.name else None})
		if existing_invoice:
			throw(_("Duplicate Supplier Inv No: Supplier {0}, Invoice No {1}, Existing Invoice: {2}").format(self.supplier, self.supplier_inv_no, existing_invoice))

	def on_submit(self):

		print("on_submit")

		init_document_posting_status(self.doctype, self.name)

		turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

		# if(frappe.session.user == "Administrator" and turn_off_background_job):
		# 	self.do_postings_on_submit()
		# else:
			# frappe.enqueue(self.do_postings_on_submit, queue="long")
  			# frappe.msgprint("The relevant postings for this document are happening in the background. Changes may take a few seconds to reflect.", alert=1)
		self.do_postings_on_submit()

	def do_postings_on_submit(self):

		self.insert_gl_records(self.remarks)
		self.insert_payment_postings()
		self.add_stock_for_purchase_receipt()
		create_bank_reconciliation("Purchase Invoice", self.name)

		# posting_status_doc = frappe.get_doc("Document Posting Status",{'document_type':'Purchase Invoice','document_name':self.name})
		# print(posting_status_doc)
		# posting_status_doc.posting_status = "Completed"
		# posting_status_doc.save()

		update_accounts_for_doc_type('Purchase Invoice',self.name)
		self.update_supplier_prices()

		update_posting_status(self.doctype, self.name, 'posting_status','Completed')
		print("after status update")

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

	def update_supplier_prices(self):

		for docitem in self.items:
				item = docitem.item
				rate = docitem.rate_in_base_unit
				update_supplier_item_price(item, self.supplier,rate,self.posting_date)

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

		# Create a dictionary for handling duplicate items. In stock ledger posting it is expected to have only one stock ledger per item per voucher.
		item_stock_ledger = {}

		for docitem in self.items:
			maintain_stock = frappe.db.get_value('Item', docitem.item , 'maintain_stock')
			print('MAINTAIN STOCK :', maintain_stock)
			if(maintain_stock == 1):

   		# Check for more records after this date time exists. This is mainly for deciding whether stock balance needs to update
		# in this flow itself. If more records, exists stock balance will be udpated lateer
				more_records_count_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
					'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})

				more_records = more_records + more_records_count_for_item

				new_balance_qty = docitem.qty_in_base_unit

				print("default balance qty")
				print(new_balance_qty)

				# Default valuation rate
				valuation_rate = docitem.rate_in_base_unit

				print("default valuation rate")
				print(valuation_rate)

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

					print("new_balance_qty")
					print(new_balance_qty)

					print("new_balance_value")
					print(new_balance_value)

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
					new_stock_ledger.voucher = "Purchase Invoice"
					new_stock_ledger.voucher_no = self.name
					new_stock_ledger.source = "Purchase Invoice Item"
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
					new_stock_balance.unit = docitem.unit
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

	def on_cancel(self):
		cancel_bank_reconciliation("Purchase Invoice", self.name)
		update_posting_status(self.doctype, self.name, 'posting_status', 'Cancel Pending')
		turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

		# if(frappe.session.user == "Administrator" and turn_off_background_job):
		# 	self.cancel_purchase()
		# else:
			# frappe.enqueue(self.cancel_purchase, queue="long")
		self.cancel_purchase()

		frappe.msgprint("The relevant postings for this document are happening in the background. Changes may take a few seconds to reflect.", alert=1)

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
				{"voucher": "Purchase Invoice",
					"voucher_no":self.name
				})

		delete_gl_postings_for_cancel_doc_type('Purchase Invoice', self.name)

		# frappe.db.delete("GL Posting",
		# 		{"voucher_type": "Purchase Invoice",
		# 			"voucher_no":self.name
		# 		})

		update_posting_status(self.doctype, self.name, 'posting_status', 'Completed')

	def insert_gl_records(self, remarks):

		print("from insert_gl_records")
		default_company = frappe.db.get_single_value("Global Settings","default_company")

		default_accounts = frappe.get_value("Company", default_company,['default_payable_account','default_inventory_account',

		'stock_received_but_not_billed','round_off_account','tax_account'], as_dict=1)

		idx =1
		# Trade Payable - Credit - Against Inventory A/c
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
		gl_doc.against_account = default_accounts.default_inventory_account
		gl_doc.remarks = remarks
		gl_doc.insert()
		idx +=1

		# Stock Received But Not Billed - Debit - Against Trade Payable A/c

		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Purchase Invoice"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.default_inventory_account
		gl_doc.debit_amount =  self.net_total - self.tax_total
		gl_doc.against_account = default_accounts.default_payable_account
		gl_doc.remarks = remarks
		gl_doc.insert()
		idx +=1

		# Tax - Debit - Against Trade Payable A/c
		if self.tax_total>0:
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Purchase Invoice"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.tax_account
			gl_doc.debit_amount = self.tax_total
			gl_doc.against_account = default_accounts.default_payable_account
			gl_doc.remarks = remarks
			gl_doc.insert()
			idx +=1

		# Round Off
		if self.round_off!=0.00:
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Purchase Invoice"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.round_off_account

			if self.rounded_total > self.net_total:
				gl_doc.debit_amount = abs(self.round_off)
				gl_doc.against_account = default_accounts.default_inventory_account
			else:
				gl_doc.credit_amount = abs(self.round_off)
				gl_doc.against_account = default_accounts.default_payable_account

			gl_doc.remarks = remarks

			gl_doc.insert()
			idx +=1

		update_posting_status(self.doctype,self.name, 'gl_posted_time',None)

	def insert_gl_record(self,gl_doc, accounts):
		gl_doc.insert()
		if gl_doc.account not in accounts:
				accounts.append(gl_doc.account)

	def insert_payment_postings(self):

		if self.credit_purchase==0:

			gl_count = frappe.db.count('GL Posting',{'voucher_type':'Purchase Invoice', 'voucher_no': self.name})


			default_company = frappe.db.get_single_value("Global Settings","default_company")

			default_accounts = frappe.get_value("Company", default_company,['default_payable_account','default_inventory_account',
			'stock_received_but_not_billed','round_off_account','tax_account'], as_dict=1)

			# payment_mode = frappe.get_value("Payment Mode", self.payment_mode, ['account'],as_dict=1)

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
			gl_doc.against_account = self.payment_account
			gl_doc.insert()

			idx= idx + 1

			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Purchase Invoice"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = self.payment_account
			gl_doc.credit_amount = self.rounded_total
			gl_doc.against_account = default_accounts.default_payable_account
			gl_doc.insert()

			# posting_status_doc = frappe.get_doc("Document Posting Status",{'document_type':'Purchase Invoice','document_name':self.name})
			# posting_status_doc.payment_posted_time = datetime.now()
			# posting_status_doc.save()
			update_posting_status(self.doctype, self.name, 'payment_posted_time', None)

@frappe.whitelist()
def get_default_payment_mode():
    default_payment_mode = frappe.db.get_value('Company', filters={'name'},fieldname='default_payment_mode_for_purchase')
    print(default_payment_mode)
    return default_payment_mode

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

	exclude_field = 'name'

	# Modify the existing lists to exclude 'name' field
	source_fields = [field for field in source_fields if field['fieldname'] != exclude_field]
	target_fields = [field for field in target_fields if field['fieldname'] != exclude_field]

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

	# doc.name = frappe.get_auto_incremented_value('Purchase Return')

	doc.name = ""

	pi_doc = frappe.get_doc("Purchase Invoice", source_name)

	selected_item_names = []

	# Iterate through items
	for item in pi_doc.items:
		qty_returned = item.get('qty_returned', 0)
		qty = item.get('qty', 0)

		# Check condition: qty_returned < qty
		if qty_returned < qty:
			selected_item_names.append(item.get('name'))

	filtered_items = []

	# Create a new list to store items without removing unwanted ones
	for item_name in selected_item_names:
		# Check if the item with pi_item_reference already exists in filtered_items
		item_exists = any(item.pi_item_reference == item_name for item in filtered_items)

		if not item_exists:
			# If the item doesn't exist in filtered_items, find it in doc.items and append it
			for item in doc.items:
				if item.pi_item_reference == item_name:

						# Again check in the orginal PI to get the qty for return
						for pi_item in pi_doc.items:
							if pi_item.name == item_name:
								# Calculate the quantity difference
								qty_difference = pi_item.qty - pi_item.qty_returned

								# Modify the item's qty with the new variable value
								item.qty = qty_difference
								item.parent = doc.name
								filtered_items.append(item)
								break  # Break out of the inner loop once the item is found and appended

 	# Update the document with the filtered items
	doc.items = filtered_items
	return doc

@frappe.whitelist()
def get_gl_postings(purchase_invoice):
    gl_postings = frappe.get_all("GL Posting",
                                  filters={"voucher_no": purchase_invoice},
                                  fields=["name", "debit_amount", "credit_amount", "against_account", "remarks"])
    formatted_gl_postings = []
    for posting in gl_postings:
        formatted_gl_postings.append({
            "gl_posting": posting.name,
            "debit_amount": posting.debit_amount,
            "credit_amount": posting.credit_amount,
            "against_account": posting.against_account,
            "remarks": posting.remarks
        })

    return formatted_gl_postings

@frappe.whitelist()
def get_stock_ledgers(purchase_invoice):
    stock_ledgers = frappe.get_all("Stock Ledger",
                                    filters={"voucher_no": purchase_invoice},
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
    print(formatted_stock_ledgers)
    return formatted_stock_ledgers
