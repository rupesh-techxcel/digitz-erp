# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.sales_order_api import check_pending_items_exists
from digitz_erp.api.item_price_api import update_customer_item_price
from frappe.utils import money_in_words

class SalesOrder(Document):


	def before_validate(self):
		self.in_words = money_in_words(self.rounded_total,"AED")

		if self.is_new():
			for item in self.items:
				item.qty_sold_in_base_unit = 0
			self.order_status = "Pending"

	def on_submit(self):
		self.update_customer_prices()

	def update_customer_prices(self):

		for docitem in self.items:
				item = docitem.item
				rate = docitem.rate_in_base_unit
				update_customer_item_price(item, self.customer,rate,self.posting_date)


	@frappe.whitelist()
	def generate_sale_invoice(self):


		pending_items= check_pending_items_exists(self.name)

		if not pending_items:
			frappe.throw("No pending items in the Sales Order to generate a Sales Invoice.")

		sales_invoice_doc = frappe.new_doc('Sales Invoice')

		# Set fields directly from the object's attributes
		fields_to_copy = [
			'company', 'customer', 'customer_name', 'customer_display_name', 'customer_address', 'reference_no',
			'posting_date', 'posting_time', 'ship_to_location', 'salesman', 'salesman_code', 'tax_id', 'lpo_no',
			'lpo_date', 'price_list', 'rate_includes_tax', 'warehouse', 'credit_sale', 'credit_days', 'payment_terms',
			'payment_mode', 'payment_account', 'remarks', 'gross_total', 'total_discount_in_line_items', 'tax_total',
			'net_total', 'round_off', 'rounded_total', 'terms', 'terms_and_conditions', 'address_line_1', 'address_line_2',
			'area_name', 'country', 'quotation'
		]
		for field in fields_to_copy:
			setattr(sales_invoice_doc, field, getattr(self, field, None))

		sales_invoice_doc.sales_order = self.name

		sales_invoice_doc.save()

		for item in self.items:
			sales_invoice_item = frappe.new_doc("Sales Invoice Item")
			# Directly map the necessary fields
			for field in ['warehouse', 'item', 'item_name', 'display_name', 'unit', 'base_unit', 'rate_includes_tax',
						'rate_excluded_tax', 'gross_amount', 'tax_excluded', 'tax', 'tax_rate', 'tax_amount',
						'discount_percentage', 'discount_amount', 'net_amount', 'unit_conversion_details']:
				setattr(sales_invoice_item, field, getattr(item, field, None))

			sales_invoice_item.qty = round((item.qty_in_base_unit - item.qty_sold_in_base_unit) / item.conversion_factor, 2)
			sales_invoice_item.rate = item.rate_in_base_unit * item.conversion_factor
			sales_invoice_item.qty_in_base_unit = item.qty_in_base_unit - item.qty_sold_in_base_unit
			sales_invoice_item.rate_in_base_unit = item.rate_in_base_unit
			sales_invoice_item.conversion_factor = item.conversion_factor
			sales_invoice_item.sales_order_item_reference_no = item.name

			sales_invoice_doc.append('items', sales_invoice_item)

		sales_invoice_doc.save()
		return {"sales_invoice_name": sales_invoice_doc.name}

	@frappe.whitelist()
	def generate_delivery_note(self):

		pending_items= check_pending_items_exists(self.name)

		if not pending_items:
			frappe.throw("No pending items in the Sales Order to generate a Delivery Note.")

		delivery_note_doc = frappe.new_doc('Delivery Note')
		delivery_note_doc.company = self.company
		delivery_note_doc.customer = self.customer
		delivery_note_doc.customer_name = self.customer_name
		delivery_note_doc.customer_display_name = self.customer_display_name
		delivery_note_doc.customer_address = self.customer_address
		delivery_note_doc.reference_no = self.reference_no
		delivery_note_doc.posting_date = self.posting_date
		delivery_note_doc.posting_time = self.posting_time
		delivery_note_doc.ship_to_location = self.ship_to_location
		delivery_note_doc.salesman = self.salesman
		delivery_note_doc.salesman_code = self.salesman_code
		delivery_note_doc.tax_id = self.tax_id
		delivery_note_doc.lpo_no = self.lpo_no
		delivery_note_doc.lpo_date = self.lpo_date
		delivery_note_doc.price_list = self.price_list
		delivery_note_doc.rate_includes_tax = self.rate_includes_tax
		delivery_note_doc.warehouse = self.warehouse
		delivery_note_doc.credit_sale = self.credit_sale
		delivery_note_doc.credit_days = self.credit_days
		delivery_note_doc.payment_terms = self.payment_terms
		delivery_note_doc.payment_mode = self.payment_mode
		delivery_note_doc.payment_account = self.payment_account
		delivery_note_doc.remarks = self.remarks
		delivery_note_doc.gross_total = self.gross_total
		delivery_note_doc.total_discount_in_line_items = self.total_discount_in_line_items
		delivery_note_doc.tax_total = self.tax_total
		delivery_note_doc.net_total = self.net_total
		delivery_note_doc.round_off = self.round_off
		delivery_note_doc.rounded_total = self.rounded_total
		delivery_note_doc.terms = self.terms
		delivery_note_doc.terms_and_conditions = self.terms_and_conditions
		delivery_note_doc.address_line_1 = self.address_line_1
		delivery_note_doc.address_line_2 = self.address_line_2
		delivery_note_doc.area_name = self.area_name
		delivery_note_doc.country = self.country
		delivery_note_doc.quotation = self.quotation
		delivery_note_doc.sales_order = self.name

		# delivery_note_doc.save()

		idx = 0

		for item in self.items:
			idx = idx + 1
			delivery_note_item = frappe.new_doc("Delivery Note Item")
			delivery_note_item.warehouse = item.warehouse
			delivery_note_item.item = item.item
			delivery_note_item.item_name = item.item_name
			delivery_note_item.display_name = item.display_name
			delivery_note_item.qty =item.qty
			delivery_note_item.unit = item.unit
			delivery_note_item.rate = item.rate
			delivery_note_item.base_unit = item.base_unit
			delivery_note_item.qty_in_base_unit = item.qty_in_base_unit
			delivery_note_item.rate_in_base_unit = item.rate_in_base_unit
			delivery_note_item.conversion_factor = item.conversion_factor
			delivery_note_item.rate_includes_tax = item.rate_includes_tax
			delivery_note_item.rate_excluded_tax = item.rate_excluded_tax
			delivery_note_item.gross_amount = item.gross_amount
			delivery_note_item.tax_excluded = item.tax_excluded
			delivery_note_item.tax = item.tax
			delivery_note_item.tax_rate = item.tax_rate
			delivery_note_item.tax_amount = item.tax_amount
			delivery_note_item.discount_percentage = item.discount_percentage
			delivery_note_item.discount_amount = item.discount_amount
			delivery_note_item.net_amount = item.net_amount
			delivery_note_item.cost_center = item.cost_center
			delivery_note_item.unit_conversion_details = item.unit_conversion_details
			delivery_note_item.idx = idx
			delivery_note_item.sales_order_item_reference_no = item.name

			delivery_note_doc.append('items', delivery_note_item )
			#  target_items.append(target_item)

		delivery_note_doc.save()
		return {"delivery_note_name": delivery_note_doc.name}
