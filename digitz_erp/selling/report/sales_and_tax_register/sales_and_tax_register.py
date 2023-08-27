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
            name as 'invoice_no',
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
            c.emirate,
            SUM(ts.net_total) AS total_net_total,
            SUM(ts.tax_total) AS total_tax_total
        FROM
            `tabSales Invoice` ts
        INNER JOIN
            `tabCustomer` c ON c.name = ts.customer
        WHERE
            ts.docstatus != 2
            AND ts.posting_date >= %(from_date)s
            AND ts.posting_date <= %(to_date)s
    """
    if filters:
        if filters.get('customer'):
            query += " AND ts.customer = %(customer)s"
        if filters.get('from_date'):
            query += " AND ts.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND ts.posting_date <= %(to_date)s"
    query += " GROUP BY c.emirate"
    data = frappe.db.sql(query, filters, as_list=True)

    chart = {
        "data": {
            "labels": [row[0] for row in data],
            "datasets": [
                {"name": "Net Total", "values": [row[1] for row in data]},
                {"name": "Tax Total", "values": [row[2] for row in data]}
            ]
        },
        "type": "bar"
    }

    return chart


def get_columns():
    return [        
        {
            "label": _("Invoice No"),
            "fieldname": "invoice_no",
            "fieldtype": "Data",            
            "width": 161
        },
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 200
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 400
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
