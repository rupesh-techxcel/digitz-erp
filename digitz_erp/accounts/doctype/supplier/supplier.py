# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Supplier(Document):	
	
	def before_save(self):
		self.validate_globals()	

		address = self.address
		city =""
		
		if self.address !="":			
			city = "\n"	+ self.city
		else:
			city = self.city
			
		emirate =""
		if	self.emirate !="":
			emirate = "\n" + self.emirate

		country = ""
		if self.country !="":
			country = "\n" + self.country

		full_address = self.address  + city + emirate + country
		self.full_address = full_address

	
	def validate_globals(self):
		
		global_settings = frappe.db.get_single_value("Global Settings","default_company")
		if not global_settings:
			frappe.throw('Default companuy is not configured in the Global Settings!.')			

	# def after_insert(self):
	# 	doc = frappe.get_doc('doctype':'Account',
	# 				'account_name': self.Supplier_name

	# 	)


		
    
	
