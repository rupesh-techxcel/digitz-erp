# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Supplier(Document):	
	
	def before_save(self):
		self.validate_globals()	

	
	def validate_globals(self):
		
		global_settings = frappe.db.get_single_value("Global Settings","default_company")
		if not global_settings:
			frappe.throw('Default companuy is not configured in the Global Settings!.')			

	def after_insert(self):		
		
		if self.create_account_with_supplier_name_while_saving:
			doc = frappe.new_doc('Account')
			doc.account_name = self.supplier_name
			doc.parent_account = self.account_group
			doc.account_type = "Creditors"
			doc.insert()		

			supDoc = frappe.get_doc('Supplier', self.supplier_name)					

			supDoc.account_ledger = self.supplier_name
			supDoc.save()
			
			frappe.msgprint("Account ledger created and assigned to the supplier.")

			
			
		

		
	



		
		
		
		

		

		

		
		
		
		


	# def after_insert(self):
	# 	doc = frappe.get_doc('doctype':'Account',
	# 				'account_name': self.Supplier_name

	# 	)


		
    
	
