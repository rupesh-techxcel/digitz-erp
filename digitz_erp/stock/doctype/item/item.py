# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
import uuid
from frappe.model.document import Document
from digitz_erp.api.settings_api import get_default_currency
from digitz_erp.api.item_price_api import update_item_price
from frappe import _

class Item(Document):
    	
	def validate(self):
     
		if not self.is_new():
			if self.base_unit != frappe.db.get_value("Item", self.item_code, "base_unit"):
				self.check_stock_ledgers_for_base_unit_change()
   
   
		default_company = frappe.db.get_single_value(
			"Global Settings", "default_company")
  
		company_default = frappe.get_value("Company", default_company, ['default_product_expense_account'], as_dict=1)

		if not company_default.default_product_expense_account:
			frappe.throw("'Default Product Expense Account' is not configured for the company.")
       
   
	def check_stock_ledgers_for_base_unit_change(self):
		base_unit = self.base_unit
		existing_stock_ledgers = frappe.db.get_all("Stock Ledger", filters={"item": self.item_code}, fields=["name", "unit"])
		for ledger in existing_stock_ledgers:
			if ledger["unit"] != base_unit:
				frappe.throw("Cannot change base unit as it's being used in stock ledgers.")
    
	def before_validate(self):
		
		if not self.description:
			self.description = self.item_name
   
		if self.item_type == "Fixed Asset" and self.maintain_stock:
			self.maintain_stock = False
			frappe.msgprint("Maintaining stock for fixed assets is not applicable. It has been set to false.",alert=True)


	def update_standard_selling_price(self):

		# unique_id = str(uuid.uuid4())
		# #print("unique_id crated")
		# #print(unique_id)
		currency = get_default_currency()

		if not frappe.db.exists("Item Price",{'item': self.item_code, 'price_list':'Standard Selling', 'currency':currency}):

			if(self.standard_selling_price>0):
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

				frappe.msgprint(f"Price list,'Standard Selling' added for the item, {self.item_code}", alert= True)
		else:

				item_price_name = frappe.get_value("Item Price",{'item': self.item_code, 'price_list': 'Standard Selling', 'currency':currency},['name'])
				item_price_to_update = frappe.get_doc('Item Price', item_price_name)

				if(item_price_to_update.rate != self.standard_selling_price):
					item_price_to_update.rate = self.standard_selling_price
					item_price_to_update.save()
					frappe.msgprint(f"Price list,'Standard Selling' updated for the item, {self.item_code}", alert= True)

	def update_standard_buying_price(self):

		currency = get_default_currency()

		if not frappe.db.exists("Item Price",{'item': self.item_code, 'price_list':'Standard Buying', 'currency':currency}):

			if(self.standard_buying_price>0):

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
				
				frappe.msgprint(f"Price list,'Standard Buying' added for the item, {self.item_code}", alert= True)
		else:
				item_price_name = frappe.get_value("Item Price",{'item': self.item_code, 'price_list': 'Standard Buying', 'currency':currency},['name'])
				item_price_to_update = frappe.get_doc('Item Price', item_price_name)

				if(item_price_to_update.rate != self.standard_buying_price):
					item_price_to_update.rate = self.standard_buying_price
					item_price_to_update.save()
					frappe.msgprint(f"Price list,'Standard Buying' updated for the item, {self.item_code}", alert= True)

				# #print("item_price_to_update")
				# #print(item_price_to_update)

				# if(item_price_to_update.rate != self.standard_buying_price):
				# 	sql = """
				# 	UPDATE `tabItem Price`
				# 	SET `rate` = %s
				# 	WHERE `name` = %s
				# 	""".format(frappe.db.escape(self.standard_buying_price), frappe.db.escape(item_price_name))


	def on_update(self):

		# if self.do_not_update_price == False:
		self.update_standard_buying_price()
		self.update_standard_selling_price()
