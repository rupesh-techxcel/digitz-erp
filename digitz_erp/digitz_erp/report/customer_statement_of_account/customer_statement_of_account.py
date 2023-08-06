# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe import _, scrub
from frappe.utils import cint, flt, formatdate



def execute(filters=None):
	columns, data = [], []

	group_wise_columns = frappe.dict(
	{
		
	}		
  
	)


	return columns, data

 




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
		
			"fieldname": "ship_to_location",
			"fieldtype": "Data",
			"label": "Delivery Location",
			"width": 120,
	
		},
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
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"label": "Paid Amount",
			"width": 120,	
		},
  		{
			"fieldname": "balance_amount",
			"fieldtype": "Currency",
			"label": "Balance Amount",
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
		
			"fieldname": "ship_to_location",
			"fieldtype": "Data",
			"label": "Delivery Location",
			"width": 120,
	
		},
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
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"label": "Paid Amount",
			"width": 120,	
		},
  		{
			"fieldname": "balance_amount",
			"fieldtype": "Currency",
			"label": "Balance Amount",
			"width": 120,	
		}
	]
