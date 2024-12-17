# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.pdf_utils import *
from datetime import *
from frappe.utils import *

class GLPosting(Document):
    
	def after_insert(self):
		self.update_project_work_in_progress()

	def update_project_work_in_progress(self):
     
		if self.project:
			# Fetch the account linked to the current document
			account = frappe.get_doc("Account", self.account)

			# Check if the account's account_type is 'Work In Progress'
			if account.account_type == "Work In Progress":
				# Fetch sum of debit_amount and credit_amount from GL Posting for the same project
				gl_entries = frappe.db.sql("""
					SELECT 
						SUM(glp.debit_amount) AS total_debit, 
						SUM(glp.credit_amount) AS total_credit
					FROM `tabGL Posting` glp
					JOIN `tabAccount` acc ON glp.account = acc.name
					WHERE 
						acc.account_type = 'Work In Progress' AND 
						glp.project = %(project)s
				""", {
					"project": self.project
				}, as_dict=True)

				if gl_entries and gl_entries[0]:
					# Calculate the work-in-progress balance
					total_debit = gl_entries[0].get("total_debit", 0) or 0
					total_credit = gl_entries[0].get("total_credit", 0) or 0
					work_in_progress_balance = total_debit - total_credit

					# Update the project's work_in_progress field
					frappe.db.set_value(
						"Project",
						self.project,
						"work_in_progress_value",
						work_in_progress_balance
					)		
	
@frappe.whitelist()
def get_party_balance(party_type, party):
    
	#print("party_type")
	#print(party_type)
	#print("party")
	#print(party)
 
	party_balance = 0

	if(party_type == "Customer"):
		
		party_balance = frappe.db.sql("""
		SELECT SUM(rounded_total) - SUM(paid_amount) 
		FROM `tabSales Invoice` 
		WHERE customer=%s and credit_sale =1 and docstatus<2 and rounded_total> paid_amount
		""", ( party))[0][0]
  
		if not party_balance:
			party_balance = 0.00
	
	else:

		party_balance = frappe.db.sql("""
		SELECT SUM(debit_amount) - SUM(credit_amount) 
		FROM `tabGL Posting` 
		WHERE party_type=%s AND party=%s
		""", (party_type, party))[0][0]

		# For customer it automatically shows negative 
		# For supplier, value must be negative, if it is positve that means
		# its negative balance
		if(party_type == "Supplier" and party_balance>0):
			party_balance = party_balance * -1

	return party_balance	
