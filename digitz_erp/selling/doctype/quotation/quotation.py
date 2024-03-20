# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.quotation_api import check_references_created 
from frappe.utils import money_in_words

class Quotation(Document):

	def before_validate(self):
		self.in_words = money_in_words(self.rounded_total,"AED")
  

@frappe.whitelist()
def generate_sale_invoice(quotation):

	check_references_created(quotation)
	quotation_doc = frappe.get_doc('Quotation',quotation)
	sales_invoice_doc = frappe.new_doc('Sales Invoice')
	sales_invoice_doc.company = quotation_doc.company		
	sales_invoice_doc.customer = quotation_doc.customer
	sales_invoice_doc.customer_name = quotation_doc.customer_name
	sales_invoice_doc.customer_display_name = quotation_doc.customer_display_name
	sales_invoice_doc.customer_address = quotation_doc.customer_address
	sales_invoice_doc.reference_no = quotation_doc.reference_no
	sales_invoice_doc.posting_date = quotation_doc.posting_date
	sales_invoice_doc.posting_time = quotation_doc.posting_time
	sales_invoice_doc.ship_to_location = quotation_doc.ship_to_location
	sales_invoice_doc.salesman = quotation_doc.salesman
	sales_invoice_doc.salesman_code = quotation_doc.salesman_code
	sales_invoice_doc.tax_id = quotation_doc.tax_id
	sales_invoice_doc.lpo_no = None
	sales_invoice_doc.lpo_date = None
	sales_invoice_doc.price_list = quotation_doc.price_list
	sales_invoice_doc.rate_includes_tax = quotation_doc.rate_includes_tax
	sales_invoice_doc.warehouse = quotation_doc.warehouse
	sales_invoice_doc.credit_sale = quotation_doc.credit_sale
	sales_invoice_doc.credit_days = quotation_doc.credit_days
	sales_invoice_doc.payment_terms = quotation_doc.payment_terms
	sales_invoice_doc.payment_mode = quotation_doc.payment_mode
	sales_invoice_doc.payment_account = quotation_doc.payment_account
	sales_invoice_doc.remarks = quotation_doc.remarks
	sales_invoice_doc.gross_total = quotation_doc.gross_total
	sales_invoice_doc.total_discount_in_line_items = quotation_doc.total_discount_in_line_items
	sales_invoice_doc.tax_total = quotation_doc.tax_total
	sales_invoice_doc.net_total = quotation_doc.net_total
	sales_invoice_doc.round_off = quotation_doc.round_off
	sales_invoice_doc.rounded_total = quotation_doc.rounded_total
	sales_invoice_doc.terms = quotation_doc.terms
	sales_invoice_doc.terms_and_conditions = quotation_doc.terms_and_conditions		
	sales_invoice_doc.address_line_1 = quotation_doc.address_line_1
	sales_invoice_doc.address_line_2 = quotation_doc.address_line_2
	sales_invoice_doc.area_name = quotation_doc.area_name
	sales_invoice_doc.country = quotation_doc.country
	sales_invoice_doc.quotation = quotation_doc.name

	idx = 0

	for item in quotation_doc.items:
		idx = idx + 1
		delivery_note_item = frappe.new_doc("Sales Invoice Item")
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
		delivery_note_item.unit_conversion_details = item.unit_conversion_details
		delivery_note_item.idx = idx
		delivery_note_item.quotation_item_reference_no = item.name

		sales_invoice_doc.append('items', delivery_note_item )
		#  target_items.append(target_item)

	sales_invoice_doc.insert()
	frappe.msgprint("Sales Invoice successfully created in draft mode.", indicator="green",alert
				=True)
	return sales_invoice_doc.name

@frappe.whitelist()
def generate_delivery_note(quotation):

	check_references_created(quotation)
	quotation_doc = frappe.get_doc('Quotation',quotation)
	delivery_note_doc = frappe.new_doc('Delivery Note')
	delivery_note_doc.company = quotation_doc.company		
	delivery_note_doc.customer = quotation_doc.customer
	delivery_note_doc.customer_name = quotation_doc.customer_name
	delivery_note_doc.customer_display_name = quotation_doc.customer_display_name
	delivery_note_doc.customer_address = quotation_doc.customer_address
	delivery_note_doc.reference_no = quotation_doc.reference_no
	delivery_note_doc.posting_date = quotation_doc.posting_date
	delivery_note_doc.posting_time = quotation_doc.posting_time
	delivery_note_doc.ship_to_location = quotation_doc.ship_to_location
	delivery_note_doc.salesman = quotation_doc.salesman
	delivery_note_doc.salesman_code = quotation_doc.salesman_code
	delivery_note_doc.tax_id = quotation_doc.tax_id
	delivery_note_doc.lpo_no = None
	delivery_note_doc.lpo_date = None
	delivery_note_doc.price_list = quotation_doc.price_list
	delivery_note_doc.rate_includes_tax = quotation_doc.rate_includes_tax
	delivery_note_doc.warehouse = quotation_doc.warehouse
	delivery_note_doc.credit_sale = quotation_doc.credit_sale
	delivery_note_doc.credit_days = quotation_doc.credit_days
	delivery_note_doc.payment_terms = quotation_doc.payment_terms
	delivery_note_doc.payment_mode = quotation_doc.payment_mode
	delivery_note_doc.payment_account = quotation_doc.payment_account
	delivery_note_doc.remarks = quotation_doc.remarks
	delivery_note_doc.gross_total = quotation_doc.gross_total
	delivery_note_doc.total_discount_in_line_items = quotation_doc.total_discount_in_line_items
	delivery_note_doc.tax_total = quotation_doc.tax_total
	delivery_note_doc.net_total = quotation_doc.net_total
	delivery_note_doc.round_off = quotation_doc.round_off
	delivery_note_doc.rounded_total = quotation_doc.rounded_total
	delivery_note_doc.terms = quotation_doc.terms
	delivery_note_doc.terms_and_conditions = quotation_doc.terms_and_conditions		
	delivery_note_doc.address_line_1 = quotation_doc.address_line_1
	delivery_note_doc.address_line_2 = quotation_doc.address_line_2
	delivery_note_doc.area_name = quotation_doc.area_name
	delivery_note_doc.country = quotation_doc.country
	delivery_note_doc.quotation = quotation_doc.name


	idx = 0

	for item in quotation_doc.items:
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
		delivery_note_item.unit_conversion_details = item.unit_conversion_details
		delivery_note_item.idx = idx
		delivery_note_item.quotation_item_reference_no = item.name

		delivery_note_doc.append('items', delivery_note_item )
		#  target_items.append(target_item)

	delivery_note_doc.insert()
	frappe.msgprint("Delivery Note successfully created in draft mode.", indicator="green",alert
				=True)
	return delivery_note_doc.name

@frappe.whitelist()
def generate_sales_order(quotation):
		
	quotation_doc =frappe.get_doc('Quotation',quotation)

	check_references_created(quotation)
	sales_order = quotation_doc.__dict__
	sales_order['doctype'] = 'Sales Order'
	# delivery_note['against_sales_invoice'] = delivery_note['name']
	# delivery_note['name'] = delivery_note_name
	sales_order['naming_series'] = ""
	sales_order['posting_date'] = quotation_doc.posting_date
	sales_order['posting_time'] = quotation_doc.posting_time
	sales_order["quotation"] = quotation_doc.name

	sales_order['docstatus'] = 0

	for item in sales_order['items']:
		item.doctype = "Sales Order Item"
		item.quotation_item_reference_no = item.name
		item._meta = ""

	new_so = frappe.get_doc(sales_order).insert()
	frappe.db.commit()
	frappe.msgprint("Sales Order successfully created in draft mode.", indicator="green", alert=True)
	print("new so created")
	return new_so.name


