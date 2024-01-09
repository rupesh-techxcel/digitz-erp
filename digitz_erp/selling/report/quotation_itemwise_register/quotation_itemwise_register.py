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
    print("chart")
    print(chart)
    return columns, data, None, chart

def get_chart_data(filters=None):
    query = """
        SELECT
            item_group,
            sum(qi.net_amount) as net_amount
        FROM
            `tabQuotation Item` qi
        INNER JOIN
            `tabQuotation` q ON q.name = qi.parent
        INNER JOIN `tabItem` i on i.name = qi.item
        WHERE q.docstatus =1
    """
    if filters:
        if filters.get('customer'):
            query += " AND q.customer = %(customer)s"
        if filters.get('from_date'):
            query += " AND q.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND q.posting_date <= %(to_date)s"
        if filters.get('item'):
            query += " AND qi.item = %(item)s"
        if filters.get('item_group'):
            query += " AND EXISTS (SELECT 1 FROM `tabItem` i WHERE i.name = qi.item AND i.item_group = %(item_group)s)"
        if filters.get('warehouse'):
            query += " AND qi.warehouse = %(warehouse)s"

    query += " GROUP BY i.item_group ORDER BY sum(qi.net_amount) desc LIMIT 25"
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
            qi.item_name as item,
            q.customer,
            q.name as 'Qtn No',            
            q.posting_date,            
            i.item_group,
            qi.warehouse,
            qty,
            rate,
            gross_amount AS 'Amount',
            tax_amount AS 'Tax Amount',
            net_amount AS 'Net Amount'
        FROM
            `tabQuotation Item` qi
        INNER JOIN
            `tabQuotation` q ON q.name = qi.parent
        INNER JOIN
            `tabItem` i ON i.name = qi.item
        WHERE q.docstatus  = 1
    """
    if filters:
        if filters.get('customer'):
            query += " AND q.customer = %(customer)s"
        if filters.get('from_date'):
            query += " AND q.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND q.posting_date <= %(to_date)s"
        if filters.get('item'):
            query += " AND qi.item = %(item)s"
        if filters.get('item_group'):
            query += " AND i.item_group = %(item_group)s"
        if filters.get('warehouse'):
            query += " AND qi.warehouse = %(warehouse)s"

    query += " ORDER BY q.modified desc"
    data = frappe.db.sql(query, filters, as_list=True)

    return data


def get_columns():
    return [
        {
            "label": _("Item"),
            "fieldname": "item",
            "fieldtype": "Link",
            "options": "Item",
            "width": 200
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 200
        },
        {
            "label": _("Qtn No"),
            "fieldname": "qtn_no",
            "fieldtype": "Link",
            "options": "Quotation",
            "width": 200
        },
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 100
        },        
        {
            "label": _("Item Group"),
            "fieldname": "item_group",
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 100
        },
        {
            "label": _("Warehouse"),
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 100
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
