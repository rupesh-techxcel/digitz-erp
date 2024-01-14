# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from datetime import datetime
from frappe.model.document import Document
from frappe.utils.data import now
from datetime import datetime,timedelta
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_item_stock_balance
from digitz_erp.api.document_posting_status_api import init_document_posting_status, update_posting_status

class StockTransfer(Document):
    
	def Voucher_In_The_Same_Time(self):
		possible_invalid= frappe.db.count('Stock Transfer', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time]})
		return possible_invalid

	def Set_Posting_Time_To_Next_Second(self):
		datetime_object = datetime.strptime(str(self.posting_time), '%H:%M:%S')

		# Add one second to the datetime object
		new_datetime = datetime_object + timedelta(seconds=1)

		# Extract the new time as a string
		self.posting_time = new_datetime.strftime('%H:%M:%S')
  
	def before_validate(self):
			
		if(self.Voucher_In_The_Same_Time()):
						
			self.Set_Posting_Time_To_Next_Second()

			if(self.Voucher_In_The_Same_Time()):
				self.Set_Posting_Time_To_Next_Second()				
				
				if(self.Voucher_In_The_Same_Time()):
					self.Set_Posting_Time_To_Next_Second()
					
					if(self.Voucher_In_The_Same_Time()):
						frappe.throw("Voucher with same time already exists.") 
	
		for docitem in self.items:	
			if(not docitem.source_warehouse):
				docitem.source_warehouse = self.source_warehouse
			if(not docitem.target_warehouse):
				docitem.target_warehouse = self.target_warehouse
        
	def on_submit(self):    
		init_document_posting_status(self.doctype, self.name)
  
		turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

		if(frappe.session.user == "Administrator" and turn_off_background_job):
			self.do_postings_on_submit()		
		else:
			print("do_postings_on_submit_enqueue started")
			frappe.enqueue(self.do_postings_on_submit, queue="long")

	def do_postings_on_submit(self):
		self.add_stock_transfer()
		update_posting_status(self.doctype, self.name, 'posting_status','Completed')
 
	def add_stock_transfer(self):
     
		# Stock movement is considering the valuations independently with the warhouses. That means the balance value is 
		# calculating based on the previous stock in the source warehouse and target warehouse seperately
		     		
		stock_recalc_voucher_for_source = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher_for_source.voucher = 'Stock Transfer'
		stock_recalc_voucher_for_source.voucher_no = self.name
		stock_recalc_voucher_for_source.voucher_date = self.posting_date
		stock_recalc_voucher_for_source.voucher_time = self.posting_time
		stock_recalc_voucher_for_source.status = 'Not Started'
		stock_recalc_voucher_for_source.source_action = "Stock Transfer"
  
		stock_recalc_voucher_for_target = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher_for_target.voucher = 'Stock Transfer'
		stock_recalc_voucher_for_target.voucher_no = self.name
		stock_recalc_voucher_for_target.voucher_date = self.posting_date
		stock_recalc_voucher_for_target.voucher_time = self.posting_time
		stock_recalc_voucher_for_target.status = 'Not Started'
		stock_recalc_voucher_for_target.source_action = "Stock Transfer"
		
		more_records_for_source = 0
		more_records_for_target = 0
  
		default_company = frappe.db.get_single_value("Global Settings",'default_company')
  
		print(default_company)

		allow_negative_stock = frappe.get_value("Company",default_company,['allow_negative_stock'])
		
		if not allow_negative_stock:
			allow_negative_stock = False
		
		posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))  		
		for docitem in self.items:
      
			# Source warehouse item      
			more_records_count_for_item_for_source = frappe.db.count('Stock Ledger',{'item':docitem.item,
				'warehouse':docitem.source_warehouse, 'posting_date':['>', posting_date_time]})
   
			more_records_for_source = more_records_for_source + more_records_count_for_item_for_source
			
			required_qty = docitem.qty_in_base_unit
   
			# Get valuation rate irrespective of the warehouses
			previous_stock_valuation_rate = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item],
																'posting_date':['<', posting_date_time]},['valuation_rate'],
							order_by='posting_date desc', as_dict=True)
   
			previous_stock_balance_in_source = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.source_warehouse]
			, 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
			order_by='posting_date desc', as_dict=True)   

			if(not previous_stock_balance_in_source and allow_negative_stock ==False): 
				frappe.throw("No stock exists for " + docitem.item )

			if(previous_stock_balance_in_source and previous_stock_balance_in_source.balance_qty < required_qty and allow_negative_stock == False):
				frappe.throw("Sufficiant qty does not exists for the item " + docitem.item + " Required Qty= " + str(required_qty) + " " +
				docitem.base_unit + "and available Qty= " + str(previous_stock_balance_in_source.balance_qty) + " " + docitem.base_unit)
				return

			change_in_stock_value = 0
			new_balance_qty = 0
			valuation_rate = 0
			new_balance_value = 0
   
			if not previous_stock_balance_in_source:
				new_balance_qty = new_balance_qty * -1
				valuation_rate = docitem.rate
				new_balance_value = new_balance_qty * valuation_rate
				change_in_stock_value = new_balance_value 
			else:
				new_balance_qty = previous_stock_balance_in_source.balance_qty - docitem.qty_in_base_unit
				valuation_rate = previous_stock_balance_in_source.valuation_rate
				new_balance_value = new_balance_qty * valuation_rate
				change_in_stock_value = new_balance_value - previous_stock_balance_in_source.balance_value

			new_stock_ledger_source = frappe.new_doc("Stock Ledger")
			new_stock_ledger_source.item = docitem.item
			new_stock_ledger_source.warehouse = docitem.source_warehouse
			new_stock_ledger_source.posting_date = posting_date_time

			new_stock_ledger_source.qty_out = docitem.qty_in_base_unit
			new_stock_ledger_source.outgoing_rate = docitem.rate_in_base_unit
			new_stock_ledger_source.unit = docitem.base_unit
			new_stock_ledger_source.valuation_rate = valuation_rate
			new_stock_ledger_source.balance_qty = new_balance_qty
			new_stock_ledger_source.balance_value = new_balance_value
			new_stock_ledger_source.voucher = "Stock Transfer"
			new_stock_ledger_source.voucher_no = self.name
			new_stock_ledger_source.source = "Stock Transfer Item"
			new_stock_ledger_source.source_document_id = docitem.name
			new_stock_ledger_source.change_in_stock_value = change_in_stock_value
			new_stock_ledger_source.insert()

			if(more_records_count_for_item_for_source>0):				
				stock_recalc_voucher_for_source.append('records',{'item': docitem.item, 'warehouse': docitem.source_warehouse, 'base_stock_ledger': new_stock_ledger_source.name
																	})
			else:				  
				if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.source_warehouse}):    
					frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.source_warehouse} )
					
				new_stock_balance = frappe.new_doc('Stock Balance')	
				new_stock_balance.item = docitem.item
				new_stock_balance.unit = docitem.base_unit
				new_stock_balance.warehouse = docitem.source_warehouse
				new_stock_balance.stock_qty = new_balance_qty
				new_stock_balance.stock_value = new_balance_value
				new_stock_balance.valuation_rate = valuation_rate

				new_stock_balance.insert()

				# item_name = frappe.get_value("Item", docitem.item,['item_name'])
				update_item_stock_balance(docitem.item)	

			more_records_count_for_item_for_target = frappe.db.count('Stock Ledger',{'item':docitem.item,
				'warehouse':docitem.target_warehouse, 'posting_date':['>', posting_date_time]})
   
			more_records_for_target = more_records_for_target + more_records_count_for_item_for_target

			previous_stock_balance_in_target = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.target_warehouse]
			, 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
			order_by='posting_date desc', as_dict=True)

			preivous_balance_qty = 0
			previous_balance_value = 0
			# valuation_rate is now same as the source stock valuation_rate
			if(previous_stock_balance_in_target):
				preivous_balance_qty = previous_stock_balance_in_target.balance_qty
				previous_balance_value = previous_stock_balance_in_target.balance_value
				# Change valuation_rate as per target warehouse
				valuation_rate = previous_stock_balance_in_target.valuation_rate
      
			new_balance_qty = preivous_balance_qty + docitem.qty_in_base_unit
			
			# No change in valuation_rate
			
			new_balance_value = new_balance_qty * valuation_rate
   
			change_in_stock_value = new_balance_value - previous_balance_value
   
			new_stock_ledger_target = frappe.new_doc("Stock Ledger")
			new_stock_ledger_target.item = docitem.item
			new_stock_ledger_target.item_name = docitem.item_name
			new_stock_ledger_target.warehouse = docitem.target_warehouse
			new_stock_ledger_target.posting_date = posting_date_time

			new_stock_ledger_target.qty_in = docitem.qty_in_base_unit
			new_stock_ledger_target.incoming_rate = docitem.rate_in_base_unit
			new_stock_ledger_target.unit = docitem.base_unit
			new_stock_ledger_target.valuation_rate = valuation_rate
			new_stock_ledger_target.balance_qty = new_balance_qty
			new_stock_ledger_target.balance_value = new_balance_value
			new_stock_ledger_target.change_in_stock_value = change_in_stock_value
			new_stock_ledger_target.voucher = "Stock Transfer"
			new_stock_ledger_target.voucher_no = self.name
			new_stock_ledger_target.source = "Stock Transfer Item"
			new_stock_ledger_target.source_document_id = docitem.name
			new_stock_ledger_target.insert()
	
			if(more_records_count_for_item_for_target>0):				
				stock_recalc_voucher_for_source.append('records',{'item': docitem.item,'warehouse': docitem.target_warehouse,'base_stock_ledger': new_stock_ledger_target.name																	})
			else:
				if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.target_warehouse}):    
					frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.target_warehouse} )
					
				new_stock_balance = frappe.new_doc('Stock Balance')	
				new_stock_balance.item = docitem.item
				new_stock_balance.item_name = docitem.item_name
				new_stock_balance.unit = docitem.base_unit
				new_stock_balance.warehouse = docitem.target_warehouse
				new_stock_balance.stock_qty = new_balance_qty
				new_stock_balance.stock_value = new_balance_value
				new_stock_balance.valuation_rate = valuation_rate

				new_stock_balance.insert()

				update_item_stock_balance(docitem.item)	
    
		update_posting_status(self.doctype,self.name, 'stock_posted_time')
  
		print("stock_recalc_voucher_for_source")
		print(stock_recalc_voucher_for_source)
	
		print("stock_recalc_voucher_for_target")
		print(stock_recalc_voucher_for_target)  
  
		if(more_records_for_source>0):
			update_posting_status(self.doctype,self.name, 'stock_recalc_required', True)
			stock_recalc_voucher_for_source.insert()
			print("before recalculate stock ledgers for source")
			recalculate_stock_ledgers(stock_recalc_voucher_for_source, self.posting_date, self.posting_time)
			update_posting_status(self.doctype, self.name, 'stock_reclc_time')
   
		if(more_records_for_target>0):
				stock_recalc_voucher_for_target.insert()
				print("before recalculate stock ledgers for target")    
				recalculate_stock_ledgers(stock_recalc_voucher_for_target, self.posting_date, self.posting_time)
	
	def on_cancel(self):   
     
		update_posting_status(self.doctype,self.name, "posting_status", "Cancel Pending")
  
		turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

		if(frappe.session.user == "Administrator" and turn_off_background_job): 
			self.cancel_stock_transfer()		
		else:
			frappe.enqueue(self.cancel_stock_transfer, queue="long" )
		     
	def cancel_stock_transfer(self):
		update_posting_status(self.doctype,self.name, "posting_status", "Completed")	
  
	def do_cancel_stock_transfer(self):
		
		# Insert record to 'Stock Recalculate Voucher' doc
		stock_recalc_voucher_source_wh = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher_source_wh.voucher = 'Stock Transfer'
		stock_recalc_voucher_source_wh.voucher_no = self.name
		stock_recalc_voucher_source_wh.voucher_date = self.posting_date
		stock_recalc_voucher_source_wh.voucher_time = self.posting_time
		stock_recalc_voucher_source_wh.status = 'Not Started'
		stock_recalc_voucher_source_wh.source_action = "Cancel"
		
		stock_recalc_voucher_target_wh = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher_target_wh.voucher = 'Stock Transfer'
		stock_recalc_voucher_target_wh.voucher_no = self.name
		stock_recalc_voucher_target_wh.voucher_date = self.posting_date
		stock_recalc_voucher_target_wh.voucher_time = self.posting_time
		stock_recalc_voucher_target_wh.status = 'Not Started'
		stock_recalc_voucher_target_wh.source_action = "Cancel"
  
		posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))					

		more_records_source_wh = 0
		more_records_target_wh = 0

		# Iterate on each item from the cancelling purchase invoice
		for docitem in self.items:	
			more_records_for_item_source_wh = frappe.db.count('Stock Ledger',{'item':docitem.item,
				'warehouse':docitem.source_warehouse, 'posting_date':['>', posting_date_time]})

			more_records_source_wh = more_records_source_wh + more_records_for_item_source_wh

			previous_stock_ledger_name_source = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.source_warehouse]
						, 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)

			# If any items in the collection has more records
			if(more_records_for_item_source_wh>0):
				
				# stock_ledger_items = frappe.get_list('Stock Ledger',{'item':docitem.item,
				# 'warehouse':docitem.source_warehouse, 'posting_date':['>', posting_date_time]}, ['name','qty_in','qty_out','voucher','balance_qty','voucher_no'],order_by='posting_date')

				# if(stock_ledger_items):

				# 	qty_cancelled = docitem.qty_in_base_unit
				# 	# Loop to verify the sufficiant quantity
				# 	for sl in stock_ledger_items:					
				# 		# On each line if outgoing qty + balance_qty (qty before outgonig) is more than the cancelling qty
				# 		if(sl.qty_out>0 and qty_cancelled> sl.qty_out+ sl.balance_qty):
				# 			frappe.throw("Cancelling the stock reconciliation is prevented due to sufficiant quantity not available for " + docitem.item +
				# 		" to fulfil the voucher " + sl.voucher_no)
			
				if previous_stock_ledger_name_source:					
					stock_recalc_voucher_source_wh.append('records',{'item': docitem.item, 
															'warehouse': docitem.source_warehouse,
															'base_stock_ledger': previous_stock_ledger_name_source 
															})
				else:
					stock_recalc_voucher_source_wh.append('records',{'item': docitem.item, 
															'warehouse': docitem.source_warehouse,
															'base_stock_ledger': "No Previous Ledger"
															})
			else:
		
				stock_balance = frappe.get_value('Stock Balance', {'item':docitem.item, 'warehouse':docitem.source_warehouse}, ['name'] )
				balance_qty =0
				balance_value =0
				valuation_rate  = 0

				if previous_stock_ledger_name_source:
					previous_stock_ledger = frappe.get_doc('Stock Ledger',previous_stock_ledger_name_source) 
					balance_qty = previous_stock_ledger.balance_qty
					balance_value = previous_stock_ledger.balance_value
					valuation_rate = previous_stock_ledger.valuation_rate
		
				if(stock_balance):
					stock_balance_for_item = frappe.get_doc('Stock Balance',stock_balance) 
					# Add qty because of balance increasing due to cancellation of delivery note
					stock_balance_for_item.stock_qty = balance_qty
					stock_balance_for_item.stock_value = balance_value
					stock_balance_for_item.valuation_rate = valuation_rate
					stock_balance_for_item.save()                    
				else:
					stock_balance_for_item = frappe.new_doc("Stock Balance")
					stock_balance_for_item.item = docitem.item
					stock_balance_for_item.warehouse = docitem.source_warehouse
					stock_balance_for_item.stock_qty = balance_qty
					stock_balance_for_item.stock_value = balance_value
					stock_balance_for_item.valuation_rate = valuation_rate
					stock_balance_for_item.insert()                    

				# item_name = frappe.get_value("Item", docitem.item,['item_name'])
				update_item_stock_balance(docitem.item)	
			
   			# Target w/h
			
			more_records_for_item_target_wh = frappe.db.count('Stock Ledger',{'item':docitem.item,
				'warehouse':docitem.target_warehouse, 'posting_date':['>', posting_date_time]})

			more_records_target_wh = more_records_target_wh + more_records_for_item_target_wh

			previous_stock_ledger_name_target = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.target_warehouse]
						, 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)

			# If any items in the collection has more records
			if(more_records_for_item_target_wh>0):
				
				stock_ledger_items = frappe.get_list('Stock Ledger',{'item':docitem.item,
				'warehouse':docitem.target_warehouse, 'posting_date':['>', posting_date_time]}, ['name','qty_in','qty_out','voucher','balance_qty','voucher_no'],order_by='posting_date')

				if(stock_ledger_items):

					qty_cancelled = docitem.qty_in_base_unit
					# Loop to verify the sufficiant quantity
					for sl in stock_ledger_items:					
						# On each line if outgoing qty + balance_qty (qty before outgonig) is more than the cancelling qty
						if(sl.qty_out>0 and qty_cancelled> sl.qty_out+ sl.balance_qty):
							frappe.throw("Cancelling the stock reconciliation is prevented due to sufficiant quantity not available for " + docitem.item +
						" to fulfil the voucher " + sl.voucher_no)
			
				if previous_stock_ledger_name_target:					
					stock_recalc_voucher_target_wh.append('records',{'item': docitem.item, 
															'warehouse': docitem.target_warehouse,
															'base_stock_ledger': previous_stock_ledger_name_target 
															})
				else:
					stock_recalc_voucher_target_wh.append('records',{'item': docitem.item, 
															'warehouse': docitem.target_warehouse,
															'base_stock_ledger': "No Previous Ledger"
															})
			else:
		
				stock_balance = frappe.get_value('Stock Balance', {'item':docitem.item, 'warehouse':docitem.target_warehouse}, ['name'] )
				balance_qty =0
				balance_value =0
				valuation_rate  = 0

				if previous_stock_ledger_name_target:
					previous_stock_ledger = frappe.get_doc('Stock Ledger',previous_stock_ledger_name_target) 
					balance_qty = previous_stock_ledger.balance_qty
					balance_value = previous_stock_ledger.balance_value
					valuation_rate = previous_stock_ledger.valuation_rate
     
				if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
					frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse} )
		
				unit = frappe.get_value("Item", docitem.item,['base_unit'])     
				stock_balance_for_item = frappe.new_doc("Stock Balance")
				stock_balance_for_item.item = docitem.item
				stock_balance_for_item.unit = unit
				stock_balance_for_item.warehouse = docitem.target_warehouse
				stock_balance_for_item.stock_qty = balance_qty
				stock_balance_for_item.stock_value = balance_value
				stock_balance_for_item.valuation_rate = valuation_rate
				stock_balance_for_item.insert()                    

				# item_name = frappe.get_value("Item", docitem.item,['item_name'])
				update_item_stock_balance(docitem.item)	

		update_posting_status(self.doctype,self.name, 'stock_posted_on_cancel_time')
  
		if(more_records_source_wh>0):
			update_posting_status(self.doctype,self.name, 'stock_recalc_required_on_cancel', True)   
			stock_recalc_voucher_source_wh.insert()   
			recalculate_stock_ledgers(stock_recalc_voucher_source_wh, self.posting_date, self.posting_time)
			update_posting_status(self.doctype, self.name, 'stock_recalc_on_cancel_time')
   
		if(more_records_target_wh>0):
			update_posting_status(self.doctype,self.name, 'stock_recalc_required_on_cancel', True)
			stock_recalc_voucher_target_wh.insert()
			recalculate_stock_ledgers(stock_recalc_voucher_target_wh, self.posting_date, self.posting_time)
			update_posting_status(self.doctype, self.name, 'stock_recalc_on_cancel_time')
   
		frappe.db.delete("Stock Ledger",
				{"voucher": "Stock Transfer",
					"voucher_no":self.name
				})		