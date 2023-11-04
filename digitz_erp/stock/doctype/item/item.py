# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
import uuid
from frappe.model.document import Document
from digitz_erp.api.settings_api import get_default_currency
from digitz_erp.api.item_price_api import update_item_price

class Item(Document):
	 
	def update_standard_selling_price(self):
     
		print("from update_standard_selling_price")
     	
		# unique_id = str(uuid.uuid4())
		# print("unique_id crated")
		# print(unique_id)  
		currency = get_default_currency()

		if not frappe.db.exists("Item Price",{'item': self.item_code, 'price_list':'Standard Selling', 'currency':currency}):				

			if(self.standard_selling_price>0):       
				  
				# sql = """
				# INSERT INTO `tabItem Price` (`name`,`item`, `item_name`, `price_list`, `currency`, `rate`, `unit`)
				# VALUES ('{name}', '{item_code}', '{item_name}', 'Standard Selling', '{currency}', '{standard_selling_price}', '{base_unit}')
				# """.format(
				# name = frappe.db.escape(unique_id),
				# item_code=frappe.db.escape(self.item_code),
				# item_name=frappe.db.escape(self.item_name),
				# currency=frappe.db.escape(currency),
				# standard_selling_price=frappe.db.escape(self.standard_selling_price),
				# base_unit=frappe.db.escape(self.base_unit)
				# )

				# frappe.db.sql(sql)       
				item_price = frappe.get_doc({
							"doctype": "Item Price",
							"item": self.item_code,
							"item_name": self.item_name,
							"price_list": "Standard Selling",
							"currency": currency,
							"is_selling":1,
							"rate": self.standard_selling_price,
							"unit": self.base_unit
							})

				# Set the flags to ignore permissions and links
				item_price.flags.ignore_permissions = True
				item_price.flags.ignore_links = True

				# Save the document to the database without firing hooks
				item_price.insert(ignore_permissions=True, ignore_links=True)    				  
				print("before show alert from item , standard selling, add ")
				frappe.msgprint(f"Price list,'Standard Selling' added for the item, {self.item_code}", alert= True)        			
		else:	
      
				item_price_name = frappe.get_value("Item Price",{'item': self.item_code, 'price_list': 'Standard Selling', 'currency':currency},['name'])    
				item_price_to_update = frappe.get_doc('Item Price', item_price_name)

				item_price_to_update.rate = self.standard_selling_price
				item_price_to_update.save()
    
				# item_price_name = frappe.get_value("Item Price",{'item': self.item_code, 'price_list': 'Standard Selling', 'currency':currency},['name'])    
				# item_price_to_update = frappe.get_doc('Item Price', item_price_name)
				# print("item_price_to_update")
				# print(item_price_to_update)
				
				# if(item_price_to_update.rate != self.standard_selling_price):    
				# 	sql = """
				# 	UPDATE `tabItem Price`
				# 	SET `rate` = %s
				# 	WHERE `name` = %s
				# 	""".format(frappe.db.escape(self.standard_selling_price), frappe.db.escape(item_price_name))
     
				print("before show alert from item , standard selling, update ")
				frappe.msgprint(f"Price list,'Standard Selling' updated for the item, {self.item_code}", alert= True)        
     
	def update_standard_buying_price(self):
     	
		currency = get_default_currency()

		if not frappe.db.exists("Item Price",{'item': self.item_code, 'price_list':'Standard Buying', 'currency':currency}):

			if(self.standard_buying_price>0):      
       
				# unique_id = str(uuid.uuid4())
				# print("unique_id crated")
				# print(unique_id)  
    
				# sql = """
				# INSERT INTO `tabItem Price` (`name`,`item`, `item_name`, `price_list`, `currency`, `rate`, `unit`)
				# VALUES ({name},{item_code}, {item_name}, 'Standard Selling', {currency}, {standard_buying_price}, {base_unit})
				# """.format(
				# name = frappe.db.escape(unique_id),
				# item_code=frappe.db.escape(self.item_code),
				# item_name=frappe.db.escape(self.item_name),
				# currency=frappe.db.escape(currency),
				# standard_buying_price=frappe.db.escape(self.standard_buying_price),
				# base_unit=frappe.db.escape(self.base_unit)
				# )
    
				# frappe.db.sql(sql)       
				
				# frappe.msgprint(f"Price list,'Standard Buying' added for the item, {self.item_code}", alert= True)        			
    
				# item_price_doc = frappe.new_doc("Item Price")
				# item_price_doc.item = self.item_code
				# item_price_doc.item_name = self.item_name
				# item_price_doc.price_list = "Standard Selling"
				# item_price_doc.currency = currency
				# item_price_doc.rate = self.standard_buying_price
				# item_price_doc.unit = self.base_unit

				# item_price_doc.insert()
    
				item_price = frappe.get_doc({
				"doctype": "Item Price",
				"item": self.item_code,
				"item_name": self.item_name,
				"price_list": "Standard Buying",
				"currency": currency,
				"is_buying":1,
				"rate": self.standard_buying_price,
				"unit": self.base_unit
				})

				# Set the flags to ignore permissions and links
				item_price.flags.ignore_permissions = True
				item_price.flags.ignore_links = True

				# Save the document to the database without firing hooks
				item_price.insert(ignore_permissions=True, ignore_links=True)    				  
				print("before show alert from item , standard buying, add ")
				frappe.msgprint(f"Price list,'Standard Buying' added for the item, {self.item_code}", alert= True)        			
		else:	
				item_price_name = frappe.get_value("Item Price",{'item': self.item_code, 'price_list': 'Standard Buying', 'currency':currency},['name'])    
				item_price_to_update = frappe.get_doc('Item Price', item_price_name)

				item_price_to_update.rate = self.standard_buying_price
				item_price_to_update.save()
       
				# print("item_price_to_update")
				# print(item_price_to_update)
				
				# if(item_price_to_update.rate != self.standard_buying_price):    
				# 	sql = """
				# 	UPDATE `tabItem Price`
				# 	SET `rate` = %s
				# 	WHERE `name` = %s
				# 	""".format(frappe.db.escape(self.standard_buying_price), frappe.db.escape(item_price_name))
				print("before show alert from item , standard buying, update ")     
				frappe.msgprint(f"Price list,'Standard Buying' updated for the item, {self.item_code}", alert= True)  

	def on_update(self):     
		
		# if self.do_not_update_price == False:
		self.update_standard_buying_price()	
		self.update_standard_selling_price()
	