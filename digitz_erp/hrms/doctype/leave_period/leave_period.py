# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LeavePeriod(Document):
    
	def validate(self):
  
		exists = frappe.db.sql("""
			SELECT name 
			FROM `tabLeave Period` 
			WHERE 
				(from_date BETWEEN %s AND %s) OR
				(to_date BETWEEN %s AND %s) OR
				(%s BETWEEN from_date AND to_date) OR
				(%s BETWEEN from_date AND to_date)
				AND name != %s
		""", (self.from_date, self.to_date, self.from_date, self.to_date, self.from_date, self.to_date, self.name), as_dict=True)
		
		if exists:
			frappe.throw(f"A conflicting leave period {exists[0]['name']} already exists in the system.")
		
		if exists:
			frappe.throw(f"A conflicting leave period {exists[0]['name']} already exists in the system.")
