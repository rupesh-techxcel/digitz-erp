# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Item(Document):
		
	def update_standard_buying_price(self):	

		if not frappe.db.exists("Price List Item",{'item': self.item_name, 'parent':'Standard Buying'}):				
			doc = frappe.get_doc("Price List","Standard Buying")		
			row = doc.append('items', {'item': self.item_name , 'price': self.standard_buying_price})
			doc.save()
			frappe.msgprint("Added the price to Standard Buying Price List")
		else:			
			frappe.db.set_value("Price List Item",{'item': self.item_name, 'parent': 'Standard Buying'},
		 						{'price' : self.standard_buying_price})
			frappe.msgprint("Updated the price to Standard Buying Price List")	
		
	def update_standard_selling_price(self):

		if not frappe.db.exists("Price List Item",{'item': self.item_name, 'parent':'Standard Selling'}):				
			doc = frappe.get_doc("Price List","Standard Selling")		
			row = doc.append('items', {'item': self.item_name , 'price': self.standard_selling_price})
			doc.save()
			frappe.msgprint("Added the price to Standard Selling Price List")
		else:			
			frappe.db.set_value("Price List Item",{'item': self.item_name, 'parent': 'Standard Selling'},
		 						{'price' : self.standard_selling_price})
			frappe.msgprint("Updated the price to Standard Selling Price List")

	def delete_standard_buying_price(self):	
		if frappe.db.exists("Price List Item",{'item': self.item_name, 'parent':'Standard Buying'}):
			frappe.db.delete("Price List Item", {"parent":"Standard Buying", "item": self.item_name})				
			frappe.msgprint("Deleted Standard Buying Price for price zero.")
	
	def delete_standard_selling_price(self):	
		if frappe.db.exists("Price List Item",{'item': self.item_name, 'parent':'Standard Selling'}):
			frappe.db.delete("Price List Item", {"parent":"Standard Selling", "item": self.item_name})				
			frappe.msgprint("Deleted Standard Selling Price for price zero.")	
		
	def before_save(self):

		# Since data is not already saved for the first time, checking the condnition, entry does not exist
		# In that case after_insert will work
		if frappe.db.exists("Item",{'item': self.item_name}):			
			if self.standard_buying_price == 0:
				self.delete_standard_buying_price()		
			else:
				self.update_standard_buying_price()
		
			if self.standard_selling_price == 0:
				self.delete_standard_selling_price()		
			else:		
				self.update_standard_selling_price()			
	
	def after_insert(self):

		if not self.standard_buying_price == 0:
			self.update_standard_buying_price()
		
		if not self.standard_selling_price == 0:
			self.update_standard_selling_price()
