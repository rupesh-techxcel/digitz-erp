# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Company(Document):
	
	def after_insert(self):	
		
		global_settings = frappe.db.get_single_value("Global Settings","default_company")

		if not global_settings:		
			frappe.db.set_value("Global Settings", None, "default_company", self.company_name)



	
		# if(not default_company):
	