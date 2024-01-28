# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from digitz_erp.accounts.report.digitz_erp import filter_accounts
from digitz_erp.api.profit_and_loss_statement_api import get_accounts_data

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
   
    # chart = get_chart_data(filters)
    # return columns, data, None, chart
    return columns, data, None

def get_chart_data(filters=None):
    
    data = get_data(filters)
    datasets = []
    values = []
    labels = ['Income', 'Expense', 'Net Profit/Loss']
    
    for d in data:
        if d.get('account') == 'Total Income (Credit)':
            values.append(d.get('amount'))
        if d.get('account') == 'Total Expense (Debit)':
            values.append(d.get('amount'))
        if d.get('account') == 'Net Profit':
            values.append(d.get('amount'))
            
    datasets.append({'values': values})
    chart = {"data": {"labels": labels, "datasets": datasets}, "type": "bar"}
    chart["fieldtype"] = "Currency"
    return chart

def get_data(filters= None):
    
    # print("accounts")
    # print(accounts)
    
    accounts = frappe.db.sql(
        """
            select
                name,
                parent_account,
                lft,
                rgt,
                balance
            from
                `tabAccount` 
            where root_type in ('Expense','Income')  or name = 'Accounts' and (is_group=1 or (is_group=0 and include_in_gross_profit =1))
            ORDER BY FIELD(root_type, 'Income', 'Expense')
        """, as_dict=True
    )
  
    gp_accounts = get_accounts_data(filters.get('from_date'), filters.get('to_date'),for_gp=True)
    
    indices_to_remove = []
    gross_profit = 0
    for i,account in enumerate(accounts):
        found = False
        for account2 in gp_accounts:
            if account["name"] == account2["name"]:
                account["balance"] = account2["balance"] 
                found = True
        
        if not found:
                    indices_to_remove.append(i)

    # Remove rows based on indices
    for index in reversed(indices_to_remove):
        del accounts[index]
    
    print("accounts") 
    print(accounts)
  
    filter_accounts(accounts)
    
    data =[]
    for account in accounts:
        
        if account.name == "Accounts":
            continue
        else:
            if(account.name == "Income"):
                account.name = "Revenue"
                
            data.append(account)
    
    # Get Gross Profit
    query = """
            SELECT sum(credit_amount)-sum(debit_amount) as balance from `tabGL Posting` gl inner join `tabAccount` a on a.name = gl.account where posting_date >= %s and posting_date<=%s and a.root_type in ('Income') and a.include_in_gross_profit = 1
            """
    income_balance_data = frappe.db.sql(query,(filters.get('from_date'), filters.get('to_date')), as_dict = 1)
    
    query = """
            SELECT sum(debit_amount)-sum(credit_amount) as balance from `tabGL Posting` gl inner join `tabAccount` a on a.name = gl.account where posting_date >= %s and posting_date<=%s and a.root_type in ('Expense') and a.include_in_gross_profit = 1
            """
    expense_balance_data = frappe.db.sql(query,(filters.get('from_date'), filters.get('to_date')), as_dict = 1)
    
    gross_profit = income_balance_data[0].balance - expense_balance_data[0].balance 
    
    gp_data = {'name':'Gross Profit','indent':2,'balance' :gross_profit}
    data.append(gp_data)
    
    # Net Profit Section
    
    accounts = frappe.db.sql(
        """
            select
                name,
                parent_account,
                lft,
                rgt,
                balance
            from
                `tabAccount` 
            where root_type in ('Expense','Income')  or name = 'Accounts' and (is_group=1 or (is_group=0 and include_in_gross_profit =0))
            ORDER BY FIELD(root_type, 'Income', 'Expense')
        """, as_dict=True
    )
    
    np_accounts = get_accounts_data(filters.get('from_date'), filters.get('to_date'),for_gp=False)
    
    indices_to_remove = []
    gross_profit = 0
    for i,account in enumerate(accounts):
        found = False
        for account2 in np_accounts:
            if account["name"] == account2["name"]:
                account["balance"] = account2["balance"] 
                found = True
        
        if not found:
                    indices_to_remove.append(i)

    # Remove rows based on indices
    for index in reversed(indices_to_remove):
        del accounts[index]
    
    print("accounts") 
    print(accounts)
  
    filter_accounts(accounts)
    
    for account in accounts:
        
        if account.name == "Accounts":
            continue
        else:
            if(account.name == "Income"):
                account.name = "Revenue"
                
            data.append(account)
    
    # Get Gross Profit
    query = """
            SELECT sum(credit_amount)-sum(debit_amount) as balance from `tabGL Posting` gl inner join `tabAccount` a on a.name = gl.account where posting_date >= %s and posting_date<=%s and a.root_type in ('Income') 
            """
    income_balance_data = frappe.db.sql(query,(filters.get('from_date'), filters.get('to_date')), as_dict = 1)
    
    query = """
            SELECT sum(debit_amount)-sum(credit_amount) as balance from `tabGL Posting` gl inner join `tabAccount` a on a.name = gl.account where posting_date >= %s and posting_date<=%s and a.root_type in ('Expense') 
            """
    expense_balance_data = frappe.db.sql(query,(filters.get('from_date'), filters.get('to_date')), as_dict = 1)
    
    gross_profit = income_balance_data[0].balance - expense_balance_data[0].balance 
    
    gp_data = {'name':'Net Profit','indent':2,'balance' :gross_profit}
    data.append(gp_data)
    
    
    
    return data

def prepare_data(accounts):
    data = []
    
    for d in accounts:
        print("d[name]")
        print(d["name"])
        
        account = d["name"]
        print(account)
        parent_account = d["parent_account"]
        print(parent_account)
        balance = d["balance"]
        print(balance)
        
        row = get_account_details(accounts[d]["name"], accounts[d]["parent_account"],accounts[d]["balance"])
        # accounts_by_name[d.name]['balance'] += row['balance']
        # accumulate_values_into_parents(accounts_by_name, d.parent_account, row['balance'])
        row['account'] = accounts[d]["name"]
        data.append(row)
        
    return data

def get_account_details(account, parent_account, balance):
    data = {}
    data['parent_account'] = parent_account
    # data['indent'] = indent
    data['account'] = account
    data['balance'] = balance
    # data['balance_dr_cr'] = frappe.get_value("Account", account, "balance_dr_cr")
    return data

def get_data_old(filters=None):
    
    accounts = frappe.db.sql(
        """
        SELECT
            a.name,
            a.parent_account,
            a.lft,
            a.rgt,
            a.root_type,
            0 as amount
        FROM
            `tabAccount` a
        WHERE
            (a.root_type = 'Expense' AND a.include_in_gross_profit = 1)
        OR
        	(a.root_type = 'Income' AND a.include_in_gross_profit = 1)
        OR
            a.name = 'Accounts'
        ORDER BY
        CASE
            WHEN a.root_type = 'Expense' THEN 0
            WHEN a.root_type = 'Income' THEN 1
            ELSE 2
        END,
        a.lft        
        """,
        as_dict=True
    )
    print("accounts 1")
    print(accounts)
    
    accounts, accounts_by_name, parent_children_map = filter_accounts(accounts)
    data = prepare_data(accounts, filters, parent_children_map, accounts_by_name)
    
    total_income_credit = sum(row['amount'] for row in data if row.get('root_type') == 'Income')
    total_expense_debit = sum(row['amount'] for row in data if row.get('root_type') == 'Expense')
    net_profit = total_income_credit - total_expense_debit

    # Append the total_income_credit and total_expense_debit to the data as the last row
    total_row = {
        'account': 'Total Income (Credit)',
        'amount':  '<span style="color: blue;">{0}</span>'.format(total_income_credit),
        'parent_account': '',
        'indent': 0
    }
    total_row = {
        'account': 'Total Income (Credit)',
        'amount': total_income_credit,
        'parent_account': '',
        'indent': 0
    }
    data.append(total_row)

    total_row = {
        'account': 'Total Expense (Debit)',
        'amount': total_expense_debit,
        'parent_account': '',
        'indent': 0
    }
    data.append(total_row)

    total_row = {
        'account': 'Net Profit',
        'amount': net_profit,
        'parent_account': '',
        'indent': 0
    }
    data.append(total_row)
   
    return data

value_fields = (
	"amount",
)

def get_columns():
    return [
        {
            "fieldname": "name",
            "label": _("Account"),
            "fieldtype": "Data",
            "width": 600,
        },
        {
            "fieldname": "balance",
            "label": _("Amount"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 300,
        }
    ]

def accumulate_values_into_parents(accounts, accounts_by_name):
	for d in reversed(accounts):
		if d.parent_account:
			for key in value_fields:
				accounts_by_name[d.parent_account][key] += d[key]
