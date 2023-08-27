# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = get_columns()
    print(columns)
    data = get_data(filters)
    chart = []
    return columns, data, None, chart


def get_columns():
    return [        
        {
            "label": "Invoice No",
            "fieldname": "invoice_no",
            "fieldtype": "Data",            
            "width": 161
        },
        {
            "label": "Posting Date",
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 200
        },
        {
            "label": "Supplier",
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 400
        },        
        {
            "label": "Net Total",
            "fieldname": "net_total",
            "fieldtype": "Currency",
            "width": 200
        },
        {
            "label": "Tax Total",
            "fieldname": "tax_total",
            "fieldtype": "Currency",
            "width": 200
        },
    ]


def get_data(filters=None):
    query = """
         SELECT
            name as 'invoice_no',
             posting_date,
             supplier,             
             net_total,
             tax_total
        FROM
            `tabPurchase Invoice`
        WHERE
            docstatus != 2
            AND posting_date >= %(from_date)s
            AND posting_date <= %(to_date)s
    """
    if filters:
        if filters.get('supplier'):
            query += " AND supplier = %(supplier)s"
        if filters.get('posting_date'):
            query += " AND posting_date = %(posting_date)s"

    data = frappe.db.sql(query, filters, as_dict=True)
    return data

