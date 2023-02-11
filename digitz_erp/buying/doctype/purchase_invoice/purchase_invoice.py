# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime

from frappe.model.document import Document


class PurchaseInvoice(Document):

	def before_submit(self):		

		possible_invalid= frappe.db.count('Purchase Invoice', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time], 'docstatus':['=', 1]})				
		# When duplicating the voucher user may not remember to change the date and time. So do not allow to save the voucher to be 
		# posted on the same time with any of the existing vouchers. This also avoid invalid selection to calculate moving average value
		# Also in add_stock_for_purchase_receipt method only checking for < date_time in order avoid difficulty to get exact last record 
		# to get balance qty and balance value.

		print(possible_invalid)

		if(possible_invalid >0):			
			frappe.throw("There is another purchase invoice exist with the same date and time. Please correct the date and time.")

		self.insert_gl_records()
		self.insert_payment_postings()		
		self.add_stock_for_purchase_receipt()

	def before_cancel(self):		

		frappe.db.delete("Stock Ledger",
				{"voucher": "Purchase Invoice",
				 "voucher_no":self.name
				})
	
		frappe.db.delete("GL Posting",
				{"Voucher_type": "Purchase Invoice",
				 "voucher_no":self.name
				})


		# Take items and check any of the items has entry in stock out ledger and prevent cancellation for such purchases
		# Note that if the cancelling invoice do not have reference in stock out ledger that means all reamaining purchases
		# also do not have references because of FIFO distribution of items

		# First verify that purchase 'stock in ledger' item has reference in 'stock out ledger'
		

		# When cancel take all the items 
		# When the purchase invoice or its line item has a reference in the subsequent documents like Stock Out Ledger (with Stock In Ledger)
		# because of the reference system will not allow to remove. So only need to adjust balnces of the subsequent purchases for the items

		# posting_date_time = get_datetime(self.posting_date + " " + self.posting_time)
		# for docitem in self.items:
		# 	remaining_purchases = frappe.db.get_list('Stock In Ledger', filters= {'posting_date':['>', posting_date_time], 'item': ['=', docitem.item],'warehouse':['=', docitem.warehouse]}, fields= ['posting_date','voucher_type','voucher_no',
		# 	 'balance_qty', 'incoming_rate', 'source'], order_by='posting_date')		
	
		# 	for stock_in_ledger in remaining_purchases:

		# 		# If manual stock entered then exit the loop. The cancellation could happen only for new entries (as system prevents
		# 		# cancellation for reference documents and also purchases are picking in FIFO way cancellation happens from the old invoices is
		# 		# not likely to happen. Due to this in the following logic considering to adjust the balance quantities for the remaining records)

		# 		new_running_balance_qty = new_running_balance_qty + stock_in_ledger.running_balance_qty
		# 		value = value +  (stock_in_ledger.running_balance_qty * stock_in_ledger.incoming_rate)

	def add_stock_for_purchase_receipt(self):

		for docitem in self.items:			
			
			new_balance_qty = docitem.qty_in_base_unit
			# Default valuation rate
			valuation_rate = docitem.rate_in_base_unit						

			print("posting_date")
			print(self.posting_date)
			print("posting_time")
			print(self.posting_time)
			
			posting_date_time = get_datetime(self.posting_date + " " + self.posting_time)			

			# Default balance value calculating withe the current row only
			new_balance_value = new_balance_qty * valuation_rate



			print(posting_date_time)

			# posting_date<= consider because to take the dates with in the same minute								
			# dbCount = frappe.db.count('Stock Ledger',{'item_code': ['=', docitem.item_code],'warehouse':['=', docitem.warehouse], 'posting_date':['<=', posting_date_time]})
			dbCount = frappe.db.count('Stock Ledger',{'item_code': ['=', docitem.item_code],'warehouse':['=', docitem.warehouse], 'posting_date': ['<', posting_date_time]})
			print("dbCount")
			print(dbCount)
			print(docitem.item)
			print(docitem.warehouse)
			print(posting_date_time)

			if(dbCount>0):

				# Find out the balance value and valuation rate. Here recalculates the total balance value and valuation rate
				# from the balance qty in the existing rows x actual incoming rate

				last_stock_ledger = frappe.db.get_value('Stock Ledger', {'item_code': ['=', docitem.item_code], 'warehouse':['=', docitem.warehouse], 'posting_date':['<', posting_date_time]},['balance_qty', 'balance_value', 'valuation_rate'],order_by='posting_date desc', as_dict=True)				
				new_balance_qty = new_balance_qty + last_stock_ledger.balance_qty
				print("Last Stock Ledger Balance Qty")
				print(new_balance_qty)
				
				print("new_balance_qty")
				print(new_balance_qty)
				
				new_balance_value = new_balance_value + (last_stock_ledger.balance_value)

				print("new_balance_value")
				print(new_balance_value)

				valuation_rate = new_balance_value/new_balance_qty

				print("valuation rate 1")
				print(valuation_rate)

			
			print("Valuation Rate 2")
			print(valuation_rate)

		
			new_stock_ledger = frappe.new_doc("Stock Ledger")
			new_stock_ledger.item = docitem.item
			new_stock_ledger.warehouse = docitem.warehouse
			new_stock_ledger.posting_date = posting_date_time			
			
			new_stock_ledger.qty_in = docitem.qty_in_base_unit
			new_stock_ledger.incoming_rate = docitem.rate_in_base_unit
			new_stock_ledger.unit = docitem.base_unit
			new_stock_ledger.valuation_rate = valuation_rate
			new_stock_ledger.balance_qty = new_balance_qty
			new_stock_ledger.balance_value = new_balance_value
			new_stock_ledger.voucher = "Purchase Invoice"
			new_stock_ledger.voucher_no = self.name
			new_stock_ledger.source = "Purchase Invoice Item"
			new_stock_ledger.source_document_id = docitem.name
			new_stock_ledger.insert()	

			if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):    
				frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse} )

			new_stock_balance = frappe.new_doc('Stock Balance')	
			new_stock_balance.item = docitem.item
			new_stock_balance.unit = docitem.unit
			new_stock_balance.warehouse = docitem.warehouse
			new_stock_balance.stock_qty = new_balance_qty
			new_stock_balance.stock_value = new_balance_value
			new_stock_balance.valuation_rate = valuation_rate
			
			new_stock_balance.insert()


			item = frappe.get_doc('Item', docitem.item)
			item.stock_balance = item.stock_balance + docitem.qty_in_base_unit
			item.save()


	def insert_gl_records(self):

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
		gl_doc.insert()


		# Round Off
		
		if self.round_off!=0.00:
			idx =4
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

			gl_doc.insert()
		
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
