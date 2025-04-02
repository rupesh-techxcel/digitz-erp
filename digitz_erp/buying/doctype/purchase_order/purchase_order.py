# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now
from frappe.model.document import Document
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_stock_balance_in_item
from datetime import datetime,timedelta
from frappe.utils import get_datetime
from frappe.utils import money_in_words
from digitz_erp.api.settings_api import add_seconds_to_time
from digitz_erp.api.accounts_api import get_balance_budget_value
from frappe.utils import flt

class PurchaseOrder(Document):

	def Voucher_In_The_Same_Time(self):
		possible_invalid= frappe.db.count('Purchase Order', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time]})
		return possible_invalid

	def validate(self):

		if not self.credit_purchase and self.payment_mode == None:
			frappe.throw("Select Payment Mode")

		self.validate_items()
		self.validate_budget_for_items()

	def validate_budget_for_items(self):
		"""
		Validate budget for each item in a Material Request.
		"""
		for item in self.items:
			budget_data = get_balance_budget_value(
				reference_type="Item",
				reference_value=item.item,
				doc_type="Purchase Order",
				doc_name=self.name,
				transaction_date=self.posting_date,
				company=self.company,
				project=self.project,
				cost_center=self.default_cost_center
			)
			
			if budget_data and not budget_data.get("no_budget"):
				details = budget_data.get("details", {})
				budget_amount = flt(details.get("Budget Amount", 0))
				used_amount = flt(details.get("Used Amount", 0))
				available_balance = flt(details.get("Available Balance", 0))
				ref_type = details.get("Reference Type")
				total_map = 0

				for row in self.items:
					
					gross_amount = flt(row.gross_amount)
     					
					if ref_type == "Item" and row.item == item.item:
						total_map += gross_amount
					elif ref_type == "Item Group" and row.item_group == item.item_group:
						total_map += gross_amount
				
				used_amount += total_map
				
				if budget_amount < used_amount:
					frappe.throw(f"Exceeding the allocated budget for the item {item.item}!")
     
	def get_balance_budget_value(reference_type, reference_value, doc_type, doc_name, transaction_date, company, project, cost_center):
			"""
			Fetch the budget details from existing API method.
			"""
			return frappe.call(
				"digitz_erp.api.accounts_api.get_balance_budget_value",
				reference_type=reference_type,
				reference_value=reference_value,
				doc_type=doc_type,
				doc_name=doc_name,
				transaction_date=transaction_date,
				company=company,
				project=project,
				cost_center=cost_center
			)

	def before_validate(self):
		  
		if self.rounded_total is not None:
			self.in_words = money_in_words(self.rounded_total, "AED")
		else:
			# Handle case when rounded_total is None
			self.in_words = None  # or provide a default string

		if(self.Voucher_In_The_Same_Time()):

				self.Set_Posting_Time_To_Next_Second()

				if(self.Voucher_In_The_Same_Time()):
					self.Set_Posting_Time_To_Next_Second()

					if(self.Voucher_In_The_Same_Time()):
						self.Set_Posting_Time_To_Next_Second()

						if(self.Voucher_In_The_Same_Time()):
							frappe.throw("Voucher with same time already exists.")

		if not self.credit_purchase or self.credit_purchase  == False:
			self.paid_amount = self.rounded_total
		else:
			if self.is_new():
				#print("is new true")
				self.paid_amount = 0

		if self.is_new():
			for item in self.items:
				item.qty_purchased_in_base_unit = 0
			self.order_status = "Pending"

	from datetime import datetime

	def Set_Posting_Time_To_Next_Second(self):
		# Add 12 seconds to self.posting_time and update it
		self.posting_time = add_seconds_to_time(str(self.posting_time), seconds=12)

	def validate_items(self):

		idx =0
		for item in self.items:
			idx2 = 0
			for item2 in self.items:
				if(idx != idx2):
					if item.item == item2.item and item.display_name == item2.display_name:
						frappe.throw("Same item canot use in multiple rows with the same display name.")
				idx2= idx2 + 1
			idx = idx + 1
   
	def on_update(self):
     
		if self.material_request:
			self.update_material_request_quantities_on_update()			
     
	def on_cancel(self):
    
		if self.material_request:
			#print("Calling update po qties b4 cancel or delete")
			self.update_material_request_quantities_on_update(forDeleteOrCancel=True)
	
	def on_trash(self):
     
		if self.material_request:
			self.update_material_request_quantities_on_update(forDeleteOrCancel=True)
	
	def update_material_request_quantities_on_update(self, forDeleteOrCancel=False):

		po_reference_any = False

		for item in self.items:
			if not item.mr_item_reference:
				continue
			else:
				# Get total purchase invoice qty for the mr_item_reference other than in the current purchase invoice.
				total_purchased_qty_not_in_this_pi = frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_used_qty from `tabPurchase Order Item` pinvi inner join `tabPurchase Order` pinv on pinvi.parent= pinv.name WHERE pinvi.mr_item_reference=%s AND pinv.name !=%s and pinv.docstatus<2""",(item.mr_item_reference, self.name))[0][0]
				po_item = frappe.get_doc("Material Request Item", item.mr_item_reference)

				# Get Total returned quantity for the po_item, since there can be multiple purchase invoice line items for the same po_item_reference and which could be returned from the purchase invoices as well.

				total_qty_purchased = (total_purchased_qty_not_in_this_pi if total_purchased_qty_not_in_this_pi else 0) 

				po_item.qty_purchased_in_base_unit = total_qty_purchased + (item.qty_in_base_unit if not forDeleteOrCancel else 0)

				po_item.save()
				po_reference_any = True

		if(po_reference_any):
			frappe.msgprint("Purchased Qty of items in the corresponding material request updated successfully", indicator= "green", alert= True)


@frappe.whitelist()
def get_default_payment_mode():
    default_payment_mode = frappe.db.get_value('Company', filters={'name'},fieldname='default_payment_mode_for_purchase')
    #print(default_payment_mode)
    return default_payment_mode
