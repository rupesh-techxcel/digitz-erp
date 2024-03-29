# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns, data = [], []

	if filters.get("group_by") == "Date":
		columns = get_columns_datewise()
		data = get_data_datewise(filters)

	elif filters.get("group_by") == "Customer":
		columns = get_columns_customerwise()
		data = get_data_customerwise(filters)

	elif filters.get("group_by") == "Customer And Date":
		columns = get_columns_customer_and_datewise()
		data = get_data_customer_and_datewise(filters)

	elif filters.get("group_by") == "None":
		columns = get_columns()
		data = get_data(filters)

	return columns, data

def get_data(filters):

	trans_data =[]

	if filters.get("customer") and filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		customer,document_no,document_date,amount,scheduled_date
		FROM
		`tabReceipt Schedule` rs
		WHERE rs.customer = '{customer}' and  rs.scheduled_date BETWEEN '{from_date}' and '{to_date}' ORDER BY rs.scheduled_date """.format(customer=filters.get('customer'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

	elif filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		customer,document_no,document_date,amount,scheduled_date
		FROM
		`tabReceipt Schedule` rs
		WHERE rs.scheduled_date BETWEEN '{from_date}' and '{to_date}' ORDER BY rs.scheduled_date """.format(customer=filters.get('customer'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)


	return trans_data

def get_data_datewise(filters):

	trans_data =[]

	if filters.get("customer") and filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		scheduled_date, sum(amount) as amount
		FROM
		`tabReceipt Schedule` rs
		WHERE rs.customer = '{customer}' and  rs.scheduled_date BETWEEN '{from_date}' and '{to_date}' GROUP BY scheduled_date	ORDER BY rs.scheduled_date """.format(customer=filters.get('customer'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

	elif filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		scheduled_date, sum(amount) as amount
		FROM
		`tabReceipt Schedule` rs
		WHERE  rs.scheduled_date BETWEEN '{from_date}' and '{to_date}' GROUP BY scheduled_date	ORDER BY rs.scheduled_date """.format(customer=filters.get('customer'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)


	return trans_data

def get_data_customerwise(filters):

	trans_data =[]

	if filters.get("customer") and filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		customer, sum(amount) as amount
		FROM
		`tabReceipt Schedule` rs
		WHERE rs.customer = '{customer}' and  rs.scheduled_date BETWEEN '{from_date}' and '{to_date}' GROUP BY customer	ORDER BY rs.scheduled_date """.format(customer=filters.get('customer'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

	if  filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		customer, sum(amount) as amount
		FROM
		`tabReceipt Schedule` rs
		WHERE rs.scheduled_date BETWEEN '{from_date}' and '{to_date}' GROUP BY customer	ORDER BY rs.scheduled_date """.format( from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

	return trans_data

def get_data_customer_and_datewise(filters):

	trans_data = []

	if filters.get("customer") and filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		scheduled_date, customer, sum(amount) as amount
		FROM
		`tabReceipt Schedule` rs
		WHERE rs.customer = '{customer}' and  rs.scheduled_date BETWEEN '{from_date}' and '{to_date}' GROUP BY customer,scheduled_date	ORDER BY rs.scheduled_date """.format(customer=filters.get('customer'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

	if  filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		scheduled_date, customer, sum(amount) as amount
		FROM
		`tabReceipt Schedule` rs
		WHERE  rs.scheduled_date BETWEEN '{from_date}' and '{to_date}' GROUP BY customer,scheduled_date	ORDER BY rs.scheduled_date """.format(from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

	return trans_data


def get_columns_customerwise():

	return [
			{
				"fieldname": "customer",
				"fieldtype": "Data",
				"label": "Customer",
				"width": 230,
			},
   			{
				"fieldname": "amount",
				"fieldtype": "Currency",
				"label": "Amount",
				"width": 110,
			}
		]

def get_columns_datewise():

	return [
			{
				"fieldname": "scheduled_date",
				"fieldtype": "Date",
				"label": "Date",
				"width": 230,
			},
   			{
				"fieldname": "amount",
				"fieldtype": "Currency",
				"label": "Amount",
				"width": 110,
			}
		]

def get_columns_customer_and_datewise():

	return [
			{
				"fieldname": "scheduled_date",
				"fieldtype": "Date",
				"label": "Date",
				"width": 230,
			},
   			{
				"fieldname": "customer",
				"fieldtype": "Link",
				"label": "Customer",
				"options": "Customer",
				"width": 230,
			},
   			{
				"fieldname": "amount",
				"fieldtype": "Currency",
				"label": "Amount",
				"width": 110,
			}
		]

def get_columns():

	return [
			{
				"fieldname": "scheduled_date",
				"fieldtype": "Date",
				"label": "Scheduled Date",
				"width": 230,
			},
   			{
				"fieldname": "customer",
				"fieldtype": "Link",
				"label": "Customer",
				"options": "Customer",
				"width": 230,
			},
      		{
				"fieldname": "document_no",
				"fieldtype": "Data",
				"label": "Document",
				"width": 230,
			},
        	{
				"fieldname": "document_date",
				"fieldtype": "Date",
				"label": "Document Date",
				"width": 230,
			},
   			{
				"fieldname": "amount",
				"fieldtype": "Currency",
				"label": "Amount",
				"width": 110,
			}
		]
