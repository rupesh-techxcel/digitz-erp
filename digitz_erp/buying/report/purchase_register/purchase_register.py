# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_data(filters):
	data = ""
	if filters.get('credit_purchase'):
		is_credit_purchase = 1
	else:
		is_credit_purchase = 0
	if filters.get('supplier') and  filters.get('from_date') and filters.get('to_date'):

		data = frappe.db.sql("""
		SELECT
			si.supplier,
			si.name AS purchase_invoice_name,
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
			`tabPurchase Invoice` si
		WHERE
			si.supplier = '{0}'
			AND si.posting_date BETWEEN '{1}' AND '{2}'
			AND si.credit_purchase = {3}
		ORDER BY
			si.posting_date
		""".format(filters.get('supplier'), filters.get('from_date'), filters.get('to_date'), is_credit_purchase), as_dict=True)
	elif filters.get('from_date') and filters.get('to_date') and not frappe.get('supplier'):
		data = frappe.db.sql("""
		SELECT
			si.supplier,
			si.name AS purchase_invoice_name,
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
			`tabPurchase Invoice` si
		WHERE
			si.posting_date BETWEEN '{0}' AND '{1}'
			AND si.credit_purchase = {2}
		ORDER BY
			si.posting_date
		""".format(filters.get('from_date'), filters.get('to_date'), is_credit_purchase), as_dict=True)


	elif filters.get('supplier') and not(filters.get('from_date') and filters.get('to_date')):
		data = frappe.db.sql("""
		SELECT
			si.supplier,
			si.name AS purchase_invoice_name,
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
			`tabPurchase Invoice` si
		WHERE
			si.supplier = '{0}'
			AND si.credit_purchase = {1}
		ORDER BY
			posting_date
		""".format(filters.get('supplier'), is_credit_purchase), as_dict=True)
	else:
		data = frappe.db.sql("""
			SELECT
				si.supplier,
				si.name AS purchase_invoice_name,
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
				`tabPurchase Invoice` si
			WHERE
				si.credit_purchase = {0}
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
			"fieldtype": "Data",
			"label": "Payment Mode",
			"width": 120,
		},
		{
			"fieldname": "payment_account",
			"fieldtype": "Data",
			"label": "Payment Account",
			"width": 120,
		}
	]
