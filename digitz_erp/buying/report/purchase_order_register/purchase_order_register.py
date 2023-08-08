# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(filters)
    return columns, data, None, chart

def get_chart_data(filters=None):
    if filters.get('credit_purchase'):
        is_credit_purchase = 1
    else:
        is_credit_purchase = 0
    query = """
        SELECT
            po.supplier,
            SUM(po.rounded_total) AS amount
        FROM
            `tabPurchase Order` po
        WHERE
            po.credit_purchase = {0}
    """.format(is_credit_purchase)
    if filters:
        if filters.get('supplier'):
            query += " AND po.supplier = %(supplier)s"
        if filters.get('from_date'):
            query += " AND po.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND po.posting_date <= %(to_date)s"

    query += " GROUP BY po.supplier ORDER BY po.supplier"
    data = frappe.db.sql(query, filters, as_list=True)

    suppliers = []
    supplier_wise_amount = {}
    for row in data:
        if row[0] not in suppliers:
            suppliers.append(row[0])
        if supplier_wise_amount.get(row[0]):
            supplier_wise_amount[row[0]] += row[1]
        else:
            supplier_wise_amount[row[0]] = row[1]
    data = list(supplier_wise_amount.items())

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
    if filters.get('credit_purchase'):
        is_credit_purchase = 1
    else:
        is_credit_purchase = 0

    if filters.get('supplier') and filters.get('from_date') and filters.get('to_date'):
        data = frappe.db.sql("""
            SELECT
                po.name AS purchase_order_name,
                po.supplier,
                po.posting_date AS posting_date,
                CASE
                    WHEN po.docstatus = 1 THEN 'Submitted'
                    WHEN po.docstatus = 0 THEN 'Draft'
                    WHEN po.docstatus = 2 THEN 'Cancelled'
                    ELSE ''
                END AS docstatus,
                po.rounded_total AS amount
            FROM
                `tabPurchase Order` po
            WHERE
                po.supplier = '{0}'
                AND po.posting_date BETWEEN '{1}' AND '{2}'
                AND po.credit_purchase = {3}
            ORDER BY
                po.posting_date
            """.format(filters.get('supplier'), filters.get('from_date'), filters.get('to_date'), is_credit_purchase), as_dict=True)

    elif filters.get('from_date') and filters.get('to_date'):
        data = frappe.db.sql("""
            SELECT
                po.supplier,
                po.name AS purchase_order_name,
                po.posting_date,
                CASE
                    WHEN po.docstatus = 1 THEN 'Submitted'
                    WHEN po.docstatus = 0 THEN 'Draft'
                    WHEN po.docstatus = 2 THEN 'Cancelled'
                    ELSE ''
                END AS docstatus,
                po.posting_date,
                po.rounded_total AS amount
            FROM
                `tabPurchase Order` po
            WHERE
                po.posting_date BETWEEN '{0}' AND '{1}'
                AND po.credit_purchase = {2}
            ORDER BY
                po.posting_date
            """.format(filters.get('from_date'), filters.get('to_date'), is_credit_purchase), as_dict=True)

    elif filters.get('supplier'):
        data = frappe.db.sql("""
            SELECT
                po.name AS purchase_order_name,
                po.supplier,
                po.posting_date,
                CASE
                    WHEN po.docstatus = 1 THEN 'Submitted'
                    WHEN po.docstatus = 0 THEN 'Draft'
                    WHEN po.docstatus = 2 THEN 'Cancelled'
                    ELSE ''
                END AS docstatus,
                po.rounded_total AS amount
            FROM
                `tabPurchase Order` po
            WHERE
                po.supplier = '{0}'
                AND po.credit_purchase = {1}
            ORDER BY
                posting_date
            """.format(filters.get('supplier'), is_credit_purchase), as_dict=True)
    else:
        data = frappe.db.sql("""
            SELECT
                po.supplier,
                po.name AS purchase_order_name,
                po.posting_date AS posting_date,
                CASE
                    WHEN po.docstatus = 1 THEN 'Submitted'
                    WHEN po.docstatus = 0 THEN 'Draft'
                    WHEN po.docstatus = 2 THEN 'Cancelled'
                    ELSE ''
                END AS docstatus,
                po.rounded_total AS amount
            FROM
                `tabPurchase Order` po
            WHERE
                po.credit_purchase = {0}
            ORDER BY
                posting_date
            """.format(is_credit_purchase), as_dict=True)

    return data

def get_columns():
    return [
        {
            "fieldname": "supplier",
            "fieldtype": "Link",
            "label": "Supplier",
            "options": "Supplier",
            "width": 415
        },
        {
            "fieldname": "purchase_order_name",
            "fieldtype": "Link",
            "label": "Purchase Order No",
            "options": "Purchase Order",
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
