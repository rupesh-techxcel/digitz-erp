# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe.utils import formatdate
from frappe import _


def execute(filters=None):
    if filters.get('customer'):
        columns = get_columns_customer()
    else:
        columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_data(filters):
    if filters.get('customer'):
        query = """
            SELECT
                si.customer,
                sii.item,
                i.item_group,
                sii.warehouse,
                sum(qty),
                rate,
                gross_amount AS 'Amount',
                tax_amount AS 'Tax Amount',
                net_amount AS 'Net Amount'
            FROM
                `tabSales Invoice Item` sii
            INNER JOIN
                `tabSales Invoice` si ON si.name = sii.parent
            INNER JOIN
                `tabItem` i ON i.name = sii.item
            WHERE 1
        """
    else:
        query = """
            SELECT
                sii.item,
                i.item_group,
                sii.warehouse,
                sum(qty),
                rate,
                gross_amount AS 'Amount',
                tax_amount AS 'Tax Amount',
                net_amount AS 'Net Amount'
            FROM
                `tabSales Invoice Item` sii
            INNER JOIN
                `tabSales Invoice` si ON si.name = sii.parent
            INNER JOIN
                `tabItem` i ON i.name = sii.item
            WHERE 1
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
            query += " AND i.item_group = %(item_group)s"
        if filters.get('warehouse'):
            query += " AND sii.warehouse = %(warehouse)s"

    query += " GROUP BY item ORDER BY item"
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
            "width": 100
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


def get_columns_customer():
    columns = [{
        "label": _("customer"),
        "fieldname": "customer",
        "fieldtype": "Link",
        "options": "customer",
        "width": 200
    }]
    columns.append(get_columns())
    return columns
