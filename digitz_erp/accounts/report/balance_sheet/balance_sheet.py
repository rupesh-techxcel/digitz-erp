# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from digitz_erp.accounts.report.digitz_erp import filter_accounts

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(filters)
    return columns, data, None, chart

def get_chart_data(filters=None):
    data = get_data(filters)
    datasets = []
    values = []
    labels = ['Asset', 'Liability', 'Provisional Profit/Loss']
    for d in data:
        if d.get('account') == 'Total Asset (Debit)':
            values.append(d.get('amount'))
        if d.get('account') == 'Total Liability (Credit)':
            values.append(d.get('amount'))
        if d.get('account') == 'Provisional Profit/Loss':
            values.append(d.get('amount'))
    datasets.append({'values': values})
    chart = {"data": {"labels": labels, "datasets": datasets}, "type": "bar"}
    chart["fieldtype"] = "Currency"
    return chart

def get_data(filters=None):
    accounts = frappe.db.sql(
        """
        SELECT
            a.name,
            a.parent_account,
            a.lft,
            a.rgt,
            a.root_type
        FROM
            `tabAccount` a
        WHERE
            a.root_type IN ('Asset','Liability')
        OR
            a.name = 'Accounts'
        ORDER BY
            a.lft;
        """,
        as_dict=True
    )
    accounts, accounts_by_name, parent_children_map = filter_accounts(accounts)
    data = prepare_data(accounts, filters, parent_children_map)

    total_asset_debit = sum(row['amount'] for row in data if row.get('root_type') == 'Asset')
    total_liability_credit = sum(row['amount'] for row in data if row.get('root_type') == 'Liability')
    provisional_profit_or_loss = total_liability_credit + total_asset_debit
    total_row = {
        'account': 'Total Asset (Debit)',
        'amount': total_asset_debit,
        'parent_account': '',
        'indent': 0
    }
    data.append(total_row)

    total_row = {
        'account': 'Total Liability (Credit)',
        'amount': total_liability_credit,
        'parent_account': '',
        'indent': 0
    }
    data.append(total_row)

    total_row = {
        'account': 'Provisional Profit/Loss',
        'amount': provisional_profit_or_loss,
        'parent_account': '',
        'indent': 0
    }
    data.append(total_row)

    return data

def prepare_data(accounts, filters, parent_children_map):
    data = []
    for d in accounts:
        row = get_account_details(d.name, d.parent_account, d.indent, filters)
        data.append(row)
    return data

def get_account_details(account, parent_account, indent, filters):
    query = """
        SELECT
            a.root_type,
            CASE
				WHEN a.root_type='Asset' THEN SUM(glp.debit_amount)
                WHEN a.root_type='Liability' THEN SUM(glp.credit_amount)
				ELSE 0
			END AS amount
        FROM
            `tabGL Posting` as glp,
            `tabAccount` as a
        WHERE
            (a.name = '{0}' or a.parent_account = '{0}') AND
            glp.account = a.name
    """.format(account)
    if filters.get('year_selection') == 'Date Range':
        if filters.get('from_date'):
            query += "AND glp.posting_date >= '{0}'".format(filters.get('from_date'))
        if filters.get('to_date'):
            query += "AND glp.posting_date <= '{0}'".format(filters.get('to_date'))
    elif filters.get('year_selection') == 'Fiscal Year':
        fiscal_year = filters.get('select_year')
        if fiscal_year:
            query += " AND glp.posting_date >= '{0}-01-01' AND glp.posting_date <= '{0}-12-31'".format(fiscal_year)
    result = frappe.db.sql(query, as_dict=True)[0]

    data = {
        'account': account,
        'parent_account': parent_account,
        'indent': indent,
        'amount': result['amount'] or 0,
        'root_type': result['root_type'] or '',
    }
    return data

def get_columns():
    return [
        {
            "fieldname": "account",
            "label": _("Account"),
            "fieldtype": "Data",
            "width": 600,
        },
        {
            "fieldname": "amount",
            "label": _("Amount"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 600,
        }
    ]
