# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now

class Supplier(Document):	
	
	# def on_update(self):	

	# 	self.validate_globals()	

	# 	address = self.address
	# 	city =""
		
	# 	if self.address !="":			
	# 		city = "\n"	+ self.city
	# 	else:
	# 		city = self.city
			
	# 	emirate =""
	# 	if	self.emirate !="":
	# 		emirate = "\n" + self.emirate

	# 	country = ""
	# 	if self.country !="":
	# 		country = "\n" + self.country

	# 	taxId = ""
		
	# 	if self.tax_id !="":
	# 		taxId = "\n" + "TRN No:" + self.tax_id
		
	# 	full_address = self.address  + city + emirate + country + taxId

	# 	self.full_address = full_address

	
	def validate_globals(self):
		
		global_settings = frappe.db.get_single_value("Global Settings","default_company")
		if not global_settings:
			frappe.throw('Default companuy is not configured in the Global Settings!.')			

	

		
    
	
