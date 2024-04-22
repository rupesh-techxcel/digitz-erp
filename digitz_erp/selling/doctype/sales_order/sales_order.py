# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.sales_order_api import check_pending_items_exists
from digitz_erp.api.item_price_api import update_customer_item_price

class SalesOrder(Document):
	 
	def before_validate(self):
     
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
	def generate_sales_order(self):

		sales_order = frappe.new_doc('Sales Order')

		sales_order.customer = self.customer
		sales_order.customer_name = self.customer_name
		sales_order.customer_display_name = self.customer_display_name
		sales_order.customer_address = self.customer_address        
		sales_order.posting_date = self.posting_date
		sales_order.posting_time = self.posting_time
		sales_order.ship_to_location = self.ship_to_location
		sales_order.salesman = self.salesman
		sales_order.salesman_code = self.salesman_code
		sales_order.tax_id = self.tax_id
		
		sales_order.price_list = self.price_list
		sales_order.rate_includes_tax = self.rate_includes_tax
		sales_order.warehouse = self.warehouse        
		sales_order.credit_sale = self.credit_sale
		sales_order.credit_days = self.credit_days
		sales_order.payment_terms = self.payment_terms
		sales_order.payment_mode = self.payment_mode
		sales_order.payment_account = self.payment_account
		sales_order.remarks = self.remarks
		sales_order.gross_total = self.gross_total
		sales_order.total_discount_in_line_items = self.total_discount_in_line_items
		sales_order.tax_total = self.tax_total
		sales_order.net_total = self.net_total
		sales_order.round_off = self.round_off
		sales_order.rounded_total = self.rounded_total
		sales_order.terms = self.terms
		sales_order.terms_and_conditions = self.terms_and_conditions
		sales_order.auto_generated_from_delivery_note = False
		sales_order.address_line_1 = self.address_line_1
		sales_order.address_line_2 = self.address_line_2
		sales_order.area_name = self.area_name
		sales_order.country = self.country
		sales_order.company = self.company


		idx = 0

		for item in self.items:
			idx = idx + 1
			sales_order_item = frappe.new_doc("Sales Order Item")
			sales_order_item.warehouse = item.warehouse
			sales_order_item.item = item.item
			sales_order_item.item_name = item.item_name
			sales_order_item.display_name = item.display_name
			sales_order_item.qty =item.qty
			sales_order_item.unit = item.unit
			sales_order_item.rate = item.rate
			sales_order_item.base_unit = item.base_unit
			sales_order_item.qty_in_base_unit = item.qty_in_base_unit
			sales_order_item.rate_in_base_unit = item.rate_in_base_unit
			sales_order_item.conversion_factor = item.conversion_factor
			sales_order_item.rate_includes_tax = item.rate_includes_tax
			sales_order_item.rate_excluded_tax = item.rate_excluded_tax
			sales_order_item.gross_amount = item.gross_amount
			sales_order_item.tax_excluded = item.tax_excluded
			sales_order_item.tax = item.tax
			sales_order_item.tax_rate = item.tax_rate
			sales_order_item.tax_amount = item.tax_amount
			sales_order_item.discount_percentage = item.discount_percentage
			sales_order_item.discount_amount = item.discount_amount
			sales_order_item.net_amount = item.net_amount
			sales_order_item.unit_conversion_details = item.unit_conversion_details
			sales_order_item.idx = idx

			sales_order.append('items', sales_order_item)            

		sales_order.save()

		frappe.msgprint("Sales Order duplicated successfully.",indicator="green", alert=True)
		
		return sales_order.name

@frappe.whitelist()
def generate_do(sales_order_name):

	pending_items= check_pending_items_exists(sales_order_name)

	if not pending_items:
		frappe.throw("No pending items in the Sales Order to generate a Delivery Note.")  

	sales_order_doc = frappe.get_doc("Sales Order", sales_order_name)

	delivery_note_doc = frappe.new_doc('Delivery Note')
	delivery_note_doc.company = sales_order_doc.company		
	delivery_note_doc.customer = sales_order_doc.customer
	delivery_note_doc.customer_name = sales_order_doc.customer_name
	delivery_note_doc.customer_display_name = sales_order_doc.customer_display_name
	delivery_note_doc.customer_address = sales_order_doc.customer_address
	delivery_note_doc.reference_no = sales_order_doc.reference_no
	delivery_note_doc.posting_date = sales_order_doc.posting_date
	delivery_note_doc.posting_time = sales_order_doc.posting_time
	delivery_note_doc.ship_to_location = sales_order_doc.ship_to_location
	delivery_note_doc.salesman = sales_order_doc.salesman
	delivery_note_doc.salesman_code = sales_order_doc.salesman_code
	delivery_note_doc.tax_id = sales_order_doc.tax_id
	delivery_note_doc.lpo_no = sales_order_doc.lpo_no
	delivery_note_doc.lpo_date = sales_order_doc.lpo_date
	delivery_note_doc.price_list = sales_order_doc.price_list
	delivery_note_doc.rate_includes_tax = sales_order_doc.rate_includes_tax
	delivery_note_doc.warehouse = sales_order_doc.warehouse
	delivery_note_doc.credit_sale = sales_order_doc.credit_sale
	delivery_note_doc.credit_days = sales_order_doc.credit_days
	delivery_note_doc.payment_terms = sales_order_doc.payment_terms
	delivery_note_doc.payment_mode = sales_order_doc.payment_mode
	delivery_note_doc.payment_account = sales_order_doc.payment_account
	delivery_note_doc.remarks = sales_order_doc.remarks
	delivery_note_doc.gross_total = sales_order_doc.gross_total
	delivery_note_doc.total_discount_in_line_items = sales_order_doc.total_discount_in_line_items
	delivery_note_doc.tax_total = sales_order_doc.tax_total
	delivery_note_doc.net_total = sales_order_doc.net_total
	delivery_note_doc.round_off = sales_order_doc.round_off
	delivery_note_doc.rounded_total = sales_order_doc.rounded_total
	delivery_note_doc.terms = sales_order_doc.terms
	delivery_note_doc.terms_and_conditions = sales_order_doc.terms_and_conditions		
	delivery_note_doc.address_line_1 = sales_order_doc.address_line_1
	delivery_note_doc.address_line_2 = sales_order_doc.address_line_2
	delivery_note_doc.area_name = sales_order_doc.area_name
	delivery_note_doc.country = sales_order_doc.country
	delivery_note_doc.quotation = sales_order_doc.quotation
	delivery_note_doc.sales_order = sales_order_doc.name

	delivery_note_doc.append('sales_orders', {
		'sales_order': sales_order_doc.name
	})

	print(delivery_note_doc)

	idx = 0

	for item in sales_order_doc.items:
		
		if(item.qty_in_base_unit > item.qty_sold_in_base_unit):
			idx = idx + 1
			delivery_note_item = frappe.new_doc("Delivery Note Item")
			delivery_note_item.warehouse = item.warehouse
			delivery_note_item.item = item.item
			delivery_note_item.item_name = item.item_name
			delivery_note_item.display_name = item.display_name
			delivery_note_item.qty = (item.qty_in_base_unit - item.qty_sold_in_base_unit)/ item.conversion_factor
			delivery_note_item.unit = item.unit
			delivery_note_item.rate = item.rate_in_base_unit * item.conversion_factor
			delivery_note_item.base_unit = item.base_unit
			delivery_note_item.qty_in_base_unit = item.qty_in_base_unit - item.qty_sold_in_base_unit
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
			delivery_note_item.sales_order_item_reference_no = item.name

			delivery_note_doc.append('items', delivery_note_item )
		#  target_items.append(target_item)

	delivery_note_doc.insert()
	frappe.db.commit()

	print(delivery_note_doc)

	frappe.msgprint("Delivery Note generated successfully, in draft mode.",indicator="green", alert=True)
	return delivery_note_doc.name


@frappe.whitelist()
def generate_sales_invoice(sales_order_name):

	pending_items= check_pending_items_exists(sales_order_name)

	if not pending_items:
		frappe.throw("No pending items in the Sales Order to generate a Sales Invoice.")

	sales_order_doc = frappe.get_doc("Sales Order", sales_order_name)

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
		setattr(sales_invoice_doc, field, getattr(sales_order_doc, field, None))

	sales_invoice_doc.sales_order = sales_order_doc.name

	for item in sales_order_doc.items:
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

	sales_invoice_doc.insert()
	frappe.msgprint("Sales Invoice generated successfully, in draft mode.", alert=True)
	return sales_invoice_doc.name