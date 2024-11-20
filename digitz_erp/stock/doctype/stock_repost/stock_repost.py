# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.stock_update import re_post_stock_ledgers
from datetime import date,datetime,timedelta,time
from datetime import date
import dateutil.parser

class StockRepost(Document):
    
	@frappe.whitelist()
	def stock_repost(self):        
		try:
			print("Stock repost starting..")
			re_post_stock_ledgers(show_alert=True)
			print("stock repost completed")
		except Exception as e:
			# Handle any other exception
			frappe.log_error(frappe.get_traceback(), 'Unexpected Error Occurred')
			# Inform the user or take other appropriate action
			frappe.msgprint(('An unexpected error occurred: {0}').format(str(e)))
		finally:
			pass

	
		
     
     
     

        