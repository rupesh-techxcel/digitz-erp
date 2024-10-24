# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import money_in_words


class ProformaInvoice(Document):

	def before_validate(self):
		self.in_words = money_in_words(self.rounded_total,"AED")

	def on_submit(self):
		
		if not self.client_approved:
			frappe.throw("Client approval pending to submit the Proforma Invoice.")
		
