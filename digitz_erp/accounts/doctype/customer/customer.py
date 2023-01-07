# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class Customer(Document):


	def before_save(self):

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
