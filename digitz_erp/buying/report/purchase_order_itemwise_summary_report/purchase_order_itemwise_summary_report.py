# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe.utils import formatdate
from frappe import _


def execute(filters=None):
    if filters.get('supplier'):
        columns = get_columns_supplier()
    else:
        columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(filters)
    return columns, data, None, chart

def get_chart_data(filters=None):
    query = """
        SELECT
            item_name as item,
            sum(qty)
        FROM
            `tabPurchase Order Item` poi
        INNER JOIN
            `tabPurchase Order` po ON po.name = poi.parent
        WHERE 1
    """
    if filters:
        if filters.get('supplier'):
            query += " AND po.supplier = %(supplier)s"
        if filters.get('from_date'):
            query += " AND po.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND po.posting_date <= %(to_date)s"
        if filters.get('item'):
            query += " AND poi.item = %(item)s"
        if filters.get('item_group'):
            query += " AND EXISTS (SELECT 1 FROM `tabItem` i WHERE i.name = poi.item AND i.item_group = %(item_group)s)"
        if filters.get('warehouse'):
            query += " AND poi.warehouse = %(warehouse)s"

    query += " GROUP BY item ORDER BY item"
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
    if filters.get('supplier'):
        query = """
            SELECT
                po.supplier,
                poi.item_name as item,
                i.item_group,
                poi.warehouse,
                sum(qty),
                round(sum(qty*rate)/sum(qty),2) as rate,
                gross_amount AS 'Amount',
                tax_amount AS 'Tax Amount',
                net_amount AS 'Net Amount'
            FROM
                `tabPurchase Order Item` poi
            INNER JOIN
                `tabPurchase Order` po ON po.name = poi.parent
            INNER JOIN
                `tabItem` i ON i.name = poi.item
            WHERE 1
        """
    else:
        query = """
            SELECT
                poi.item_name as item,
                i.item_group,
                poi.warehouse,
                sum(qty),
                round(sum(qty*rate)/sum(qty),2) as rate,
                gross_amount AS 'Amount',
                tax_amount AS 'Tax Amount',
                net_amount AS 'Net Amount'
            FROM
                `tabPurchase Order Item` poi
            INNER JOIN
                `tabPurchase Order` po ON po.name = poi.parent
            INNER JOIN
                `tabItem` i ON i.name = poi.item
            WHERE 1
        """
    if filters:
        if filters.get('supplier'):
            query += " AND po.supplier = %(supplier)s"
        if filters.get('from_date'):
            query += " AND po.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND po.posting_date <= %(to_date)s"
        if filters.get('item'):
            query += " AND poi.item = %(item)s"
        if filters.get('item_group'):
            query += " AND i.item_group = %(item_group)s"
        if filters.get('warehouse'):
            query += " AND poi.warehouse = %(warehouse)s"

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
            "width": 255
        },
        {
            "label": _("Item Group"),
            "fieldname": "item_group",
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 205
        },
        {
            "label": _("Warehouse"),
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 200
        },
        {
            "label": _("Qty"),
            "fieldname": "qty",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Avg Rate"),
            "fieldname": "rate",
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "label": _("Amount"),
            "fieldname": "Amount",
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "label": _("Tax Amount"),
            "fieldname": "Tax Amount",
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "label": _("Net Amount"),
            "fieldname": "Net Amount",
            "fieldtype": "Currency",
            "width": 120
        }
    ]


def get_columns_supplier():
    columns = [{
        "label": _("supplier"),
        "fieldname": "supplier",
        "fieldtype": "Link",
        "options": "supplier",
        "width": 200
    }]
    columns.extend(get_columns())
    return columns
