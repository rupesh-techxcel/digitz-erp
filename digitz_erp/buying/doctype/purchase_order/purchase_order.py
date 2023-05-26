# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now
from frappe.model.document import Document
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_item_stock_balance

class PurchaseOrder(Document):

	def before_submit(self):		

		possible_invalid= frappe.db.count('Purchase Order', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time], 'docstatus':['=', 1]})				
		# When duplicating the voucher user may not remember to change the date and time. So do not allow to save the voucher to be 
		# posted on the same time with any of the existing vouchers. This also avoid invalid selection to calculate moving average value
		# Also in add_stock_for_purchase_receipt method only checking for < date_time in order avoid difficulty to get exact last record 
		# to get balance qty and balance value.

		print(possible_invalid)

		if(possible_invalid >0):			
			frappe.throw("There is another Order invoice exist with the same date and time. Please correct the date and time.")
