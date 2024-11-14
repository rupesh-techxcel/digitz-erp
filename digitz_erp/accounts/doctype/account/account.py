# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet

class Account(NestedSet):
	
	def validate(self):
     
		if self.name != "Accounts":
     
			if(not self.parent_account): 
				frappe.throw("Parent account mandatory.")
	
			# if(not self.root_type): 
			# 	frappe.throw("Root Type mandatory.")

	def before_validate(self):
		# Check if there's a parent account specified
		if self.parent_account and self.parent_account !="Accounts":
			# Fetch the parent account document
			parent_account = frappe.get_doc("Account", self.parent_account)

			# Set the root_type of the current account to match the parent's root_type
			self.root_type = parent_account.root_type
			print(f"Root type set from parent account: {self.root_type}")
