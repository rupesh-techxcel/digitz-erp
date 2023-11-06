# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import date

class ItemPrice(Document):
 
	def validate(self):
		
		print("from validate")

		if(self.from_date and self.to_date):

			existing_records = frappe.db.sql("""
			SELECT name
			FROM `tabItem Price`
			WHERE item=%(item)s AND price_list=%(price_list)s AND from_date IS NOT NULL AND to_date IS NOT NULL AND name != %(name)s
			""", {"item": self.item, "price_list": self.price_list, "name": self.name}, as_dict=1)
   
			print("existing_records")
			print(existing_records)
   
			for record_item_price in existing_records:
       
				record = frappe.get_doc("Item Price", record_item_price.name)
    
				print("record")    
				print(record)
    
				print("record from_date")    
				print(record.from_date)
				
				   			        
				if(record.from_date and record.to_date):
        	
					if ((self.from_date <= record.to_date and self.to_date >= record.from_date)
				or (self.from_date <= record.from_date and self.to_date >= record.from_date)
				or (self.from_date <= record.to_date and self.to_date >= record.to_date)
				):
						frappe.throw("Another ItemPrice with the same item/pricelist has overlapping date range.")
					
				# 	if ((date.fromisoformat(self.from_date) <= record.to_date and date.fromisoformat(self.to_date) >= record.from_date)
				# or (date.fromisoformat(self.from_date) <= record.from_date and date.fromisoformat(self.to_date) >= record.from_date)
				# or (date.fromisoformat(self.from_date) <= record.to_date and date.fromisoformat(self.to_date) >= record.to_date)
				# ):
				# 		frappe.throw("Another ItemPrice with the same item/pricelist has overlapping date range.")
		else:
   
			prices = frappe.db.sql("""
				SELECT name
				FROM `tabItem Price`
				WHERE item=%(item)s AND price_list=%(price_list)s AND from_date IS NULL AND to_date IS NULL AND name != %(name)s
			""", {"item": self.item, "price_list": self.price_list, "name": self.name})

			print(prices)
   
			if(prices):
					frappe.throw("Another ItemPrice with the same item/pricelist exist.")
     
	def on_update(self):
     
		item_to_update_price = frappe.get_doc("Item", self.item)
		print("item_to_update_price")
		print(item_to_update_price)
		print("item_to_update_price item")
		print(item_to_update_price.item)

		if self.price_list == "Standard Buying":
			if item_to_update_price.standard_buying_price != self.rate:
				sql = """
				UPDATE `tabItem`
				SET `standard_buying_price` = %s
				WHERE `name` = %s
				"""
				frappe.db.sql(sql, (self.rate, self.item))
				print("before show alert from 'item price', standard buying, update ")
				frappe.msgprint(f"Standard buying price updated for the item, {self.item}", alert=True)

		if self.price_list == "Standard Selling":
			if item_to_update_price.standard_selling_price != self.rate:
				sql = """
				UPDATE `tabItem`
				SET `standard_selling_price` = %s
				WHERE `name` = %s
				"""
				frappe.db.sql(sql, (self.rate, self.item))
				print("before show alert from 'item price', standard selling, update ")
				frappe.msgprint(f"Standard selling price updated for the item, {self.item}", alert=True)
		


			

			