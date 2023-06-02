# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now
from frappe.model.document import Document
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_item_stock_balance
from digitz_erp.api.purchase_order_api import check_and_update_purchase_order_status
class PurchaseInvoice(Document):

	def before_submit(self):		

		possible_invalid= frappe.db.count('Purchase Invoice', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time], 'docstatus':['=', 1]})				
		# When duplicating the voucher user may not remember to change the date and time. So do not allow to save the voucher to be 
		# posted on the same time with any of the existing vouchers. This also avoid invalid selection to calculate moving average value
		# Also in add_stock_for_purchase_receipt method only checking for < date_time in order avoid difficulty to get exact last record 
		# to get balance qty and balance value.
		

		if(possible_invalid >0):			
			frappe.throw("There is another purchase invoice exist with the same date and time. Please correct the date and time.")

		self.insert_gl_records()
		self.insert_payment_postings()		
		self.add_stock_for_purchase_receipt()
	
  
	def before_save(self):	
		print("before_save")
		if self.purchase_order:			
			self.update_purchase_order_quantities_before_save()	
			check_and_update_purchase_order_status(self.purchase_order)
   
	def before_cancel(self):
		print("before_cancel")
		if self.purchase_order:			
			self.update_purchase_order_quantities_before_cancel()
			check_and_update_purchase_order_status(self.purchase_order)
   
	def update_purchase_order_quantities_before_cancel(self):
		
		for item in self.items:
			
			print("item")
			print(item.item)

			item_in_purchase_order= frappe.get_value("Purchase Order Item", {'item':item.item, 'display_name':item.display_name},['name'] )
			purchase_order_item = frappe.get_doc("Purchase Order Item", item_in_purchase_order)
			purchase_order_item.qty_purchased = item.qty

			total_used_qty = frappe.db.sql(""" SELECT SUM(qty) as total_used_qty from `tabPurchase Invoice Item` pinvi JOIN `tabPurchase Invoice` pinv on pinv.name= pinvi.parent WHERE pinvi.item=%s AND pinvi.display_name=%s AND pinv.purchase_order=%s AND pinv.name !=%s""",(item.item,item.display_name, self.purchase_order,self.name))[0][0]     
								
			if(total_used_qty):
				purchase_order_item.qty_purchased =  total_used_qty
			else:
				purchase_order_item.qty_purchased =  0
		
			purchase_order_item.save()
   
	def update_purchase_order_quantities_before_save(self):
     
		# Get the purchase order and verify the qty purchased against each line items
		purchase_order = frappe.get_doc("Purchase Order", self.purchase_order)
		
		for item in purchase_order.items:
   
			item.qty_purchased = 0
   
			for pi_item in self.items:
       
       
				if(pi_item.item == item.item and pi_item.display_name == item.display_name):
					
					item.qty_purchased = pi_item.qty
      			
			total_used_qty_not_in_this_pi = frappe.db.sql(""" SELECT SUM(qty) as total_used_qty from `tabPurchase Invoice Item` pinvi JOIN `tabPurchase Invoice` pinv on pinv.name= pinvi.parent WHERE pinvi.item=%s AND pinvi.display_name=%s AND pinv.purchase_order=%s AND pinv.name !=%s""",(item.item,item.display_name, self.purchase_order,self.name))[0][0]     
   
			if total_used_qty_not_in_this_pi:
				item.qty_purchased = item.qty_purchased + total_used_qty_not_in_this_pi      
	
		purchase_order.save()

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

			print("Item")
			print(docitem.item)
			print("Qty")
			print(new_balance_qty)
			print("Value")
			print(new_balance_value)
   
			# Assigned current stock value to use if previous values not exist
			change_in_stock_value = new_balance_value
			print("Change in stock value")
			print(change_in_stock_value)

			print(posting_date_time)

			# posting_date<= consider because to take the dates with in the same minute								
			# dbCount = frappe.db.count('Stock Ledger',{'item_code': ['=', docitem.item_code],'warehouse':['=', docitem.warehouse], 'posting_date':['<=', posting_date_time]})
			dbCount = frappe.db.count('Stock Ledger',{'item_code': ['=', docitem.item_code],'warehouse':['=', docitem.warehouse], 
                                             'posting_date': ['<', posting_date_time]})
			
			if(dbCount>0):
       
				print("dbCount")
				print(dbCount)    

				# Find out the balance value and valuation rate. Here recalculates the total balance value and valuation rate
				# from the balance qty in the existing rows x actual incoming rate

				last_stock_ledger = frappe.db.get_value('Stock Ledger', {'item_code': ['=', docitem.item_code], 'warehouse':['=', docitem.warehouse], 
                                                        'posting_date':['<', posting_date_time]},
                                            ['balance_qty', 'balance_value', 'valuation_rate'],order_by='posting_date desc', as_dict=True)				
    
				new_balance_qty = new_balance_qty + last_stock_ledger.balance_qty			
			
				new_balance_value = new_balance_value + (last_stock_ledger.balance_value)


				if new_balance_qty!=0:
					valuation_rate = new_balance_value/new_balance_qty	
     
				change_in_stock_value = new_balance_value - last_stock_ledger.balance_value
			
		
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
			new_stock_ledger.change_in_stock_value = change_in_stock_value
			new_stock_ledger.voucher = "Purchase Invoice"
			new_stock_ledger.voucher_no = self.name
			new_stock_ledger.source = "Purchase Invoice Item"
			new_stock_ledger.source_document_id = docitem.name
			new_stock_ledger.insert()
   
			print("Change in stock value 2nd")
			print(change_in_stock_value)
   
			sl = frappe.get_doc("Stock Ledger", new_stock_ledger.name)
			print("from sl")
			print(sl.change_in_stock_value)
			
   
			# If no more records for the item, update balances. otherwise it updates in the flow
			if more_records_count_for_item==0: 
	
				print("more_records_count_for_item==0" + docitem.item)

				if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):    
					frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse})

				new_stock_balance = frappe.new_doc('Stock Balance')	
				new_stock_balance.item = docitem.item
				new_stock_balance.unit = docitem.unit
				new_stock_balance.warehouse = docitem.warehouse
				new_stock_balance.stock_qty = new_balance_qty
				new_stock_balance.stock_value = new_balance_value
				new_stock_balance.valuation_rate = valuation_rate
			
				new_stock_balance.insert()
				print("new stock balance qty")
				print(new_balance_qty)
				
				item_name = frappe.get_value("Item", docitem.item,['item_name'])
				update_item_stock_balance(item_name)
	
			else:
				stock_recalc_voucher.append('records',{'item': docitem.item, 
    													'warehouse': docitem.warehouse,
                                                        'base_stock_ledger': new_stock_ledger.name 
                                                            })
		if(more_records>0):
			stock_recalc_voucher.insert()			
			recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)

	def on_cancel(self):        	
		self.cancel_purchase()
			
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
    
				item_name = frappe.get_value("Item", docitem.item,['item_name'])
				update_item_stock_balance(item_name)	
		
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
    
	# def update_item_stock_balance(self, item):
     
	# 	print(item)

	# 	item_balances_in_warehouses = frappe.get_list('Stock Balance',{'item': item},['stock_qty','stock_value'])
  
	# 	balance_stock_qty = 0
	# 	balance_stock_value = 0

	# 	if(item_balances_in_warehouses):
	# 		for item_stock in item_balances_in_warehouses:
       
	# 			if item_stock.stock_qty:
	# 				balance_stock_qty = balance_stock_qty + item_stock.stock_qty

	# 			if item_stock.stock_value:
	# 				balance_stock_value = balance_stock_value + item_stock.stock_value
	
	# 	item_to_update = frappe.get_doc('Item', item)	
			
	# 	if(not item_to_update.stock_balance):				
	# 		item_to_update.stock_balance = 0
	# 		item_to_update.stock_value = 0
	# 	item_to_update.stock_balance = balance_stock_qty
	# 	item_to_update.stock_value = balance_stock_value
			
	# 	item_to_update.save()	
	
	# def recalculate_stock_ledgers(self,stock_recalc_voucher):
        
	# 	posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))  		

	# 	for record in stock_recalc_voucher.records:
            
	# 		new_balance_qty = 0
	# 		new_balance_value = 0
	# 		new_valuation_rate = 0
	# 		if record.base_stock_ledger != "No Previous Ledger":
	# 			base_stock_ledger = frappe.get_doc('Stock Ledger', record.base_stock_ledger)				
	# 			new_balance_qty = base_stock_ledger.balance_qty 
	# 			new_balance_value = base_stock_ledger.balance_value
	# 			new_valuation_rate = base_stock_ledger.valuation_rate
			
	# 		next_stock_ledgers = frappe.get_list('Stock Ledger',{'item':record.item,
	# 		'warehouse':record.warehouse, 'posting_date':['>', posting_date_time]}, 'name',order_by='posting_date')

	# 		# Scenario 1- PUrchase Invoice - current row cancelled. For this assigned previous stock ledger balance to 'Stock Recalculate Voucher'

	# 		for sl_name in next_stock_ledgers:
				
	# 			sl = frappe.get_doc('Stock Ledger', sl_name)          
	# 			qty_in = 0
	# 			qty_out = 0
				
	# 			# Exit the loop if there is a manual stock entry, since the manual stock entry is considered as corrected stock entry
	# 			if(sl.voucher == "Stock Reconciliation"):
	# 				if(sl.balance_qty > new_balance_qty):
	# 					qty_in = sl.balance_qty - new_balance_qty
	# 				else:
	# 					qty_out = new_balance_qty -sl.balance_qty                    
				
	# 				sl.qty_in = qty_in
	# 				sl.qty_out = qty_out
					
	# 				# Previous stock value difference
	# 				previous_balance_value = new_balance_value #Assign before change        
	# 				sl.change_in_stock_value =   (sl.balance_value - previous_balance_value) 
										
	# 				new_valuation_rate = sl.valuation_rate                    
	# 				new_balance_qty = sl.balance_qty
	# 				new_balance_value = sl.balance_value                    
					
	# 				# Once qty adjusted exit for next item, since after manual entry subsequent entries are not considered
	# 				sl.save()
	# 				break;
				
	# 			if(sl.voucher == "Delivery Note"):
	# 				previous_balance_value = new_balance_value #Assign before change    
	# 				new_balance_qty = new_balance_qty - sl.qty_out
	# 				new_balance_value = new_balance_qty * new_valuation_rate
	# 				change_in_stock_value = new_balance_value - previous_balance_value
	# 				sl.change_in_stock_value = change_in_stock_value
					
	# 			if(new_balance_qty<0):
	# 				frappe.throw("Stock availability is not sufficiant to make thistransaction, the delivery note " + sl.voucher_no + " cannot be fulfilled.")
										
	# 			if (sl.voucher == "Purchase Invoice"):
	# 				previous_balance_value = new_balance_value #Assign before change 
	# 				new_balance_qty = new_balance_qty + sl.qty_in
	# 				new_balance_value = new_balance_value  + (sl.qty_in * sl.incoming_rate)
	# 				change_in_stock_value = new_balance_value - previous_balance_value
	# 				sl.change_in_stock_value = change_in_stock_value
		
	# 				if(new_balance_qty!=0): #Avoid divisible by zero
	# 					new_valuation_rate = new_balance_value/ new_balance_qty
				
	# 			sl.balance_qty = new_balance_qty
	# 			sl.balance_value = new_balance_value
	# 			sl.valuation_rate = new_valuation_rate				
	# 			sl.save()

	# 		if frappe.db.exists('Stock Balance', {'item':record.item,'warehouse': record.warehouse}):    
	# 			frappe.db.delete('Stock Balance',{'item': record.item, 'warehouse': record.warehouse} )

	# 		item_name,unit = frappe.get_value("Item", record.item,['item_name','base_unit'])
	# 		new_stock_balance = frappe.new_doc('Stock Balance')	
	# 		new_stock_balance.item = record.item
	# 		new_stock_balance.unit = unit
	# 		new_stock_balance.warehouse = record.warehouse
	# 		new_stock_balance.stock_qty = new_balance_qty
	# 		new_stock_balance.stock_value = new_balance_value
	# 		new_stock_balance.valuation_rate = new_valuation_rate

	# 		new_stock_balance.insert()

			
	# 		self.update_item_stock_balance(item_name)					

	# 	stock_recalc_voucher.status = 'Completed'
	# 	stock_recalc_voucher.end_time = now()
	# 	stock_recalc_voucher.save()

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


	