# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from digitz_erp.accounts.report.digitz_erp import filter_accounts

value_fields = (
	"opening_debit",
	"opening_credit",
	"debit",
	"credit",
	"closing_debit",
	"closing_credit",
)

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_data(filters=None):
	accounts = frappe.db.sql(
		"""
			select
				name, parent_account, lft, rgt, 0 as opening_debit, 0 as opening_credit, 0 as debit, 0 as credit, 0 as closing_debit, 0 as closing_credit
			from
				`tabAccount` order by lft
		""",as_dict=True
	)
	accounts, accounts_by_name, parent_children_map = filter_accounts(accounts)
	min_lft, max_rgt = frappe.db.sql(
		"""
			select
				min(lft), max(rgt)
			from
				`tabAccount`
		""",)[0]
	total_row = []
	data = prepare_data(accounts, filters, total_row, parent_children_map, accounts_by_name)
	return data

def prepare_data(accounts, filters, total_row, parent_children_map, accounts_by_name):
	data = []
	for d in accounts:
		row = get_account_details(d.name, d.parent_account, d.indent, filters)
		print(row)
		for key in value_fields:
			amt = row.get(key) or 0
			accounts_by_name[d.name][key] += amt
	accumulate_values_into_parents(accounts, accounts_by_name)
	for d in accounts:
		row = {}
		row['account'] = d.name
		for key in value_fields:
			row[key] = accounts_by_name[d.name][key]
		row['indent'] = d.indent
		data.append(row)
	return data

def get_account_details(account, parent_account, indent, filters):
	query = """
		SELECT
			glp.account,
			0,
			0,
			SUM(glp.debit_amount) as debit,
			SUM(glp.credit_amount) as credit,
			CASE
				WHEN SUM(glp.debit_amount) > SUM(glp.credit_amount) THEN SUM(glp.debit_amount) - SUM(glp.credit_amount)
				ELSE 0
			END AS closing_debit,
			CASE
				WHEN SUM(glp.debit_amount) < SUM(glp.credit_amount) THEN SUM(glp.credit_amount) - SUM(glp.debit_amount)
				ELSE 0
			END AS closing_credit
		FROM
			`tabGL Posting` as glp,
			`tabAccount` as a
		WHERE
			(a.name = '{0}' or a.parent_account = '{0}') AND
			glp.account = a.name
	""".format(account)
	if filters.get('from_date'):
		query += "AND glp.posting_date >= '{0}'".format(filters.get('from_date'))
	if filters.get('to_date'):
		query += "AND glp.posting_date <= '{0}'".format(filters.get('to_date'))
	data = frappe.db.sql(query, as_dict=True)[0]
	data['parent_account'] = parent_account
	data['indent'] = indent
	data['account'] = account
	data['opening_debit'] = 0
	data['opening_credit'] = 0
	opening_balance = get_opening_balance(account, filters)
	if opening_balance.get('opening_debit'):
		data['opening_debit'] = opening_balance.get('opening_debit')
	if opening_balance.get('opening_credit'):
		data['opening_credit'] = opening_balance.get('opening_credit')
	return data

def get_columns():
	return [
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 355,
		},
		{
			"fieldname": "opening_debit",
			"label": _("Opening (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "opening_credit",
			"label": _("Opening (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "debit",
			"label": _("Debit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 155,
		},
		{
			"fieldname": "credit",
			"label": _("Credit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": "closing_debit",
			"label": _("Closing (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": "closing_credit",
			"label": _("Closing (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		}
	]

def get_opening_balance(account, filters):
	query = """
		SELECT
			glp.account,
			IFNULL(SUM(glp.debit_amount),0) as opening_debit,
			IFNULL(SUM(glp.credit_amount),0) as opening_credit
		FROM
			`tabGL Posting` as glp,
			`tabAccount` as a
		WHERE
			(a.name = '{0}' or a.parent_account = '{0}') AND
			glp.account = a.name
	""".format(account)
	if filters.get('from_date'):
		query += "AND glp.posting_date < '{0}'".format(filters.get('from_date'))
	data = frappe.db.sql(query, as_dict=True)[0]
	return data

def accumulate_values_into_parents(accounts, accounts_by_name):
	for d in reversed(accounts):
		if d.parent_account:
			for key in value_fields:
				accounts_by_name[d.parent_account][key] += d[key]
