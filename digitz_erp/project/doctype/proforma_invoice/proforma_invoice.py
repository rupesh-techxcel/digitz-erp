# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProformaInvoice(Document):

	def on_submit(self):
     
		if not self.client_approved:
			frappe.throw("Client approval pending to submit the Proforma Invoice.")
     
