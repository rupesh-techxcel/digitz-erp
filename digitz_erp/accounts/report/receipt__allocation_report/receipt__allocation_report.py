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
            "label": "Receipt Voucher No",
            "fieldname": "receipt_voucher_no",
            "fieldtype": "Data",
            "width": 161
        },
        {
            "label": "Receipt Voucher Date",
            "fieldname": "receipt_voucher_date",
            "fieldtype": "Date",
            "width": 161
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
            "width": 120
        },
		{
            "label": "Voucher Date",
            "fieldname": "voucher_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": "Customer",
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 290
        },
        {
            "label": "Paid Amount",
            "fieldname": "paid_amount",
            "fieldtype": "Currency",
            "width": 200
        },
    ]

def get_data(filters=None):
    query = """
        SELECT
            re.name as 'receipt_voucher_no',
            re.posting_date as receipt_voucher_date,
            red.reference_type as 'voucher_type',
            re.posting_date as voucher_date,
            ra.reference_name as voucher_no,
            ra.customer as customer,
            re.amount as paid_amount
        FROM
            `tabReceipt Entry` re
        INNER JOIN
            `tabReceipt Entry Detail` red ON red.parent = re.name
        INNER JOIN
            `tabReceipt Allocation` ra ON ra.parent = re.name
        WHERE
            re.docstatus != 2
            AND re.posting_date >= %(from_date)s
            AND re.posting_date <= %(to_date)s
            AND red.reference_type IN ('Sales Invoice', 'Sales Return', 'Credit Note')
    """

    if filters:
        if filters.get('customer'):
            query += " AND ra.customer = %(customer)s"
        if filters.get('posting_date'):
            query += " AND re.posting_date = %(posting_date)s"

    data = frappe.db.sql(query, filters, as_dict=True)
    return data
