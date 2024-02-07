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
            "label": "Voucher Type",
            "fieldname": "voucher_type",
            "fieldtype": "Data",
            "width": 161
        },
        {
            "label": "Posting Date",
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": "Supplier",
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 290
        },
        {
            "label": "Taxable Total",
            "fieldname": "gross_total",
            "fieldtype": "Currency",
            "width": 200
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
            pi.name as 'invoice_no',
            pi.posting_date,
            pi.supplier,
            'Purchase Invoice' as 'voucher_type',
            pi.gross_total,
            pi.net_total,
            pi.tax_total
        FROM
            `tabPurchase Invoice` pi
        WHERE
            pi.docstatus != 2
            AND pi.posting_date >= %(from_date)s
            AND pi.posting_date <= %(to_date)s
    """
    if filters:
        if filters.get('supplier'):
            query += " AND pi.supplier = %(supplier)s"
        if filters.get('posting_date'):
            query += " AND pi.posting_date = %(posting_date)s"

    query += """
        UNION ALL
        SELECT
            ee.name as 'invoice_no',
            ee.posting_date,
            eed.supplier,
            'Expense Entry' as 'voucher_type',
            ee.total_expense_amount,
            ee.grand_total,
            ee.total_tax_amount
        FROM
            `tabExpense Entry` ee
        INNER JOIN
            `tabExpense Entry Details` eed ON ee.name = eed.parent
        WHERE
            ee.docstatus != 2
            AND ee.posting_date >= %(from_date)s
            AND ee.posting_date <= %(to_date)s
    """

    query += """
        UNION ALL
        SELECT
            aee.name as 'invoice_no',
            aee.posting_date,
            ed.supplier,
            'Additional Expense Entry' as 'voucher_type',
            aee.total_expense_amount,
            aee.grand_total,
            aee.total_tax_amount
        FROM
            `tabAdditional Expense Entry` aee
        INNER JOIN
            `tabExpense Entry Details` ed ON aee.name = ed.parent
        WHERE
            aee.docstatus != 2
            AND aee.posting_date >= %(from_date)s
            AND aee.posting_date <= %(to_date)s
    """

    data = frappe.db.sql(query, filters, as_dict=True)
    return data
