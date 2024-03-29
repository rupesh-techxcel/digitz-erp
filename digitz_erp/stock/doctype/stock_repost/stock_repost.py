# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.stock_update import re_post_stock_ledgers
from datetime import date,datetime,timedelta,time

class StockRepost(Document):
    
	@frappe.whitelist()
	def stock_repost(self):        
		try:
			re_post_stock_ledgers()
			print("stock repost completed")
		except Exception as e:
			# Handle any other exception
			frappe.log_error(frappe.get_traceback(), 'Unexpected Error Occurred')
			# Inform the user or take other appropriate action
			frappe.msgprint(('An unexpected error occurred: {0}').format(str(e)))
		finally:
			pass

	@frappe.whitelist()
	def do_repost(self):
		# Define start and end dates
		transaction_date = date(2023, 1, 1)
		end_date = date(2024, 3, 29)

		# Loop through each day in the range
		while transaction_date <= end_date:
			print(transaction_date)

			# List of document types to process
			doc_types = ['Purchase Invoice', 'Stock Reconciliation', 'Stock Transfer', 'Receipt Entry', 'Sales Invoice']

			for doc_type in doc_types:
				# Fetch documents for the current date and doc_type
				documents = frappe.db.sql(f"""
					SELECT name
					FROM `tab{doc_type}`
					WHERE docstatus = 0 AND posting_date = %s
					ORDER BY posting_date ASC, posting_time ASC
				""", (transaction_date,), as_dict=True)

				# Process each document
				for document in documents:
					doc = frappe.get_doc(doc_type, document.name)
					print(doc.name)

					# Special handling for Stock Reconciliation
					if doc_type == 'Stock Reconciliation':
						doc.purpose = "Stock Reconciliation"
						doc.save()
      
					if doc_type == 'Receipt Entry':
						doc.warehouse = 'Default Warehouse'
						doc.save()

					doc.submit()
     
			if transaction_date == end_date:
				break

			# Move to the next day
			transaction_date += timedelta(days=1)
   
		frappe.msgprint("Reposting completed.")
   


     
		
     
		
     
		
     
     
     

        