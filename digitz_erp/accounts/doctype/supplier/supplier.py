# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Supplier(Document):	
	
	def before_save(self):
		self.validate_globals()	

	
	def validate_globals(self):
		
		global_settings = frappe.db.get_single_value("Global Settings","default_company")
		if not global_settings:
			frappe.throw('Default companuy is not configured in the Global Settings!.')			

	# def after_insert(self):
	# 	doc = frappe.get_doc('doctype':'Account',
	# 				'account_name': self.Supplier_name

	# 	)


		
    
	
