# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PriceList(Document):
	pass
	# def before_rename(dt,old):
	# 	print("before rename")
	# 	print(dt)
	# 	print(old)		
  
		# original_name = self.get_doc_before_save().get("name")
		# current_name = self.name
		# if original_name in ["Standard Selling", "Standard Buying"] and current_name not in ["Standard Selling", "Standard Buying"]:
		# 	frappe.throw("You are not allowed to modify this record.")