# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class ItemGroup(Document):
	def before_validate(self):

		if not self.description:
			self.description = self.item_group_name

