# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):    
	
	if(filters.get('group_by')  == "Invoice"):
     
		if(filters.get('customer')):		
			columns = get_columns()
		else:
			columns = get_columns_with_customer()  
   
		data = get_data(filters)
  
	else:
		columns = get_columns_for_customer_group()
		data = get_data_customer_wise(filters)
  
	if filters.get('show_pending_only'):
		data = [
			row for row in data if 
			(row.get('doc_type') == 'Sales Invoice' and row.get('balance_amount', 0) > 0) or 
			(row.get('doc_type') == 'Sales Return' and row.get('balance_amount', 0) < 0) or 
			(row.get('doc_type') == 'Credit Note' and row.get('balance_amount', 0) < 0)
		]    
  
	chart = get_chart_data()
 
	return columns, data, None, chart

def get_chart_data():
     # Query to fetch the top 20 customers by total invoice amount
	query = """
			SELECT 
				customer_name, 
				SUM(total_invoice_amount) as total_invoice_amount
			FROM (
				SELECT 
					si.customer as customer_name, 
					si.rounded_total as total_invoice_amount
				FROM 
					`tabSales Invoice` si
				WHERE 
					si.docstatus = 1 OR si.docstatus = 0
				
				UNION ALL
				
				SELECT 
					psi.customer as customer_name, 
					psi.rounded_total as total_invoice_amount
				FROM 
					`tabProgressive Sales Invoice` psi
				WHERE 
					psi.docstatus = 1
			) as combined_invoices
			GROUP BY 
				customer_name
			ORDER BY 
				total_invoice_amount DESC
			LIMIT 20
			"""


	data = frappe.db.sql(query, as_dict=True)

	# Prepare the data for chart representation
	chart_data = {
		'labels': [row['customer_name'] for row in data],
		'datasets': [{
			'name': 'Total Invoice Amount',
			'values': [row['total_invoice_amount'] for row in data]
		}]
	}

	# Chart configuration
	chart = {
		'data': chart_data,
		'type': 'bar',  # Can be 'line', 'scatter', 'pie', etc. depending on your needs
		'title': 'Top 20 Customers by Invoice Amount'
	}

	return chart


def get_data_customer_wise(filters):
    
	customer_condition = "customer = '{}'".format(filters.get('customer')) if filters.get('customer') else "1=1"
	date_condition = "posting_date BETWEEN '{0}' AND '{1}'".format(filters.get('from_date'), filters.get('to_date')) if filters.get('from_date') and filters.get('to_date') else "1=1"
	opening_date_condition = "posting_date < '{}'".format(filters.get('from_date')) if filters.get('from_date') else "1=1"

	invoice_query = f"""
		SELECT 
			customer,
			rounded_total,
			paid_amount,
			posting_date
		FROM `tabSales Invoice`
		WHERE 
			(docstatus = 1 or docstatus = 0) 
			AND credit_sale = 1 
			AND {customer_condition}
			AND ({date_condition} OR {opening_date_condition})
	"""

	progressive_invoice_query = f"""
		SELECT 
			customer,
			rounded_total,
			paid_amount,
			posting_date
		FROM `tabProgressive Sales Invoice`
		WHERE 
			(docstatus = 1 or docstatus = 0) 
			AND credit_sale = 1 
			AND {customer_condition}
			AND ({date_condition} OR {opening_date_condition})
	"""

	return_query = f"""
		SELECT 
			customer,
			rounded_total * -1 as rounded_total,
			paid_amount * -1 as paid_amount,
			posting_date
		FROM `tabSales Return`
		WHERE 
			(docstatus = 1 or docstatus = 0) 
			AND credit_sale = 1 
			AND {customer_condition}
			AND ({date_condition} OR {opening_date_condition})
	"""

	combined_query = f"""
		SELECT 
			c.customer_name as customer,
			ROUND(SUM(CASE WHEN si.posting_date < '{filters.get('from_date')}' THEN 0 ELSE si.rounded_total END), 2) as invoice_amount,
			ROUND(SUM(CASE WHEN si.posting_date < '{filters.get('from_date')}' THEN 0 ELSE si.paid_amount END), 2) as paid_amount,
			ROUND(SUM(si.rounded_total) - SUM(IFNULL(si.paid_amount, 0)), 2) as balance_amount,
			ROUND(SUM(CASE WHEN si.posting_date < '{filters.get('from_date')}' THEN si.rounded_total - IFNULL(si.paid_amount, 0) ELSE 0 END), 2) as opening_balance
		FROM (
			{invoice_query}
			UNION ALL
			{progressive_invoice_query}
			UNION ALL
			{return_query}
		) AS si
		LEFT JOIN `tabCustomer` c ON si.customer = c.name
		WHERE (c.exclude_from_showing_in_soa IS NULL OR c.exclude_from_showing_in_soa = 0)
		GROUP BY c.customer_name
		HAVING ROUND(SUM(si.rounded_total) - SUM(IFNULL(si.paid_amount, 0)), 2) != 0
		ORDER BY balance_amount DESC
	"""

	return frappe.db.sql(combined_query, as_dict=True)
    
def get_data(filters):
    
	# Define the base fields common in both tables, but handle customer_name outside of this since it's fetched via JOIN
	invoice_fields = """
		si.name as sales_invoice_name,
		si.posting_date as posting_date,
		si.rounded_total as amount,
		si.paid_amount,
		si.rounded_total - COALESCE(si.paid_amount, 0) as balance_amount,
		si.ship_to_location as 'ship_to_location'
	"""
 
	progressive_invoice_fields = """
		si.name as sales_invoice_name,
		si.posting_date as posting_date,
		si.rounded_total as amount,
		si.paid_amount,
		si.rounded_total - COALESCE(si.paid_amount, 0) as balance_amount,
		si.ship_to_location as 'ship_to_location'
	"""

	return_fields = """
		si.name as sales_invoice_name,
		si.posting_date as posting_date,
		si.rounded_total*-1 as amount,
		si.paid_amount * -1 as paid_amount,
		(si.rounded_total - COALESCE(si.paid_amount, 0))*-1 as balance_amount,
		si.ship_to_location as 'ship_to_location'
	"""

	# invoice_fields = invoice_fields + ", si.delivery_note as delivery_note"
	invoice_fields = invoice_fields + ", '' as delivery_note"
	progressive_invoice_fields = progressive_invoice_fields + ", '' as delivery_note"
	return_fields = return_fields + ", '' as delivery_note"  # Assuming 'delivery_note' does not exist in 'tabSales Return'

	opening_balance_date_condition = f"AND si.posting_date < '{filters.get('from_date')}'" if filters.get('from_date') else ""
	customer_condition = f"AND si.customer = '{filters.get('customer')}'" if filters.get('customer') else ""
	date_condition = f"AND si.posting_date BETWEEN '{filters.get('from_date')}' AND '{filters.get('to_date')}'" if filters.get('from_date') and filters.get('to_date') else ""


	invoice_query = f"""
	SELECT 
		{invoice_fields},'Sales Invoice' as doc_type ,
		c.customer_name as customer_name
	FROM 
		`tabSales Invoice` si 
	LEFT JOIN
		`tabCustomer` c ON si.customer = c.name
	WHERE 
		(si.docstatus = 1 or si.docstatus = 0) 
		AND si.credit_sale = 1 
		{customer_condition}
		{date_condition}
		AND (c.exclude_from_showing_in_soa IS NULL OR c.exclude_from_showing_in_soa = 0)
	"""
	progressive_invoice_query = f"""
	SELECT 
		{progressive_invoice_fields},'Progressive Sales Invoice' as doc_type ,
		c.customer_name as customer_name
	FROM 
		`tabProgressive Sales Invoice` si 
	LEFT JOIN
		`tabCustomer` c ON si.customer = c.name
	WHERE 
		(si.docstatus = 1 or si.docstatus = 0)
		AND si.credit_sale = 1 
		{customer_condition}
		{date_condition}
		AND (c.exclude_from_showing_in_soa IS NULL OR c.exclude_from_showing_in_soa = 0)
	"""

	return_query = f"""
	SELECT 
		{return_fields},'Sales Return' as doc_type ,
		c.customer_name as customer_name
	FROM 
		`tabSales Return` si 
	LEFT JOIN
		`tabCustomer` c ON si.customer = c.name
	WHERE 
		(si.docstatus = 1 or si.docstatus = 0) 
		AND si.credit_sale = 1 
		{customer_condition}
		{date_condition}
		AND (c.exclude_from_showing_in_soa IS NULL OR c.exclude_from_showing_in_soa = 0)
	"""

	# invoice_fields = """
	# 	si.name as sales_invoice_name,
	# 	si.posting_date as posting_date,
	# 	si.rounded_total as amount,
	# 	si.paid_amount,
	# 	si.rounded_total - COALESCE(si.paid_amount, 0) as balance_amount,
	# 	si.ship_to_location as 'ship_to_location'
	# """
	# progressive_invoice_fields = """
	# 	si.name as sales_invoice_name,
	# 	si.posting_date as posting_date,
	# 	si.rounded_total as amount,
	# 	si.paid_amount,
	# 	si.rounded_total - COALESCE(si.paid_amount, 0) as balance_amount,
	# 	si.ship_to_location as 'ship_to_location'
	# """
	opening_balance_query = f"""

	SELECT 'Opening Balance' as sales_invoice_name,
		MAX(si.posting_date) as posting_date,
		0 as amount, 
		0 as paid_amount,
		SUM(si.balance_amount) as balance_amount,
		'' as 'ship_to_location',
		'' as delivery_note,
		'' as doc_type,
		c.customer_name as customer_name        
	FROM  
		(
		SELECT 
			si.customer, 
			si.posting_date, 
			si.rounded_total - COALESCE(si.paid_amount, 0) as balance_amount
		FROM 
			`tabSales Invoice` si
		WHERE 
			si.docstatus = 1 
			AND si.credit_sale = 1
			AND (si.rounded_total - COALESCE(si.paid_amount, 0))>0 
			{customer_condition}
			{opening_balance_date_condition} 
		UNION ALL
		SELECT 
			si.customer, 
			si.posting_date, 
			si.rounded_total - COALESCE(si.paid_amount, 0) as balance_amount
		FROM 
			`tabProgressive Sales Invoice` si
		WHERE 
			si.docstatus = 1 
			AND si.credit_sale = 1
			AND (si.rounded_total - COALESCE(si.paid_amount, 0))>0 
			{customer_condition}
			{opening_balance_date_condition} 
		UNION ALL
		SELECT 
			si.customer, 
			si.posting_date, 
			(si.rounded_total - COALESCE(si.paid_amount, 0)) * -1 as balance_amount
		FROM 
			`tabSales Return` si
		WHERE 
			si.docstatus = 1 
			AND si.credit_sale = 1
			AND (si.rounded_total - COALESCE(si.paid_amount, 0))>0
			{customer_condition}
			{opening_balance_date_condition}
	) as si
	LEFT JOIN
		`tabCustomer` c ON si.customer = c.name
	WHERE
		(c.exclude_from_showing_in_soa IS NULL OR c.exclude_from_showing_in_soa = 0)
	GROUP BY c.customer_name 
	"""

	# Adjusted final query to include opening balance
	final_query = f"""
	SELECT * FROM (
		{opening_balance_query} 
		UNION ALL 
		{invoice_query} 
		UNION ALL 
		{progressive_invoice_query} 
		UNION ALL 
		{return_query}
	) as combined
	ORDER BY combined.customer_name, combined.posting_date
	"""

	data = frappe.db.sql(final_query, as_dict=True)

	# Assuming the delivery_note is relevant only for invoices
	for dl in data:
		if 'sales_invoice_name' in dl and 'tabSales Invoice' in dl['sales_invoice_name']:
			delivery_note_name = frappe.db.get_value("Sales Invoice Delivery Notes", {"parent": dl.get('sales_invoice_name')}, 'delivery_note')
			dl.update({"delivery_note": delivery_note_name or dl.get('delivery_note')})

	return data

def get_columns():
	return [
    
    	{
		
			"fieldname": "doc_type",
			"fieldtype": "Data",
			"label": "Document Type",			
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

def get_columns_with_customer():
	return [
		{
		
			"fieldname": "customer_name",
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

def get_columns_for_customer_group():
	return [
		{
		
			"fieldname": "customer",
			"fieldtype": "Link",
			"label": "Customer",
			"options": "Customer",
			"width": 300,	
		},		
		{		
			"fieldname": "opening_balance",
			"fieldtype": "Currency",
			"label": "Opening Balance",
			"width": 180,
	
		},
		{		
			"fieldname": "invoice_amount",
			"fieldtype": "Currency",
			"label": "Invoice Amount",
			"width": 180,	
		},
		{
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"label": "Paid Amount",
			"width": 180,	
		},
  		{
			"fieldname": "balance_amount",
			"fieldtype": "Currency",
			"label": "Balance Amount",
			"width": 180,	
		}
	]
