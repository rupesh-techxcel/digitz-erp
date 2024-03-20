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

class PurchaseOrder(Document):

	def Voucher_In_The_Same_Time(self):
		possible_invalid= frappe.db.count('Purchase Order', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time]})
		return possible_invalid

	def validate(self):

		if not self.credit_purchase and self.payment_mode == None:
			frappe.throw("Select Payment Mode")

		self.validate_items()

	def before_validate(self):
		self.in_words = money_in_words(self.rounded_total,"AED")

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
				print("is new true")
				self.paid_amount = 0

		if self.is_new():
			for item in self.items:
				item.qty_purchased_in_base_unit = 0
			self.order_status = "Pending"

	def Set_Posting_Time_To_Next_Second(self):
		datetime_object = datetime.strptime(str(self.posting_time), '%H:%M:%S')

		# Add one second to the datetime object
		new_datetime = datetime_object + timedelta(seconds=1)

		# Extract the new time as a string
		self.posting_time = new_datetime.strftime('%H:%M:%S')

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
def get_default_payment_mode():
    default_payment_mode = frappe.db.get_value('Company', filters={'name'},fieldname='default_payment_mode_for_purchase')
    print(default_payment_mode)
    return default_payment_mode

@frappe.whitelist()
def generate_purchase_invoice_for_purchase_order(purchase_order):

	purchase_doc = frappe.get_doc("Purchase Order", purchase_order)

	# Create Purchase Invoice
	purchase_invoice = frappe.new_doc("Purchase Invoice")
	purchase_invoice.supplier = purchase_doc.supplier
	purchase_invoice.company = purchase_doc.company
	purchase_invoice.supplier_address = purchase_doc.supplier_address
	purchase_invoice.tax_id = purchase_doc.tax_id
	purchase_invoice.posting_date = purchase_doc.posting_date
	purchase_invoice.posting_time = purchase_doc.posting_time
	purchase_invoice.price_list = purchase_doc.price_list
	purchase_invoice.do_no = purchase_doc.do_no
	purchase_invoice.warehouse = purchase_doc.warehouse
	purchase_invoice.supplier_inv_no = purchase_doc.supplier_inv_no
	purchase_invoice.rate_includes_tax = purchase_doc.rate_includes_tax
	purchase_invoice.credit_purchase = purchase_doc.credit_purchase
	purchase_invoice.credit_days = purchase_doc.credit_days
	purchase_invoice.payment_terms = purchase_doc.payment_terms
	purchase_invoice.payment_mode = purchase_doc.payment_mode
	purchase_invoice.payment_account = purchase_doc.payment_account
	purchase_invoice.remarks = purchase_doc.remarks
	purchase_invoice.reference_no = purchase_doc.reference_no
	purchase_invoice.reference_date = purchase_doc.reference_date
	purchase_invoice.gross_total = purchase_doc.gross_total
	purchase_invoice.total_discount_in_line_items = purchase_doc.total_discount_in_line_items
	purchase_invoice.tax_total = purchase_doc.tax_total
	purchase_invoice.net_total = purchase_doc.net_total
	purchase_invoice.round_off = purchase_doc.round_off
	purchase_invoice.rounded_total = purchase_doc.rounded_total
	purchase_invoice.paid_amount = purchase_doc.paid_amount
	purchase_invoice.terms = purchase_doc.terms
	purchase_invoice.terms_and_conditions = purchase_doc.terms_and_conditions
	print("purchase_order")
	print(purchase_order)
	purchase_invoice.purchase_order = purchase_order

	pending_item_exists = False

	# Append items from Purchase Order to Purchase Invoice
	for item in purchase_doc.items:

		if(item.qty_in_base_unit - item.qty_purchased_in_base_unit>0):
			pending_item_exists = True
			invoice_item = frappe.new_doc("Purchase Invoice Item")
			invoice_item.item = item.item
			invoice_item.item_name = item.item_name
			invoice_item.display_name = item.display_name
			invoice_item.qty = round((item.qty_in_base_unit - item.qty_purchased_in_base_unit)/ item.conversion_factor,2)
			invoice_item.unit = item.unit
			invoice_item.rate = item.rate_in_base_unit * item.conversion_factor
			invoice_item.base_unit = item.base_unit
			invoice_item.qty_in_base_unit = item.qty_in_base_unit - item.qty_purchased_in_base_unit
			invoice_item.rate_in_base_unit = item.rate_in_base_unit
			invoice_item.conversion_factor = item.conversion_factor
			invoice_item.rate_includes_tax = item.rate_includes_tax
			invoice_item.rate_excluded_tax = item.rate_excluded_tax
			invoice_item.warehouse = item.warehouse
			invoice_item.gross_amount = item.gross_amount
			invoice_item.tax_excluded = item.tax_excluded
			invoice_item.tax = item.tax
			invoice_item.tax_rate = item.tax_rate
			invoice_item.tax_amount = item.tax_amount
			invoice_item.discount_percentage = item.discount_percentage
			invoice_item.discount_amount = item.discount_amount
			invoice_item.net_amount = item.net_amount
			invoice_item.po_item_reference = item.name
			purchase_invoice.append("items", invoice_item)

	if pending_item_exists:
		purchase_invoice.insert()
		frappe.db.commit()
		frappe.msgprint("Purchase Invoice generated in draft mode", alert=True)
		return purchase_invoice.name
	else:
		frappe.msgprint("Purchase Invoice cannot be created because there are no pending items in the Purchase Order.")
		return "No Pending Items"
