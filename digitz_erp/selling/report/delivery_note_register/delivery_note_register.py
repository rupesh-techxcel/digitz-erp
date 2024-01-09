# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(filters)
	return columns, data, None, chart

def get_chart_data(filters=None):
    query = """
        SELECT
            dn.customer,
            SUM(dn.rounded_total) AS amount
        FROM
            `tabDelivery Note` dn
        WHERE docstatus =1
    """
    if filters:
        if filters.get('customer'):
            query += " AND dn.customer = %(customer)s"
        if filters.get('from_date'):
            query += " AND dn.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND dn.posting_date <= %(to_date)s"

    query += " GROUP BY dn.customer ORDER BY dn.customer DESC LIMIT 20"
    data = frappe.db.sql(query, filters, as_list=True)

    customers = []
    customer_wise_amount = {}
    for row in data:
        if row[0] not in customers:
            customers.append(row[0])
        if customer_wise_amount.get(row[0]):
            customer_wise_amount[row[0]] += row[1]
        else:
            customer_wise_amount[row[0]] = row[1]
    data = list(customer_wise_amount.items())

    datasets = []
    labels = []
    chart = {}

    if data:
        for d in data:
            labels.append(d[0])
            datasets.append(d[1])

        chart = {
            "data": {
                "labels": labels,
                "datasets": [{"values": datasets}]
            },
            "type": "bar"
        }
    return chart

def get_data(filters):
	data = ""
	status = filters.get('status')

	if filters.get('customer') and filters.get('from_date') and filters.get('to_date'):
		query = """
			SELECT
				dn.name AS delivery_note_name,
				dn.customer,
				dn.posting_date AS posting_date,
				CASE
					WHEN dn.docstatus = 1 THEN 'Submitted'
					WHEN dn.docstatus = 0 THEN 'Draft'
				    WHEN dn.docstatus = 2 THEN 'Cancelled'
					ELSE ''
				END AS docstatus,
				dn.rounded_total AS amount
			FROM
				`tabDelivery Note` dn
			WHERE
				dn.customer = '{0}'
				AND dn.posting_date BETWEEN '{1}' AND '{2}'
			""".format(filters.get('customer'), filters.get('from_date'), filters.get('to_date'), as_dict=True)
		if status == 'Draft':
			sub_query = "AND dn.docstatus = 0 "
			query += sub_query
		elif status == 'Submitted':
			sub_query = "AND dn.docstatus = 1 "
			query += sub_query
		elif status == 'Cancelled':
			sub_query = "AND dn.docstatus = 2 "
			query += sub_query
		elif status == 'Not Cancelled':
			sub_query = "AND dn.docstatus !=2 "
			query += sub_query
		query += "ORDER BY dn.posting_date"
		data = frappe.db.sql(query, as_dict=True)

	elif filters.get('from_date') and filters.get('to_date'):
		query = """
			SELECT
				dn.customer,
				dn.name AS delivery_note_name,
				dn.posting_date,
				CASE
					WHEN dn.docstatus = 1 THEN 'Submitted'
					WHEN dn.docstatus = 0 THEN 'Draft'
				    WHEN dn.docstatus = 2 THEN 'Cancelled'
					ELSE ''
				END AS docstatus,
				dn.posting_date,
				dn.rounded_total AS amount
			FROM
				`tabDelivery Note` dn
			WHERE
				dn.posting_date BETWEEN '{0}' AND '{1}'
			""".format(filters.get('from_date'), filters.get('to_date'), as_dict=True)
		if status == 'Draft':
			sub_query = "AND dn.docstatus = 0 "
			query += sub_query
		elif status == 'Submitted':
			sub_query = "AND dn.docstatus = 1 "
			query += sub_query
		elif status == 'Cancelled':
			sub_query = "AND dn.docstatus = 2 "
			query += sub_query
		elif status == 'Not Cancelled':
			sub_query = "AND dn.docstatus !=2 "
			query += sub_query
		query += "ORDER BY dn.posting_date"
		data = frappe.db.sql(query, as_dict=True)

	elif filters.get('customer'):
		query = """
			SELECT
				dn.name AS delivery_note_name,
				dn.customer,
				dn.posting_date,
				CASE
					WHEN dn.docstatus = 1 THEN 'Submitted'
					WHEN dn.docstatus = 0 THEN 'Draft'
				    WHEN dn.docstatus = 2 THEN 'Cancelled'
					ELSE ''
				END AS docstatus,
				dn.rounded_total AS amount
			FROM
				`tabDelivery Note` dn
			WHERE
				dn.customer = '{0}'
			""".format(filters.get('customer'), as_dict=True)
		if status == 'Draft':
			sub_query = "AND dn.docstatus = 0 "
			query += sub_query
		elif status == 'Submitted':
			sub_query = "AND dn.docstatus = 1 "
			query += sub_query
		elif status == 'Cancelled':
			sub_query = "AND dn.docstatus = 2 "
			query += sub_query
		elif status == 'Not Cancelled':
			sub_query = "AND dn.docstatus !=2 "
			query += sub_query
		query += "ORDER BY dn.posting_date"
		data = frappe.db.sql(query, as_dict=True)

	else:
		query = """
			SELECT
				dn.customer,
				dn.name AS delivery_note_name,
				dn.posting_date AS posting_date,
				CASE
					WHEN dn.docstatus = 1 THEN 'Submitted'
					WHEN dn.docstatus = 0 THEN 'Draft'
				    WHEN dn.docstatus = 2 THEN 'Cancelled'
					ELSE ''
				END AS docstatus,
				dn.rounded_total AS amount
			FROM
				`tabDelivery Note` dn
			WHERE
				1
			"""
		if status == 'Draft':
			sub_query = "AND dn.docstatus = 0 "
			query += sub_query
		elif status == 'Submitted':
			sub_query = "AND dn.docstatus = 1 "
			query += sub_query
		elif status == 'Cancelled':
			sub_query = "AND dn.docstatus = 2 "
			query += sub_query
		elif status == 'Not Cancelled':
			sub_query = "AND dn.docstatus !=2 "
			query += sub_query
		query += "ORDER BY dn.posting_date"
		data = frappe.db.sql(query, as_dict=True)

	return data


def get_columns():
	return [
		{
			"fieldname": "customer",
			"fieldtype": "Link",
			"label": "Customer",
			"options": "Customer",
			"width": 415
		},
		{
			"fieldname": "delivery_note_name",
			"fieldtype": "Link",
			"label": "Delivery Note No",
			"options": "Delivery Note",
			"width": 250
		},
		{
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"label": "Date",
			"width": 170
		},
		{
			"fieldname": "docstatus",
			"fieldtype": "Data",
			"label": "Status",
			"width": 170
		},
		{
			"fieldname": "amount",
			"fieldtype": "Currency",
			"label": "Invoice Amount",
			"width": 200
		}
	]
