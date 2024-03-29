# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class StockLedger(Document):
    
	def on_update(self):
     
		# If the user attempts to save a stock ledger with a datetime before the 'Stock Repost' record's datetime, means the stock repost already happened on the datetime. Need to find out the previous stock ledger for the user saving stock ledger and update to 'Stock Repost' so that it can be repost again from that stock ledger
       
		stock_repost_doc = frappe.get_doc("Stock Repost")  		

		posting_date_dt = getdate(self.posting_date)
		last_processed_posting_date_dt = getdate(stock_repost_doc.last_processed_posting_date)
		
		if posting_date_dt < last_processed_posting_date_dt:
			previous_stock_ledger_for_the_posting_date = frappe.db.get_value('Stock Ledger', 
																				{'warehouse': self.warehouse, 'posting_date': ('<', posting_date_dt)},
																				['name', 'posting_date'],
																				order_by='posting_date desc', 
																				as_dict=True)
			
			if previous_stock_ledger_for_the_posting_date:
				# Correctly update the stock_repost_doc fields
				stock_repost_doc.last_processed_stock_ledger = previous_stock_ledger_for_the_posting_date['name']
				stock_repost_doc.last_processed_posting_date = previous_stock_ledger_for_the_posting_date['posting_date']
				stock_repost_doc.save()
			
   
			

		
  
     
