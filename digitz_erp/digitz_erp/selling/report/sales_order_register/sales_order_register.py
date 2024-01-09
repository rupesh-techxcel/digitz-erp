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
            item_group,
            sum(qty)
        FROM
            `tabSales Order Item` sii
        INNER JOIN
            `tabSales Order` si ON si.name = sii.parent
        INNER JOIN `tabItem` i on i.name = sii.item
        WHERE si.docstatus =1
    """
    if filters:
        if filters.get('customer'):
            query += " AND si.customer = %(customer)s"
        if filters.get('from_date'):
            query += " AND si.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND si.posting_date <= %(to_date)s"
        if filters.get('item'):
            query += " AND sii.item = %(item)s"
        if filters.get('item_group'):
            query += " AND EXISTS (SELECT 1 FROM `tabItem` i WHERE i.name = sii.item AND i.item_group = %(item_group)s)"
        if filters.get('warehouse'):
            query += " AND sii.warehouse = %(warehouse)s"

    query += " GROUP BY item_group ORDER BY sum(sii.qty) desc LIMIT 25"
    data = frappe.db.sql(query, filters, as_list=True)

    items = []
    item_wise_qty = {}
    for row in data:
        if row[0] not in items:
            items.append(row[0])
        if item_wise_qty.get(row[0]):
            item_wise_qty[row[0]] = item_wise_qty.get(row[0]) + row[1]
        else:
            item_wise_qty[row[0]] = row[1]
    data = list(item_wise_qty.items())

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
	data = []

	if filters.get('customer') and filters.get('from_date') and filters.get('to_date'):
		data = frappe.db.sql("""
			SELECT
				so.name AS sales_order_name,
				so.customer,
				so.posting_date AS posting_date,
				CASE
					WHEN so.docstatus = 1 THEN 'Submitted'
					ELSE ''
				END AS docstatus,
				so.rounded_total AS amount
			FROM
				`tabSales Order` so
			WHERE
				so.customer = '{0}'
				AND so.posting_date BETWEEN '{1}' AND '{2}'
				AND so.docstatus = 1
			ORDER BY
				so.posting_date
			""".format(filters.get('customer'), filters.get('from_date'), filters.get('to_date')), as_dict=True)

	elif filters.get('from_date') and filters.get('to_date'):
		data = frappe.db.sql("""
			SELECT
				so.customer,
				so.name AS sales_order_name,
				so.posting_date,
				CASE
					WHEN so.docstatus = 1 THEN 'Submitted'
					ELSE ''
				END AS docstatus,
				so.posting_date,
				so.rounded_total AS amount
			FROM
				`tabSales Order` so
			WHERE
				so.posting_date BETWEEN '{0}' AND '{1}'
				AND so.docstatus = 1
			ORDER BY
				so.posting_date
			""".format(filters.get('from_date'), filters.get('to_date')), as_dict=True)

	elif filters.get('customer'):
		data = frappe.db.sql("""
			SELECT
				so.name AS sales_order_name,
				so.customer,
				so.posting_date,
				CASE
					WHEN so.docstatus = 1 THEN 'Submitted'
					ELSE ''
				END AS docstatus,
				so.rounded_total AS amount
			FROM
				`tabSales Order` so
			WHERE
				so.customer = '{0}'
				AND so.docstatus = 1
			ORDER BY
				posting_date
			""".format(filters.get('customer')), as_dict=True)
	else:
		data = frappe.db.sql("""
			SELECT
				so.customer,
				so.name AS sales_order_name,
				so.posting_date AS posting_date,
				CASE
					WHEN so.docstatus = 1 THEN 'Submitted'
					ELSE ''
				END AS docstatus,
				so.rounded_total AS amount
			FROM
				`tabSales Order` so
			ORDER BY
				posting_date
			""", as_dict=True)

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
			"fieldname": "sales_order_name",
			"fieldtype": "Link",
			"label": "Sales Order No",
			"options": "Sales Order",
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
