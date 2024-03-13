# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SalesOrder(Document):
	
	@frappe.whitelist()
	def generate_sale_invoice(self):
     
		self.check_references_created()    
  
		sales_invoice_doc = frappe.new_doc('Sales Invoice')
  
		sales_invoice_doc.company = self.company		
		sales_invoice_doc.customer = self.customer
		sales_invoice_doc.customer_name = self.customer_name
		sales_invoice_doc.customer_display_name = self.customer_display_name
		sales_invoice_doc.customer_address = self.customer_address
		sales_invoice_doc.reference_no = self.reference_no
		sales_invoice_doc.posting_date = self.posting_date
		sales_invoice_doc.posting_time = self.posting_time
		sales_invoice_doc.ship_to_location = self.ship_to_location
		sales_invoice_doc.salesman = self.salesman
		sales_invoice_doc.salesman_code = self.salesman_code
		sales_invoice_doc.tax_id = self.tax_id
		sales_invoice_doc.lpo_no = self.lpo_no
		sales_invoice_doc.lpo_date = self.lpo_date
		sales_invoice_doc.price_list = self.price_list
		sales_invoice_doc.rate_includes_tax = self.rate_includes_tax
		sales_invoice_doc.warehouse = self.warehouse
		sales_invoice_doc.credit_sale = self.credit_sale
		sales_invoice_doc.credit_days = self.credit_days
		sales_invoice_doc.payment_terms = self.payment_terms
		sales_invoice_doc.payment_mode = self.payment_mode
		sales_invoice_doc.payment_account = self.payment_account
		sales_invoice_doc.remarks = self.remarks
		sales_invoice_doc.gross_total = self.gross_total
		sales_invoice_doc.total_discount_in_line_items = self.total_discount_in_line_items
		sales_invoice_doc.tax_total = self.tax_total
		sales_invoice_doc.net_total = self.net_total
		sales_invoice_doc.round_off = self.round_off
		sales_invoice_doc.rounded_total = self.rounded_total
		sales_invoice_doc.terms = self.terms
		sales_invoice_doc.terms_and_conditions = self.terms_and_conditions		
		sales_invoice_doc.address_line_1 = self.address_line_1
		sales_invoice_doc.address_line_2 = self.address_line_2
		sales_invoice_doc.area_name = self.area_name
		sales_invoice_doc.country = self.country
		sales_invoice_doc.quotation = self.quotation
		sales_invoice_doc.sales_order = self.name

		sales_invoice_doc.save()
		
		idx = 0

		for item in self.items:
			idx = idx + 1
			sales_invoice_item = frappe.new_doc("Sales Invoice Item")
			sales_invoice_item.warehouse = item.warehouse
			sales_invoice_item.item = item.item
			sales_invoice_item.item_name = item.item_name
			sales_invoice_item.display_name = item.display_name
			sales_invoice_item.qty =item.qty
			sales_invoice_item.unit = item.unit
			sales_invoice_item.rate = item.rate
			sales_invoice_item.base_unit = item.base_unit
			sales_invoice_item.qty_in_base_unit = item.qty_in_base_unit
			sales_invoice_item.rate_in_base_unit = item.rate_in_base_unit
			sales_invoice_item.conversion_factor = item.conversion_factor
			sales_invoice_item.rate_includes_tax = item.rate_includes_tax
			sales_invoice_item.rate_excluded_tax = item.rate_excluded_tax
			sales_invoice_item.gross_amount = item.gross_amount
			sales_invoice_item.tax_excluded = item.tax_excluded
			sales_invoice_item.tax = item.tax
			sales_invoice_item.tax_rate = item.tax_rate
			sales_invoice_item.tax_amount = item.tax_amount
			sales_invoice_item.discount_percentage = item.discount_percentage
			sales_invoice_item.discount_amount = item.discount_amount
			sales_invoice_item.net_amount = item.net_amount
			sales_invoice_item.unit_conversion_details = item.unit_conversion_details
			sales_invoice_item.idx = idx
			sales_invoice_item.sales_order_item_reference_no = item.name

			sales_invoice_doc.append('items', sales_invoice_item )
			#  target_items.append(target_item)

		sales_invoice_doc.save()
		frappe.msgprint("Sales invoice generated successfully, in draft mode.", alert=True)

	@frappe.whitelist()
	def generate_delivery_note(self):
     
		self.check_references_created()    
  
		delivery_note_doc = frappe.new_doc('Delivery Note')
		delivery_note_doc.compay = self.company		
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

		delivery_note_doc.save()
		
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
			delivery_note_item.unit_conversion_details = item.unit_conversion_details
			delivery_note_item.idx = idx
			delivery_note_item.sales_order_item_reference_no = item.name

			delivery_note_doc.append('items', delivery_note_item )
			#  target_items.append(target_item)

		delivery_note_doc.save()
    
	# @frappe.whitelist()
	# def generate_sale_invoice(self):
		
	# 	self.check_references_created()    

	# 	sales_invoice_name = ""  		
	# 	sales_order_name =  self.name
	# 	sales_invoice = self.__dict__
	# 	sales_invoice['doctype'] = 'Sales Invoice'
	# 	sales_invoice['name'] = sales_invoice_name
	# 	sales_invoice['naming_series'] = ""
	# 	sales_invoice['posting_date'] = self.posting_date
	# 	sales_invoice['posting_time'] = self.posting_time
	# 	sales_invoice['sales_order'] = sales_order_name
		
	# 	# Change the document status to draft to avoid error while submitting child table
	# 	sales_invoice['docstatus'] = 0

	# 	for item in sales_invoice['items']:            
	# 		item.doctype = "Sales Invoice Item"		
	# 		item.sales_order_item_reference_no = item.name  
	# 		item._meta = ""  

	# 		print(item)
			
	# 	frappe.get_doc(sales_invoice).insert(ignore_permissions=True)  
		
	# 	frappe.db.commit()

	# 	frappe.msgprint("Sales Invoice created successfully with draft mode.", alert=1)
		
	# @frappe.whitelist()
	# def generate_delivery_note(self):
		
	# 	self.check_references_created()
  
	# 	delivery_note = self.__dict__
	# 	delivery_note['doctype'] = 'Delivery Note'
	# 	# delivery_note['against_sales_invoice'] = delivery_note['name']
	# 	# delivery_note['name'] = delivery_note_name        
	# 	delivery_note['naming_series'] = ""
	# 	delivery_note['posting_date'] = self.posting_date
	# 	delivery_note['posting_time'] = self.posting_time
	# 	delivery_note["sales_order"] = self.name		
	# 	delivery_note['docstatus'] = 0

	# 	for item in delivery_note['items']:
	# 		item.doctype = "Delivery Note Item"
	# 		item.sales_order_item_reference_no = item.name
	# 		item._meta = "" 

	# 	doNo = frappe.get_doc(delivery_note).insert()
	# 	frappe.db.commit()
	# 	frappe.msgprint("Delivery successfully created in draft mode")

	def check_references_created(self):
		
		sales_order_exists_for_invoice = frappe.db.exists("Sales Invoice", {"sales_order": self.name}) 

		if sales_order_exists_for_invoice:
			frappe.throw("Sales Invoice exists for the sales order and cannot create additional references.")
  
		sales_order_exists_for_delivery_note = frappe.db.exists("Delivery Note", {"sales_order": self.name}) 
  
		if sales_order_exists_for_delivery_note:
			frappe.throw("Delivery Note exists for the sales order and canoot create additional references.")

		