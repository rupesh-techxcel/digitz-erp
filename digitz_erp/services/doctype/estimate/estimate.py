# Copyright (c) 2024,   and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.digitz_erp.doctype.boq.boq import update_boq

class Estimate(Document):
    
	def before_validate(self):
		
		for i in range(0,len(self.estimation_items)):			
			for j in range(0,len(self.item_groups)):			
				if self.estimation_items[i].item_group == self.item_groups[j].item_group_name:
					self.estimation_items[i].group_description = self.item_groups[j].description
     
		for i in range(0,len(self.estimation_items)):      
			if self.estimation_items[i].raw_cost:
				self.estimation_items[i].raw_cost = round(self.estimation_items[i].raw_cost,2)
    
		estimate_amount = 0
		
		for i in range(0,len(self.estimation_items)):	
			if self.estimation_items[i].boq_amount:
				estimate_amount += round(self.estimation_items[i].boq_amount,2)
			
		self.estimate_total = estimate_amount
  			
	def validate(self):
     
		for item in self.estimation_items:  # Assuming 'estimation_items' is the child table field name
			if not item.width_meter or not item.height_meter or not item.quantity or not item.rate:
				frappe.throw(("Please ensure all fields (width_meter, height_meter, quantity, rate) are entered for item: {0}").format(item.item_name))

		# Check if any field is zero
		if item.width_meter <= 0 or item.height_meter <= 0 or item.quantity <= 0 or item.rate <= 0:
			frappe.throw(("The fields width_meter, height_meter, quantity, and rate must be greater than zero for item: {0}").format(item.item_name))

	def on_submit(self):     
		
		# Check if the estimation is linked to a BOQ
		if self.boq:  # Assuming you have a field in Estimate that stores the linked BOQ ID
			update_boq(self.boq, self.name)

					

	
	





