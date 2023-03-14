# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class CustomerAddress(Document):
	pass
	# def on_update(self):	

	# 	address_line1 = self.address_line_1
		

	# 	if not self.address_line_2: 
	# 		address_line2 = ""
	# 	else:
	# 		address_line2 = "\n" + self.address_line_2
		
	# 	area = "\n"	+ self.area		
			
	# 	emirate =""
	# 	if	self.emirate:
	# 		emirate = "\n" + self.emirate

	# 	country = ""
	# 	if not self.country:
	# 		country = "\n" + self.country

	# 	taxId = ""
		
	# 	full_address = address_line1 + address_line2  + area + emirate + country + taxId

	# 	self.full_address = full_address
	
