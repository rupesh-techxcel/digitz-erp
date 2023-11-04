# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(filters)
    return columns, data, None, chart

def get_chart_data(filters=None):
    credit_sale = filters.get('credit_sale')
    query = """
        SELECT
            qr.customer,
            SUM(qr.rounded_total) AS amount
        FROM
            `tabQuotation` qr
        WHERE
            1
    """
    if filters:
        if credit_sale == 'Credit':
            sub_query = "AND qr.credit_sale = 1"
            query += sub_query
        if credit_sale == 'Cash':
            sub_query = "AND qr.credit_sale = 0"
            query += sub_query
        if filters.get('customer'):
            query += " AND qr.customer = %(customer)s"
        if filters.get('from_date'):
            query += " AND qr.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND qr.posting_date <= %(to_date)s"

    query += " GROUP BY qr.customer ORDER BY qr.rounded_total DESC LIMIT 20"

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

    credit_sale = filters.get('credit_sale')
    status = filters.get('status')

    if filters.get('customer') and filters.get('from_date') and filters.get('to_date'):
        query = """
            SELECT
                qr.name AS quotation_name,
                qr.customer,
                qr.posting_date AS posting_date,
                CASE
                    WHEN qr.docstatus = 1 THEN 'Submitted'
                    WHEN qr.docstatus = 0 THEN 'Draft'
                    WHEN qr.docstatus = 2 THEN 'Cancelled'
                    ELSE ''
                END AS docstatus,
                qr.rounded_total AS amount,
                qr.payment_mode,
                qr.payment_account
            FROM
                `tabQuotation` qr
            WHERE
                qr.customer = '{0}'
                AND qr.posting_date BETWEEN '{1}' AND '{2}'
            """.format(filters.get('customer'), filters.get('from_date'), filters.get('to_date'))
        if credit_sale == 'Credit':
            sub_query = "AND qr.credit_sale = 1 "
            query += sub_query
        if credit_sale == 'Cash':
            sub_query = "AND qr.credit_sale = 0 "
            query += sub_query
        if status == 'Draft':
            sub_query = "AND qr.docstatus = 0 "
            query += sub_query
        elif status == 'Submitted':
            sub_query = "AND qr.docstatus = 1 "
            query += sub_query
        elif status == 'Cancelled':
            sub_query = "AND qr.docstatus = 2 "
            query += sub_query
        elif status == 'Not Cancelled':
            sub_query = "AND qr.docstatus !=2 "
            query += sub_query

        query += "ORDER BY qr.posting_date"
        data = frappe.db.sql(query, as_dict=True)

    elif filters.get('from_date') and filters.get('to_date'):
        query = """
            SELECT
                qr.name AS quotation_name,
                qr.customer,
                qr.posting_date,
                CASE
                    WHEN qr.docstatus = 1 THEN 'Submitted'
                    WHEN qr.docstatus = 0 THEN 'Draft'
                    WHEN qr.docstatus = 2 THEN 'Cancelled'
                    ELSE ''
                END AS docstatus,
                qr.posting_date,
                qr.rounded_total AS amount,
                qr.payment_mode,
                qr.payment_account
            FROM
                `tabQuotation` qr
            WHERE
                qr.posting_date BETWEEN '{0}' AND '{1}'
            """.format(filters.get('from_date'), filters.get('to_date'))
        if credit_sale == 'Credit':
            sub_query = "AND qr.credit_sale = 1 "
            query += sub_query
        if credit_sale == 'Cash':
            sub_query = "AND qr.credit_sale = 0 "
            query += sub_query
        if status == 'Draft':
            sub_query = "AND qr.docstatus = 0 "
            query += sub_query
        elif status == 'Submitted':
            sub_query = "AND qr.docstatus = 1 "
            query += sub_query
        elif status == 'Cancelled':
            sub_query = "AND qr.docstatus = 2 "
            query += sub_query
        elif status == 'Not Cancelled':
            sub_query = "AND qr.docstatus !=2 "
            query += sub_query
        query += "ORDER BY qr.posting_date"
        data = frappe.db.sql(query, as_dict=True)

    elif filters.get('customer'):
        query = """
            SELECT
                qr.name AS quotation_name,
                qr.customer,
                qr.posting_date,
                CASE
                    WHEN qr.docstatus = 1 THEN 'Submitted'
                    WHEN qr.docstatus = 0 THEN 'Draft'
                    WHEN qr.docstatus = 2 THEN 'Cancelled'
                    ELSE ''
                END AS docstatus,
                qr.rounded_total AS amount,
                qr.payment_mode,
                qr.payment_account
            FROM
                `tabQuotation` qr
            WHERE
                qr.customer = '{0}'
                AND qr.credit_sale = {1}
                AND qr.docstatus = 1
            ORDER BY
                posting_date
            """.format(filters.get('customer'))
        if credit_sale == 'Credit':
            sub_query = "AND qr.credit_sale = 1 "
            query += sub_query
        if credit_sale == 'Cash':
            sub_query = "AND qr.credit_sale = 0 "
            query += sub_query
        if status == 'Draft':
            sub_query = "AND qr.docstatus = 0 "
            query += sub_query
        elif status == 'Submitted':
            sub_query = "AND qr.docstatus = 1 "
            query += sub_query
        elif status == 'Cancelled':
            sub_query = "AND qr.docstatus = 2 "
            query += sub_query
        elif status == 'Not Cancelled':
            sub_query = "AND qr.docstatus !=2 "
            query += sub_query
        query += "ORDER BY qr.posting_date"
        data = frappe.db.sql(query, as_dict=True)
    else:
        query = """
            SELECT
                qr.name AS quotation_name,
                qr.customer,
                qr.posting_date AS posting_date,
                CASE
                    WHEN qr.docstatus = 1 THEN 'Submitted'
                    WHEN qr.docstatus = 0 THEN 'Draft'
                    WHEN qr.docstatus = 2 THEN 'Cancelled'
                    ELSE ''
                END AS docstatus,
                qr.rounded_total AS amount,
                qr.payment_mode,
                qr.payment_account
            FROM
                `tabQuotation` qr
            WHERE
                1

            """
        if credit_sale == 'Credit':
            sub_query = "AND qr.credit_sale = 1 "
            query += sub_query
        if credit_sale == 'Cash':
            sub_query = "AND qr.credit_sale = 0 "
            query += sub_query
        if status == 'Draft':
            sub_query = "AND qr.docstatus = 0 "
            query += sub_query
        elif status == 'Submitted':
            sub_query = "AND qr.docstatus = 1 "
            query += sub_query
        elif status == 'Cancelled':
            sub_query = "AND qr.docstatus = 2 "
            query += sub_query
        elif status == 'Not Cancelled':
            sub_query = "AND qr.docstatus !=2 "
            query += sub_query
        query += "ORDER BY qr.posting_date"
        data = frappe.db.sql(query, as_dict=True)

    return data

def get_columns():
    return [
        {
            "fieldname": "quotation_name",
            "fieldtype": "Link",
            "label": "Invoice No",
            "options": "Quotation",
            "width": 150,
        },
        {
            "fieldname": "customer",
            "fieldtype": "Link",
            "label": "Customer",
            "options": "Customer",
            "width": 150,
        },
        {
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "label": "Date",
            "width": 120,
        },
        {
            "fieldname": "docstatus",
            "fieldtype": "Data",
            "label": "Status",
            "width": 120,
        },
        {
            "fieldname": "amount",
            "fieldtype": "Currency",
            "label": "Invoice Amount",
            "width": 120,
        },
        {
            "fieldname": "payment_mode",
            "fieldtype": "Link",
            "label": "Payment Mode",
            "options": "Payment Mode",
            "width": 120,
        },
        {
            "fieldname": "payment_account",
            "fieldtype": "Link",
            "label": "Account",
            "options": "Account",
            "width": 120,
        }
    ]
