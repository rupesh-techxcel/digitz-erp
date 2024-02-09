# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now
from frappe.model.document import Document
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_item_stock_balance

class PurchaseOrder(Document):

	def before_submit(self):

		possible_invalid= frappe.db.count('Purchase Order', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time], 'docstatus':['=', 1]})
		# When duplicating the voucher user may not remember to change the date and time. So do not allow to save the voucher to be
		# posted on the same time with any of the existing vouchers. This also avoid invalid selection to calculate moving average value
		# Also in add_stock_for_purchase_receipt method only checking for < date_time in order avoid difficulty to get exact last record
		# to get balance qty and balance value.

		print(possible_invalid)

		if(possible_invalid >0):
			frappe.throw("There is another Order invoice exist with the same date and time. Please correct the date and time.")

	def validate(self):

		if not self.credit_purchase and self.payment_mode == None:
			frappe.throw("Select Payment Mode")

		self.validate_items()

	def before_validate(self):
		if not self.credit_purchase or self.credit_purchase  == False:
			self.paid_amount = self.rounded_total
		else:
			if self.is_new():
				self.paid_amount = 0

	def before_save(self):
		print("before_save")
	 	# While duplicating making sure the status is resetting
		if self.is_new():
			self.order_status = "Pending"
			for item in self.items:
				item.purchased_qty = 0

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


	@frappe.whitelist()
	def generate_purchase_invoice(self):

		purchase_invoice_name = ""
		purchaseOrderName =  self.name

		purchase_invoice = self.__dict__
		purchase_invoice['doctype'] = 'Purchase Invoice'
		purchase_invoice['name'] = purchase_invoice_name
		purchase_invoice['naming_series'] = ""
		purchase_invoice['posting_date'] = self.posting_date
		purchase_invoice['posting_time'] = self.posting_time
		purchase_invoice['purchase_order'] = purchaseOrderName

		# Change the document status to draft to avoid error while submitting child table
		purchase_invoice['docstatus'] = 0

		rows_to_remove = []
		for i, row in enumerate(purchase_invoice['items']):
			if row.qty == row.qty_purchased:
				rows_to_remove.append(i)

		for i in reversed(rows_to_remove):
			purchase_invoice['items'].pop(i)

		for item in purchase_invoice['items']:
			item.doctype = "Purchase Invoice Item"
			item.qty = item.qty - item.qty_purchased
			item.po_item_reference = item.name
			# item.delivery_note_item_reference_no = item.name
			item._meta = ""

		purchase_invoice_doc = frappe.get_doc(
			purchase_invoice).insert(ignore_permissions=True)

		frappe.db.commit()

		frappe.msgprint("Purchase Invoice created successfully, in draft mode.")

	@frappe.whitelist()
	def check_and_update_purchase_order_status(self):

		purchase_order = frappe.get_doc("Purchase Order", self.purchase_order)

		print("purchase order")
		print(purchase_order)

		purchase_order_items = frappe.get_list("Purchase Order Item", {'parent': purchase_order},['name'])

		purchased_any = False
		at_least_one_partial_purchase = False
		purchased_full = False #Not using for conditions

		for po in self.items:
			print(po)
			if po.qty_purchased and po.qty_purchased > 0:
				purchased_any = True
				if po.qty_purchased and po.qty_purchased == po.qty:
					purchased_full = True
				else:
					at_least_one_partial_purchase = True

		if not purchased_any == False:
			print("1")
			# self.status = "Pending"
			frappe.db.set_value("Purchase Order", purchase_order.name, {'order_status': "Pending"})
			print("1 set value")
		elif at_least_one_partial_purchase:
			print("2")
			# self.status = "Partial"

			frappe.db.set_value("Purchase Order", purchase_order.name, {'order_status': "Partial"})
			print("2 set  value")
		else:
			print("3")
		#    self.status = "Completed"
			frappe.db.set_value("Purchase Order", purchase_order.name, {'order_status': "Completed"})
		#    print("3 set value")

		purchase_order.save()

@frappe.whitelist()
def get_default_payment_mode():
    default_payment_mode = frappe.db.get_value('Company', filters={'name'},fieldname='default_payment_mode_for_purchase')
    print(default_payment_mode)
    return default_payment_mode
