# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class UserWarehouse(Document):

	def validate(self):   
     
		possible_invalid= frappe.db.count('User Warehouse', {'user': ['=', self.user], 'warehouse':['=', self.warehouse]})
  
		if(possible_invalid >0):	
			frappe.throw("Duplicate record found. Cannot continue.")
   
		any_user= frappe.db.count('User Warehouse', {'user': ['=', self.user]})
  
		if(any_user == 0):
			self.is_default = 1
  

  

   
		

  
		
  	
