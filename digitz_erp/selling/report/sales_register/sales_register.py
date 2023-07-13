# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = get_columns()

	data = get_data(filters)
	return columns, data

def get_data(filters):
	data = ""
	if filters.get('credit_sale'):
		is_credit_sale = 1
	else:
		is_credit_sale = 0

	if filters.get('customer') and  filters.get('from_date') and filters.get('to_date'):
		data = frappe.db.sql("""
		SELECT
			si.name AS sales_invoice_name,
			si.customer,
			si.posting_date AS posting_date,
			CASE
				WHEN si.docstatus = 1 THEN 'Submitted'
				WHEN si.docstatus = 0 THEN 'Draft'
				WHEN si.docstatus = 2 THEN 'Cancelled'
				ELSE ''
			END AS docstatus,
			si.rounded_total AS amount,
			si.paid_amount,
			si.rounded_total - IFNULL(si.paid_amount, 0) AS balance_amount,
			si.payment_mode,
			si.payment_account
		FROM
			`tabSales Invoice` si
		WHERE
			si.customer = '{0}'
			AND si.posting_date BETWEEN '{1}' AND '{2}'
			AND si.credit_sale = {3}
		ORDER BY
			si.posting_date
		""".format(filters.get('customer'), filters.get('from_date'), filters.get('to_date'), is_credit_sale), as_dict=True)

	elif filters.get('from_date') and filters.get('to_date'):

		data = frappe.db.sql("""
		SELECT
			si.name AS sales_invoice_name,
			si.customer,
			si.posting_date,
			CASE
				WHEN si.docstatus = 1 THEN 'Submitted'
				WHEN si.docstatus = 0 THEN 'Draft'
				WHEN si.docstatus = 2 THEN 'Cancelled'
				ELSE ''
			END AS docstatus,
			si.posting_date,
			si.rounded_total AS amount,
			si.paid_amount,
			si.rounded_total - IFNULL(si.paid_amount, 0) AS balance_amount,
			si.payment_mode,
			si.payment_account
		FROM
			`tabSales Invoice` si
		WHERE
			si.posting_date BETWEEN '{0}' AND '{1}'
			AND si.credit_sale = {2}
		ORDER BY
			si.posting_date
		""".format(filters.get('from_date'), filters.get('to_date'), is_credit_sale), as_dict=True)

	elif filters.get('customer'):
		data = frappe.db.sql("""
		SELECT
			si.name AS sales_invoice_name,
			si.customer,
			si.posting_date,
			CASE
				WHEN si.docstatus = 1 THEN 'Submitted'
				WHEN si.docstatus = 0 THEN 'Draft'
				WHEN si.docstatus = 2 THEN 'Cancelled'
				ELSE ''
			END AS docstatus,
			si.rounded_total AS amount,
			si.paid_amount,
			si.rounded_total - IFNULL(si.paid_amount, 0) AS balance_amount,
			si.payment_mode,
	  		si.payment_account
		FROM
			`tabSales Invoice` si
		WHERE
			si.customer = '{0}'
			AND si.credit_sale = {1}
		ORDER BY
			posting_date
		""".format(filters.get('customer'), is_credit_sale), as_dict=True)
	else:
		data = frappe.db.sql("""
			SELECT
				si.name AS sales_invoice_name,
				si.customer,
				si.posting_date AS posting_date,
				CASE
					WHEN si.docstatus = 1 THEN 'Submitted'
					WHEN si.docstatus = 0 THEN 'Draft'
					WHEN si.docstatus = 2 THEN 'Cancelled'
					ELSE ''
				END AS docstatus,
				si.rounded_total AS amount,
				si.paid_amount,
				si.rounded_total - IFNULL(si.paid_amount, 0) AS balance_amount
			FROM
				`tabSales Invoice` si
			WHERE
				si.credit_sale = {0}
			ORDER BY
				posting_date
			""".format(is_credit_sale), as_dict=True)

	return data

def get_columns():
	return [
		{

			"fieldname": "sales_invoice_name",
			"fieldtype": "Link",
			"label": "Invoice No",
			"options": "Sales Invoice",
			"width": 150,

		},
		{

			"fieldname": "customer",
			"fieldtype": "Link",
			"label": "Customer",
			"options": "Customer",
			"width": 210,

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
			"width": 120,
		},
  		{
			"fieldname": "balance_amount",
			"fieldtype": "Currency",
			"label": "Balance Amount",
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
			"options": "Account" ,
			"width": 120,
		}
	]
