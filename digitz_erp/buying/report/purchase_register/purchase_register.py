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
            pi.supplier,
            SUM(pi.rounded_total) AS amount
        FROM
            `tabPurchase Invoice` pi
        WHERE
            pi.credit_purchase = {0}
    """.format(is_credit_purchase)
    if filters:
        if filters.get('supplier'):
            query += " AND pi.supplier = %(supplier)s"
        if filters.get('from_date'):
            query += " AND pi.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND pi.posting_date <= %(to_date)s"

    query += " GROUP BY pi.supplier ORDER BY pi.supplier"
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
	if filters.get('supplier') and  filters.get('from_date') and filters.get('to_date'):

		data = frappe.db.sql("""
		SELECT
			pi.supplier,
			pi.name AS purchase_invoice_name,
			pi.posting_date AS posting_date,
			CASE
				WHEN pi.docstatus = 1 THEN 'Submitted'
				WHEN pi.docstatus = 0 THEN 'Draft'
				WHEN pi.docstatus = 2 THEN 'Cancelled'
				ELSE ''
			END AS docstatus,
			pi.rounded_total AS amount,
			pi.paid_amount,
			pi.rounded_total - IFNULL(pi.paid_amount, 0) AS balance_amount,
			pi.payment_mode,
	  		pi.payment_account
		FROM
			`tabPurchase Invoice` pi
		WHERE
			pi.supplier = '{0}'
			AND pi.posting_date BETWEEN '{1}' AND '{2}'
			AND pi.credit_purchase = {3}
		ORDER BY
			pi.posting_date
		""".format(filters.get('supplier'), filters.get('from_date'), filters.get('to_date'), is_credit_purchase), as_dict=True)
	elif filters.get('from_date') and filters.get('to_date') and not frappe.get('supplier'):
		data = frappe.db.sql("""
		SELECT
			pi.supplier,
			pi.name AS purchase_invoice_name,
			pi.posting_date,
			CASE
				WHEN pi.docstatus = 1 THEN 'Submitted'
				WHEN pi.docstatus = 0 THEN 'Draft'
				WHEN pi.docstatus = 2 THEN 'Cancelled'
				ELSE ''
			END AS docstatus,
			pi.posting_date,
			pi.rounded_total AS amount,
			pi.paid_amount,
			pi.rounded_total - IFNULL(pi.paid_amount, 0) AS balance_amount,
			pi.payment_mode,
			pi.payment_account
		FROM
			`tabPurchase Invoice` pi
		WHERE
			pi.posting_date BETWEEN '{0}' AND '{1}'
			AND pi.credit_purchase = {2}
		ORDER BY
			pi.posting_date
		""".format(filters.get('from_date'), filters.get('to_date'), is_credit_purchase), as_dict=True)


	elif filters.get('supplier') and not(filters.get('from_date') and filters.get('to_date')):
		data = frappe.db.sql("""
		SELECT
			pi.supplier,
			pi.name AS purchase_invoice_name,
			pi.posting_date,
			CASE
				WHEN pi.docstatus = 1 THEN 'Submitted'
				WHEN pi.docstatus = 0 THEN 'Draft'
				WHEN pi.docstatus = 2 THEN 'Cancelled'
				ELSE ''
			END AS docstatus,
			pi.rounded_total AS amount,
			pi.paid_amount,
			pi.rounded_total - IFNULL(pi.paid_amount, 0) AS balance_amount,
			pi.payment_mode,
			pi.payment_account
		FROM
			`tabPurchase Invoice` pi
		WHERE
			pi.supplier = '{0}'
			AND pi.credit_purchase = {1}
		ORDER BY
			posting_date
		""".format(filters.get('supplier'), is_credit_purchase), as_dict=True)
	else:
		data = frappe.db.sql("""
			SELECT
				pi.supplier,
				pi.name AS purchase_invoice_name,
				pi.posting_date AS posting_date,
				CASE
					WHEN pi.docstatus = 1 THEN 'Submitted'
					WHEN pi.docstatus = 0 THEN 'Draft'
					WHEN pi.docstatus = 2 THEN 'Cancelled'
					ELSE ''
				END AS docstatus,
				pi.rounded_total AS amount,
				pi.paid_amount,
				pi.rounded_total - IFNULL(pi.paid_amount, 0) AS balance_amount,
				pi.payment_mode,
  				pi.payment_account

			FROM
				`tabPurchase Invoice` pi
			WHERE
				pi.credit_purchase = {0}
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
			"width": 150,
		},
		{

			"fieldname": "purchase_invoice_name",
			"fieldtype": "Link",
			"label": "Invoice No",
			"options": "Purchase Invoice",
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
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"label": "Paid Amount",
			"width": 100,
		},
  		{
			"fieldname": "balance_amount",
			"fieldtype": "Currency",
			"label": "Balance Amount",
			"width": 100,
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
			"options": "Account" ,
			"width": 120,
		}
	]
