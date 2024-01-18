# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from digitz_erp.accounts.report.digitz_erp import filter_accounts

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_data(filters=None):
    accounts = frappe.db.sql(
        """
            select
                name,
                parent_account,
                lft,
                rgt,
                balance
            from
                `tabAccount` order by lft
        """, as_dict=True
    )
    accounts, accounts_by_name, parent_children_map = filter_accounts(accounts)
    data = prepare_data(accounts, parent_children_map, accounts_by_name)
    return data

def prepare_data(accounts, parent_children_map, accounts_by_name):
    data = []
    for d in accounts:
        row = get_account_details(d.name, d.parent_account, d.indent)
        accounts_by_name[d.name]['balance'] += row['balance']
        accumulate_values_into_parents(accounts_by_name, d.parent_account, row['balance'])
        row['account'] = d.name
        data.append(row)
    return data

def get_account_details(account, parent_account, indent):
    data = {}
    data['parent_account'] = parent_account
    data['indent'] = indent
    data['account'] = account
    data['balance'] = frappe.get_value("Account", account, "balance")
    return data

def accumulate_values_into_parents(accounts_by_name, parent_account, balance):
    if parent_account:
        accounts_by_name[parent_account]['balance'] += balance
        accumulate_values_into_parents(accounts_by_name, accounts_by_name[parent_account]['parent_account'], balance)

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
            "fieldname": "balance",
            "label": _("Balance"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 150,
        }
    ]
