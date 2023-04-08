# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_data(filters):
	data = ""
	if filters.get('customer'):
		data = frappe.db.sql(""" SELECT name as sales_invoice_name,posting_date as posting_date,rounded_total as amount,delivery_note as delivery_note,ship_to_location as ship_to_location FROM `tabSales Invoice` where docstatus = 0 and customer = '{}' """.format(filters.get('customer')),as_dict=True)

	else:
		data = frappe.db.sql(""" SELECT name as sales_invoice_name,posting_date as posting_date,rounded_total as amount,delivery_note as delivery_note,ship_to_location as ship_to_location FROM `tabSales Invoice` where docstatus = 0 """,as_dict=True)


	for dl in data:
		delivery_note_name = frappe.db.get_value("Sales Invoice Delivery Notes",{"parent":dl.get('sales_invoice_name')},'delivery_note')

		dl.update({"delivery_note":delivery_note_name})

	return data

def get_columns():
	return [
		{
		
			"fieldname": "sales_invoice_name",
			"fieldtype": "Link",
			"label": "Sales Invoice Name",
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
		
			"fieldname": "ship_to_location",
			"fieldtype": "Data",
			"label": "Shift To Location",
			"width": 120,
	
		},
		{
		
			"fieldname": "delivery_note",
			"fieldtype": "Data",
			"label": "Delivery Note",
			"width": 150,
	
		},
		{
		
			"fieldname": "amount",
			"fieldtype": "Float",
			"label": "Amount",
			"width": 120,
	
		}
	]
