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
   
	def on_update(self):
     
		if frappe.flags.get('skip_expense_head_creation'):
			return
     
		self.create_expense_head_if_applicable()

	def create_expense_head_if_applicable(self):
     		
		if self.is_group or self.root_type != "Expense":
			return

		company = frappe.db.get_single_value("Global Settings",'default_company')
  
		print("company")
		print(company)

		# This checking is critical because while install the app and creating default accounts, there is no company exists and leads to error.
		if not company:
			return

		company_doc = frappe.get_doc("Company", company)
		if company_doc.get("do_not_create_expense_head_automatically"):
			return

		if self.account_already_linked():
			frappe.msgprint(f"An Expense Head is already linked to this account: {self.name}", alert=1)
			return

		if self.expense_head_name_exists():
			frappe.msgprint(f"An Expense Head with the name '{self.name}' already exists.", alert=1)
			return

		try:
			expense_head = frappe.new_doc("Expense Head")
			expense_head.expense_type = "Expense"
			expense_head.expense_head = self.name
			expense_head.account = self.name
			expense_head.tax = "UAE VAT - 5%"
			expense_head.insert(ignore_permissions=True)
			frappe.msgprint(f"Expense Head has been successfully created for the account: {self.name}", alert=1)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Failed to create Expense Head for account: {self.name}")

	def account_already_linked(self):
		return frappe.db.exists("Expense Head", {
			"account": self.name
		})

	def expense_head_name_exists(self):
		return frappe.db.exists("Expense Head", {
			"expense_head": self.name
		})