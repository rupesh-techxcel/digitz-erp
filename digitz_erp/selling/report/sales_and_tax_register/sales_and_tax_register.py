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


def get_data(filters=None):
    query = """
         SELECT
             posting_date,
             customer,
             net_total,
             tax_total
        FROM
            `tabSales Invoice`
        WHERE
            docstatus != 2
            AND posting_date >= %(from_date)s
            AND posting_date <= %(to_date)s
    """
    if filters:
        if filters.get('customer'):
            query += " AND customer = %(customer)s"
        if filters.get('posting_date'):
            query += " AND posting_date = %(posting_date)s"

    data = frappe.db.sql(query, filters, as_dict=True)
    return data


def get_chart_data(filters=None):
    query = """
         SELECT
             customer,
             net_total
        FROM
            `tabSales Invoice`
        WHERE
            docstatus != 2
            AND posting_date >= %(from_date)s
            AND posting_date <= %(to_date)s
    """
    if filters:
        if filters.get('customer'):
            query += " AND customer = %(customer)s"
        if filters.get('from_date'):
            query += " AND posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND posting_date <= %(to_date)s"
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


def get_columns():
    return [
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 400
        },
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 200
        },
        {
            "label": _("Net Total"),
            "fieldname": "net_total",
            "fieldtype": "Currency",
            "width": 200
        },
        {
            "label": _("Tax Total"),
            "fieldname": "tax_total",
            "fieldtype": "Currency",
            "width": 200
        },
    ]
