# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.pdf_utils import *
from datetime import *
from frappe.utils import *

class GLPosting(Document):
	pass
	
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
