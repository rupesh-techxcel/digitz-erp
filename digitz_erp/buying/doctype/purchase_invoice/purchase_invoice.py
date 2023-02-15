# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now
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

	def add_stock_for_purchase_receipt(self):

		more_records = 0
		posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))
  
		for docitem in self.items:						
   
   		# For back dated purchase invoice
			more_records_count_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
				'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})
   
			more_records = more_records + more_records_count_for_item
   
   
			new_balance_qty = docitem.qty_in_base_unit
			# Default valuation rate
			valuation_rate = docitem.rate_in_base_unit						
			
			# Default balance value calculating withe the current row only
			new_balance_value = new_balance_qty * valuation_rate

			print(posting_date_time)

			# posting_date<= consider because to take the dates with in the same minute								
			# dbCount = frappe.db.count('Stock Ledger',{'item_code': ['=', docitem.item_code],'warehouse':['=', docitem.warehouse], 'posting_date':['<=', posting_date_time]})
			dbCount = frappe.db.count('Stock Ledger',{'item_code': ['=', docitem.item_code],'warehouse':['=', docitem.warehouse], 'posting_date': ['<', posting_date_time]})
			
			if(dbCount>0):

				# Find out the balance value and valuation rate. Here recalculates the total balance value and valuation rate
				# from the balance qty in the existing rows x actual incoming rate

				last_stock_ledger = frappe.db.get_value('Stock Ledger', {'item_code': ['=', docitem.item_code], 'warehouse':['=', docitem.warehouse], 
                                                        'posting_date':['<', posting_date_time]},
                                            ['balance_qty', 'balance_value', 'valuation_rate'],order_by='posting_date desc', as_dict=True)				
    
				if(last_stock_ledger):
					new_balance_qty = new_balance_qty + last_stock_ledger.balance_qty			
				
					new_balance_value = new_balance_value + (last_stock_ledger.balance_value)

					valuation_rate = new_balance_value/new_balance_qty			
		
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
			
			# If no more records for the item, update balances. otherwise it updates in the su
			if more_records_count_for_item==0: 
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
				
				item_name = frappe.get_value("Item", docitem.item,['item_name'])
				self.update_item_stock_balance(item_name)
   
			# item_balances_in_warehouses = frappe.get_list('Stock Balance',{'item': docitem.item},['stock_qty'])
			# balance_stock_qty = 0
			# balance_stock_value = 0
			# for item in item_balances_in_warehouses:
			# 	balance_stock_qty = balance_stock_qty + item.stock_qty
			# 	balance_stock_value = balance_stock_value + item.stock_value   
   
		if(more_records>0):
			self.recalculate_stock_ledgers("Add",new_stock_ledger.name)		

	def on_cancel(self):	
        
		print("after cancel event")
		self.validate_and_cancel_purchase()

		frappe.db.delete("Stock Ledger",
				{"voucher": "Purchase Invoice",
				 "voucher_no":self.name
				})
	
		frappe.db.delete("GL Posting",
				{"Voucher_type": "Purchase Invoice",
				 "voucher_no":self.name
				})
		
	def validate_and_cancel_purchase(self):
     	
		posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))					

		stock_ledger_count_for_more = 0
  
		# Iterate on each item from the cancelling purchase invoice
		for docitem in self.items:	
			more_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
            	'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})
		
			print(more_for_item)
   
			stock_ledger_count_for_more = stock_ledger_count_for_more + more_for_item
   
			# If any items in the collection has more records
			if(stock_ledger_count_for_more>0):
				
				stock_ledger_items = frappe.get_list('Stock Ledger',{'item':docitem.item,
				'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]}, ['name','qty_in','qty_out','voucher','balance_qty','voucher_no'],order_by='posting_date')

				if(stock_ledger_items):

					qty_cancelled = docitem.qty_in_base_unit

					for sl in stock_ledger_items:					
						# On each line if outgoing qty + balance_qty (qty before outgonig) is more than the cancelling qty
						if(sl.qty_out>0 and qty_cancelled> sl.qty_out+ sl.balance_qty):
							frappe.throw("Cancelling the purchase is prevented due to sufficiant quantity not available for " + docitem.item +
							" for " + sl.voucher_no)        	
					
		# If any items has subnsequent entries
		# if(stock_ledger_count_for_more>0):
		# Unconditionally do recalculation to update the balances in stock_balance and item
		self.recalculate_stock_ledgers("Cancel","")
    
	def update_item_stock_balance(self, item):
     
		print(item)

		item_balances_in_warehouses = frappe.get_list('Stock Balance',{'item': item},['stock_qty','stock_value'])
  
		balance_stock_qty = 0
		balance_stock_value = 0

		if(item_balances_in_warehouses):
			for item_stock in item_balances_in_warehouses:
       
				if item_stock.stock_qty:
					balance_stock_qty = balance_stock_qty + item_stock.stock_qty

				if item_stock.stock_value:
					balance_stock_value = balance_stock_value + item_stock.stock_value
	
		item_to_update = frappe.get_doc('Item', item)	
			
		if(not item_to_update.stock_balance):	
			print("not item.stock_balance")
			item_to_update.stock_balance = 0
			item_to_update.stock_value = 0
		item_to_update.stock_balance = balance_stock_qty
		item_to_update.stock_value = balance_stock_value
			
		item_to_update.save()	
	
	def recalculate_stock_ledgers(self, operation, new_stock_ledger_name):

        # Insert record to 'Stock Recalculate Voucher' doc
		stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher.voucher = 'Purchase Invoice'
		stock_recalc_voucher.voucher_no = self.name
		stock_recalc_voucher.voucher_date = self.posting_date
		stock_recalc_voucher.voucher_time = self.posting_time
		stock_recalc_voucher.status = 'Not Started'
		stock_recalc_voucher.source_action = operation
		stock_recalc_voucher.insert()
		
		voucher_name = stock_recalc_voucher.name
  
		posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))	
  
		# Stock Recalculate Voucher holds the entry, and records to help the calculation in the subsequent stock ledgers
		stock_recalc_voucher = frappe.get_doc('Stock Recalculate Voucher', voucher_name)
		
		for docitem in self.items:
      
			# more_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
            # 	'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})

			# # Do not continue if more items is nto exists for the item
			# if(more_for_item ==0):
			# 	continue   
   
			balance_qty = 0;
			valuation_rate = 0
			balance_value = 0
			qty_in = 0
			qty_out =0
			rate_in = 0
			rate_out = 0
			
			if(operation == "Cancel"):	
				
				# For cancel purchase invoice , fetch the previous stock ledger balance. since the stock ledger corresponding to the 
    			# cancelling invoice is not valid
				posting_date_time = get_datetime(str(stock_recalc_voucher.voucher_date) + " " + str(stock_recalc_voucher.voucher_time))
				previous_ledger_name = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
					, 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)
					
				if(previous_ledger_name):					
					previous_stock_ledger = frappe.get_doc('Stock Ledger',previous_ledger_name.name)
					qty_in = previous_stock_ledger.qty_in
					qty_out = previous_stock_ledger.qty_out
					rate_in = previous_stock_ledger.incomig_rate
					rate_out = previous_stock_ledger.outgoing_rate 
					balance_qty = previous_stock_ledger.balance_qty
					balance_value = previous_stock_ledger.balance_value
					valuation_rate = balance_value / balance_qty

				stock_recalc_voucher.append('records',{'item': docitem.item, 
															'warehouse': docitem.warehouse,                                                        
															'qty_in': qty_in,      
															'incoming_rate': rate_in,
															'qty_out': qty_out,
															'outgoing_rate':rate_out,
															'balance_qty':balance_qty,
															'balance_value':balance_value,
															'valuation_rate':valuation_rate,
															'unit': docitem.unit
						 									})
                    
			if(operation == "Add"):
    			
       			# When adding purchase invoice, take the corresponding stock ledger values(newly added stock ledger in the parent method)
				stock_ledger = frappe.get_doc("Stock Ledger", new_stock_ledger_name)				
				stock_recalc_voucher.append('records',{'item': docitem.item, 
														'warehouse': docitem.warehouse,                                                        
														'qty_in': stock_ledger.qty_in,      
														'incoming_rate': stock_ledger.incoming_rate,
														'qty_out': stock_ledger.qty_out,
														'outgoing_rate':stock_ledger.outgoing_rate,
														'balance_qty':balance_qty,
														'balance_value':balance_value,
														'valuation_rate':valuation_rate,
														'unit': docitem.unit
														})
		# stock_recalc_voucher.save()
		self.recalculate_subsequent_stock_ledgers(stock_recalc_voucher)
         
			# frappe.msgprint("Stock balances updated successfully.")
	
	def recalculate_subsequent_stock_ledgers(self,stock_recalc_voucher):
     
		# stock_recalc_voucher = frappe.get_doc("Stock Recalculate Voucher", stock_recalc_voucher_name)      
		stock_recalc_voucher.status = 'Started'
		stock_recalc_voucher.start_time = now()
		print(stock_recalc_voucher)
		print(stock_recalc_voucher.records)

		posting_date_time = get_datetime(str(stock_recalc_voucher.voucher_date) + " " + str(stock_recalc_voucher.voucher_time))			

		for record in stock_recalc_voucher.records:
            
			balance_qty = record.balance_qty
			balance_value = record.balance_value
			valuation_rate = record.valuation_rate
			qty_in = record.qty_in
			incoming_rate = record.incoming_rate
			qty_out = record.qty_out
			outgoing_rate = record.outgoing_rate			
			

			stock_ledger_items = frappe.get_list('Stock Ledger',{'item':record.item,
			'warehouse':record.warehouse, 'posting_date':['>', posting_date_time]}, 'name',order_by='posting_date')
   
			# Scenario 1- PUrchase Invoice - current row cancelled. For this assigned previous stock ledger balance to 'Stock Recalculate Voucher'

			for sl_name in stock_ledger_items:
				sl = frappe.get_doc('Stock Ledger', sl_name)
				print(sl)
				
				if(sl.voucher == "Delivery Note"):
					balance_qty = balance_qty - sl.qty_out
					balance_value = balance_qty * valuation_rate
				
				if (sl.voucher == "Purchase Invoice"):
					balance_qty = balance_qty + sl.qty_in
					balance_value = balance_value  + (sl.qty_in * sl.incoming_rate)
					if(balance_qty!=0): #Avoid divisible by zero
						valuation_rate = balance_value/ balance_qty						
				
				sl.balance_qty = balance_qty
				sl.balance_value = balance_value
				sl.valuation_rate = valuation_rate
				
				sl.save()
    
			if frappe.db.exists('Stock Balance', {'item':record.item,'warehouse': record.warehouse}):    
				frappe.db.delete('Stock Balance',{'item': record.item, 'warehouse': record.warehouse} )

			new_stock_balance = frappe.new_doc('Stock Balance')	
			new_stock_balance.item = record.item
			new_stock_balance.unit = record.unit
			new_stock_balance.warehouse = record.warehouse
			new_stock_balance.stock_qty = balance_qty
			new_stock_balance.stock_value = balance_value
			new_stock_balance.valuation_rate = valuation_rate

			new_stock_balance.insert()

			item_name = frappe.get_value("Item", record.item,['item_name'])
			self.update_item_stock_balance(item_name)					

		stock_recalc_voucher.status = 'Completed'
		stock_recalc_voucher.end_time = now()
		stock_recalc_voucher.save()

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
		gl_doc.aginst_account = self.supplier
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
		gl_doc.insert()

		# Round Off
	
	
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


	