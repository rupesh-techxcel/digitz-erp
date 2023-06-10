# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	if(filters.get('customer')):
		columns = get_columns()
	else:
		columns = get_columns_with_customer()

	data = get_data(filters)
	return columns, data

def get_data(filters):
	data = ""
 
	print("case 1")
	 
	if filters.get('customer') and  filters.get('from_date') and filters.get('to_date'):     
		

		data = frappe.db.sql("""
		SELECT
		si.name AS sales_invoice_name,
		si.posting_date AS posting_date,
		CASE
			WHEN si.docstatus = 1 THEN 'Submitted'
			WHEN si.docstatus = 0 THEN 'Draft'
			WHEN si.docstatus = 2 THEN 'Cancelled'
			ELSE ''
		END AS docstatus,
		si.rounded_total AS amount,
		si.ship_to_location AS 'ship_to_location',
		si.payment_mode,
  		si.payment_account
		FROM
		`tabSales Invoice` si
		WHERE
		si.credit_sale = 0
		AND si.customer = '{0}'
		AND si.posting_date BETWEEN '{1}' AND '{2}'
		ORDER BY
		si.posting_date
		""".format(filters.get('customer'), filters.get('from_date'), filters.get('to_date')), as_dict=True)
  
  		# data = frappe.db.sql(""" SELECT si.name as sales_invoice_name,si.posting_date as posting_date,si.rounded_total as amount,si.paid_amount,si.rounded_total - IFNULL(si.paid_amount,0) as balance_amount,si.delivery_note as delivery_note,si.ship_to_location as 'ship_to_location' FROM `tabSales Invoice` si  where si.docstatus = 0 and si.credit_sale=1 and si.customer = '{0}' and si.posting_date BETWEEN '{1}' and '{2}'  order by si.posting_date""".format(filters.get('customer'),filters.get('from_date'),filters.get('to_date')),as_dict=True)
  
	elif filters.get('from_date') and filters.get('to_date') and not(filters.get('customer')):
		print("case 2")
		data = frappe.db.sql("""
		SELECT
		si.customer,
		si.name AS sales_invoice_name,
		si.posting_date,
		CASE
			WHEN si.docstatus = 1 THEN 'Submitted'
			WHEN si.docstatus = 0 THEN 'Draft'
			WHEN si.docstatus = 2 THEN 'Cancelled'
			ELSE ''
		END AS docstatus,
		si.posting_date,
		si.rounded_total AS amount,		
		si.delivery_note AS delivery_note,
		si.ship_to_location AS ship_to_location,
		si.payment_mode,
		si.payment_account
		FROM
		`tabSales Invoice` si
		WHERE
		si.credit_sale = 0
		AND si.posting_date BETWEEN '{0}' AND '{1}'
		ORDER BY
		si.posting_date
		""".format(filters.get('from_date'), filters.get('to_date')), as_dict=True)

	elif filters.get('customer') and not(filters.get('from_date') and filters.get('to_date')):
		data = frappe.db.sql("""
		SELECT
		si.name AS sales_invoice_name,
		si.posting_date,
		CASE
			WHEN si.docstatus = 1 THEN 'Submitted'
			WHEN si.docstatus = 0 THEN 'Draft'
			WHEN si.docstatus = 2 THEN 'Cancelled'
			ELSE ''
		END AS docstatus,
		si.rounded_total AS amount,
		si.delivery_note AS delivery_note,
		si.ship_to_location AS ship_to_location,
		si.payment_mode,
  		si.payment_account

		FROM
		`tabSales Invoice` si
		WHERE
		si.credit_sale = 0
		AND si.customer = '{0}'
		ORDER BY
		posting_date
		""".format(filters.get('customer')), as_dict=True)
	else:
		data = frappe.db.sql("""
			SELECT
				si.customer,
				si.name AS sales_invoice_name,
				si.posting_date AS posting_date,
				CASE
					WHEN si.docstatus = 1 THEN 'Submitted'
					WHEN si.docstatus = 0 THEN 'Draft'
					WHEN si.docstatus = 2 THEN 'Cancelled'
					ELSE ''
				END AS docstatus,
				si.rounded_total AS amount,
				si.modepayment_mode,
  				si.payment_account
				si.delivery_note AS delivery_note,
				si.ship_to_location AS ship_to_location
			FROM
				`tabSales Invoice` si
			WHERE
				si.credit_sale = 0
			ORDER BY
				posting_date
			""", as_dict=True)

	for dl in data:
		delivery_note_name = frappe.db.get_value("Sales Invoice Delivery Notes",{"parent":dl.get('sales_invoice_name')},'delivery_note')

		dl.update({"delivery_note":delivery_note_name})

	return data

def get_columns():
	return [
		{
		
			"fieldname": "sales_invoice_name",
			"fieldtype": "Link",
			"label": "Invoice No",
			"options": "Sales Invoice",
			"width": 150,
	
		},
		{
		
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"label": "Date",
			"width": 120,	
		},
  		{
		
			"fieldname": "docstatus",
			"fieldtype": "Data",
			"label": "Status",
			"width": 120,
	
		},
		# {
		
		# 	"fieldname": "ship_to_location",
		# 	"fieldtype": "Data",
		# 	"label": "Delivery Location",
		# 	"width": 120,
	
		# },
		# {
		
		# 	"fieldname": "delivery_note",
		# 	"fieldtype": "Data",
		# 	"label": "Delivery Note",
		# 	"width": 150,
	
		# },
		{
		
			"fieldname": "amount",
			"fieldtype": "Currency",
			"label": "Invoice Amount",
			"width": 120,
	
		},
  		{
			"fieldname": "payment_mode",
			"fieldtype": "Data",
			"label": "Payment Mode",
			"width": 120,	
		},
		{
			"fieldname": "payment_account",
			"fieldtype": "Data",
			"label": "Payment Account",
			"width": 120,	
		}
	]

def get_columns_with_customer():
	return [
		{
		
			"fieldname": "customer",
			"fieldtype": "Link",
			"label": "Customer",
			"options": "Customer",
			"width": 150,	
		},
  		{
		
			"fieldname": "sales_invoice_name",
			"fieldtype": "Link",
			"label": "Invoice No",
			"options": "Sales Invoice",
			"width": 150,
	
		},
		{
		
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"label": "Date",
			"width": 120,
	
		},
  		{
		
			"fieldname": "docstatus",
			"fieldtype": "Data",
			"label": "Status",
			"width": 120,
	
		},
		# {
		
		# 	"fieldname": "ship_to_location",
		# 	"fieldtype": "Data",
		# 	"label": "Delivery Location",
		# 	"width": 120,
	
		# },
		# {
		
		# 	"fieldname": "delivery_note",
		# 	"fieldtype": "Data",
		# 	"label": "Delivery Note",
		# 	"width": 150,
	
		# },
		{
		
			"fieldname": "amount",
			"fieldtype": "Currency",
			"label": "Invoice Amount",
			"width": 120,
	
		},
  		{
			"fieldname": "payment_mode",
			"fieldtype": "Data",
			"label": "Payment Mode",			
			"width": 120,	
		},
		{
			"fieldname": "payment_account",
			"fieldtype": "LInk",
			"label": "Account",
			"options": "Account" ,
			"width": 120,	
		}
	]

