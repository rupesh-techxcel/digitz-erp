# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe.utils import formatdate
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(filters)
    return columns, data, None, chart


def get_chart_data(filters=None):
    query = """
        SELECT
			item,
			qty
        FROM
			`tabDelivery Note Item` pi
        INNER JOIN
			`tabDelivery Note` p ON p.name = pi.parent
        WHERE 1
    """
    if filters:
        if filters.get('customer'):
            query += " AND p.customer = %(customer)s"
        if filters.get('from_date'):
            query += " AND p.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND p.posting_date <= %(to_date)s"

    query += " ORDER BY posting_date, item"
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
    query = """
        SELECT
            p.customer,
            posting_date,
            item,
            qty,
            rate,
            gross_amount AS 'Amount',
            tax_amount AS 'Tax Amount',
            net_amount AS 'Net Amount'
        FROM
            `tabDelivery Note Item` pi
        INNER JOIN
            `tabDelivery Note` p ON p.name = pi.parent
        WHERE 1
    """
    if filters:
        if filters.get('customer'):
            query += " AND p.customer = %(customer)s"
        if filters.get('from_date'):
            query += " AND p.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND p.posting_date <= %(to_date)s"

    query += " ORDER BY posting_date, item"
    data = frappe.db.sql(query, filters, as_list=True)

    return data


def get_columns():
    return [
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 300
        },
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Item"),
            "fieldname": "item",
            "fieldtype": "Link",
            "options": "Item",
            "width": 300
        },
        {
            "label": _("Qty"),
            "fieldname": "qty",
            "fieldtype": "Float",
            "width": 80
        },
        {
            "label": _("Rate"),
            "fieldname": "rate",
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "label": _("Amount"),
            "fieldname": "Amount",
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "label": _("Tax Amount"),
            "fieldname": "Tax Amount",
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "label": _("Net Amount"),
            "fieldname": "Net Amount",
            "fieldtype": "Currency",
            "width": 120
        }
    ]
