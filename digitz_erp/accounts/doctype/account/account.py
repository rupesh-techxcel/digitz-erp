# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet

class Account(NestedSet):
	
	def validate(self):
     
		if self.name != "Accounts":
     
			if(not self.parent_account): 
				frappe.throw("Parent account mandatory.")
	
			if(not self.root_type): 
				frappe.throw("Root Type mandatory.")

    
