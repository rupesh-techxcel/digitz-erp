# Copyright (c) 2025, Techxcel Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.settings_api import get_default_company

class SalesProspect(Document):
    
	def before_validate(self):
     		
		self.name = self.prospect_name
		company = get_default_company()
		area_mandatory = frappe.get_value("Company",company,"customer_area_required")
		
		if area_mandatory:
			self.name = f"{self.prospect_name}, {self.area}"
   
		self.validate_data()

	def validate_data(self):
		
		company = get_default_company()    
		
		area_mandatory,trn_mandatory,address_required,mobile_required,email_required, emirate_required = frappe.get_value("Company",company,["customer_area_required","customer_trn_required","customer_address_required","customer_mobile_required","customer_email_required","emirate_required"])
		
		if area_mandatory and not self.area:
			frappe.throw("Select Area.")
				
		if address_required and not self.address_line_1:
			frappe.throw("Address Line 1 is mandaoty for the customer.")
			
		if mobile_required and not self.mobile_no:
			frappe.throw("Mobile Number is mandatory for the customer.")
		
		if email_required and not self.email_id:
			frappe.throw("Email Id is mandaoty for the customer.")
   
		if emirate_required and not self.emirate:
			frappe.throw("Emirate is mandatory for the customer")
