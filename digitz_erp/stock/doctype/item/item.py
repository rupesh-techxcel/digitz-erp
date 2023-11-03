# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.settings_api import get_default_currency
from digitz_erp.api.item_price_api import update_item_price

class Item(Document):
	 
	def update_standard_selling_price(self):
     
		print("from update_standard_selling_price")
     	
		currency = get_default_currency()

		if not frappe.db.exists("Item Price",{'item': self.item_code, 'price_list':'Standard Selling', 'currency':currency}):				

			if(self.standard_selling_price>0):
       
				sql = """
				INSERT INTO `tabItem Price` (`item`, `item_name`, `price_list`, `currency`, `rate`, `unit`)
				VALUES ('{item_code}', '{item_name}', 'Standard Selling', '{currency}', '{standard_selling_price}', '{base_unit}')
				""".format(
				item_code=frappe.db.escape(self.item_code),
				item_name=frappe.db.escape(self.item_name),
				currency=frappe.db.escape(currency),
				standard_selling_price=frappe.db.escape(self.standard_selling_price),
				base_unit=frappe.db.escape(self.base_unit)
				)

				frappe.db.sql(sql)       
				
				frappe.msgprint(f"Price list,'Standard Selling' updated for the item, {self.item_code}", alert= True)        			
		else:	
				item_price_name = frappe.get_value("Item Price",{'item': self.item_code, 'price_list': 'Standard Selling', 'currency':currency},['name'])    
				item_price_to_update = frappe.get_doc('Item Price', item_price_name)
				print("item_price_to_update")
				print(item_price_to_update)
				
				if(item_price_to_update.rate != self.standard_selling_price):    
					sql = """
					UPDATE `tabItem Price`
					SET `rate` = %s
					WHERE `name` = %s
					""".format(frappe.db.escape(self.standard_selling_price), frappe.db.escape(item_price_name))
     
					frappe.msgprint(f"Price list,'Standard Selling' updated for the item, {self.item_code}", alert= True)        
     
	def update_standard_buying_price(self):
     	
		currency = get_default_currency()

		if not frappe.db.exists("Item Price",{'item': self.item_code, 'price_list':'Standard Buying', 'currency':currency}):				

			if(self.standard_buying_price>0):
       
				sql = """
				INSERT INTO `tabItem Price` (`item`, `item_name`, `price_list`, `currency`, `rate`, `unit`)
				VALUES ('{item_code}', '{item_name}', 'Standard Selling', '{currency}', '{standard_buying_price}', '{base_unit}')
				""".format(
				item_code=frappe.db.escape(self.item_code),
				item_name=frappe.db.escape(self.item_name),
				currency=frappe.db.escape(currency),
				standard_buying_price=frappe.db.escape(self.standard_buying_price),
				base_unit=frappe.db.escape(self.base_unit)
				)

				frappe.db.sql(sql)       
				
				frappe.msgprint(f"Price list,'Standard Buying' updated for the item, {self.item_code}", alert= True)        			
		else:	
				item_price_name = frappe.get_value("Item Price",{'item': self.item_code, 'price_list': 'Standard Buying', 'currency':currency},['name'])    
				item_price_to_update = frappe.get_doc('Item Price', item_price_name)
				print("item_price_to_update")
				print(item_price_to_update)
				
				if(item_price_to_update.rate != self.standard_buying_price):    
					sql = """
					UPDATE `tabItem Price`
					SET `rate` = %s
					WHERE `name` = %s
					""".format(frappe.db.escape(self.standard_buying_price), frappe.db.escape(item_price_name))
     
					frappe.msgprint(f"Price list,'Standard Buying' updated for the item, {self.item_code}", alert= True)  

	def on_update(self):     

		print("self.do_not_update_price")
		print(self.do_not_update_price)

		# if self.do_not_update_price == False:
		self.update_standard_buying_price()	
		self.update_standard_selling_price()
	