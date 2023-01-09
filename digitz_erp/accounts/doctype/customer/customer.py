# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Customer(Document):

	def on_trash(self):		
		frappe.db.delete("Customer Address", {
 	   "customer": self.customer_name
	})

	def on_update(self):	
		
		if	self.billing_address:
			billing_address_doc = frappe.get_doc('Customer Address', self.billing_address)
			billing_address_doc.customer = self.customer_name
			billing_address_doc.is_default = 1
			billing_address_doc.billing_address = 1
			billing_address_doc.shipping_address = 0
			billing_address_doc.save()

		if	self.shipping_address:
			shipping_address_doc = frappe.get_doc('Customer Address', self.shipping_address)
			shipping_address_doc.customer = self.customer_name
			shipping_address_doc.is_default = 1
			shipping_address_doc.billing_address = 0
			shipping_address_doc.shipping_address = 1
			shipping_address_doc.save()
		
		
def validate_customer(self):
	pass
