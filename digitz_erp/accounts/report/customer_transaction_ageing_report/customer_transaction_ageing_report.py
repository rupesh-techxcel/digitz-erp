# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from digitz_erp.accounts.doctype.gl_posting.gl_posting import get_party_balance

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data
   
def get_data(filters):
	filters = filters or {}
	customer_filter = filters.get('customer', '')
	date_filter = filters.get('from_date')

	sql_query = """
	SELECT
	si.customer,
	MAX(si.posting_date) AS latest_posting_date,
	DATEDIFF(CURDATE(), MAX(si.posting_date)) AS ageing
	FROM
	`tabSales Invoice` si
	WHERE
	si.docstatus = 1
	"""

	# Applying customer filter if provided
	if customer_filter:
		sql_query += " AND si.customer = %s" % frappe.db.escape(customer_filter)
  
	if date_filter:
		sql_query += " AND si.posting_date>=%s" % frappe.db.escape(date_filter)
  


	# Group by customer and order by ageing in descending order
	sql_query += """
	GROUP BY
	si.customer
	ORDER BY
	ageing DESC
	"""

	latest_customer_posting_dates = frappe.db.sql(sql_query, as_dict=True)

	for customer_data in latest_customer_posting_dates:
		customer = customer_data.get('customer')
		if customer:
			balance_details = get_party_balance(party_type='Customer', party=customer)
			customer_data['current_outstanding'] = balance_details

	return latest_customer_posting_dates

def get_columns(filters):
    return [
     	{		
			"fieldname": "customer",
			"fieldtype": "Link",
			"label": "Customer",
			"options": "Customer",
			"width": 450,	
		},
		{		
			"fieldname": "latest_posting_date",
			"fieldtype": "Date",
			"label": "Last Sale Date",			
			"width": 120,	
		},
		{		
			"fieldname": "ageing",
			"fieldtype": "int",
			"label": "Ageing in Days",			
			"width": 100,	
		},
		{
			"fieldname": "current_outstanding",
			"fieldtype": "Currency",
			"label": "Current Outstanding",			
			"width": 150,
		}
  
  ]
