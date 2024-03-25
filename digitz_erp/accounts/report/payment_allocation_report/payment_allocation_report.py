# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = []
    return columns, data, None, chart

def get_columns():
    return [
        {
            "label": "Payment Voucher No",
            "fieldname": "payment_voucher_no",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": "Payment Voucher Date",
            "fieldname": "payment_voucher_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": "Voucher Type",
            "fieldname": "voucher_type",
            "fieldtype": "Data",
            "width": 120
        },
		{
            "label": "Voucher No",
            "fieldname": "voucher_no",
            "fieldtype": "Data",
            "width": 180
        },
		{
            "label": "Voucher Date",
            "fieldname": "voucher_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": "Supplier",
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 180
        },
        {
            "label": "Invoice Amount",
            "fieldname": "invoice_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": "Paid Amount",
            "fieldname": "paid_amount",
            "fieldtype": "Currency",
            "width": 120
        },
    ]

def get_data(filters=None):
    query = """
        SELECT
            pe.name as 'payment_voucher_no',
            pe.posting_date as payment_voucher_date,
            ped.reference_type as 'voucher_type',
            pe.posting_date as voucher_date,
            pa.reference_name as voucher_no,
            pa.supplier as supplier,
            pa.total_amount as invoice_amount,
            pa.paying_amount as paid_amount
        FROM
            `tabPayment Entry` pe
        INNER JOIN
            `tabPayment Entry Detail` ped ON ped.parent = pe.name
        INNER JOIN
            `tabPayment Allocation` pa ON pa.parent = pe.name
        WHERE
            pe.docstatus != 2
            AND pe.posting_date >= %(from_date)s
            AND pe.posting_date <= %(to_date)s
            AND ped.reference_type IN ('Purchase Invoice', 'Purchase Return', 'Expense Entry', 'Debit Note')
    """

    if filters:
        if filters.get('supplier'):
            query += " AND pa.supplier = %(supplier)s"
        if filters.get('posting_date'):
            query += " AND pe.posting_date = %(posting_date)s"

    data = frappe.db.sql(query, filters, as_dict=True)
    return data
