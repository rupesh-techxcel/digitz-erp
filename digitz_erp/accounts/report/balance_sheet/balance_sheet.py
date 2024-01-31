# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from digitz_erp.accounts.report.digitz_erp import filter_accounts
from digitz_erp.api.balance_sheet_api import get_accounts_data
from datetime import datetime, timedelta

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    print("filters")
    print(filters)
        
    # chart = get_chart_data(filters)
    return columns, data, None, None

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
        select
            name,
            parent_account,
            lft,
            rgt,
            balance
        from
            `tabAccount` 
        where root_type in ('Asset','Liability')  or name = 'Accounts' 
        ORDER BY FIELD(root_type, 'Asset', 'Liability') , lft
    """, as_dict=True
    )

    from_date = filters.get('from_date')
    to_date = filters.get('to_date')
    
    if(filters.get('period_selection')== "Fiscal Year"):
        print("in Fiscal Year")
        from_date = datetime(filters.get('select_year'),1,1)
        to_date = datetime(filters.get('select_year',12,31))
        
    if filters.get('accumulated_values'):
        from_date = datetime(2000,1,1)
        
    bs_accounts = get_accounts_data(from_date, to_date)
    print("bs_accounts")
    print(bs_accounts)
    
    indices_to_remove = []
    gross_profit = 0
    for i,account in enumerate(accounts):
        found = False
        for account2 in bs_accounts:
            if account["name"] == account2["name"]:
                account["balance"] = account2["balance"] 
                found = True
        
        if not found:
                    indices_to_remove.append(i)

    # Remove rows based on indices
    for index in reversed(indices_to_remove):
        del accounts[index]
      
    filter_accounts(accounts)
        
    # Net Profit
    query = """
            SELECT sum(credit_amount)-sum(debit_amount) as balance from `tabGL Posting` gl inner join `tabAccount` a on a.name = gl.account where posting_date >= %s and posting_date<=%s and a.root_type in ('Income') 
            """
    income_balance_data = frappe.db.sql(query,(from_date, to_date), as_dict = 1)
    
    query = """
            SELECT sum(debit_amount)-sum(credit_amount) as balance from `tabGL Posting` gl inner join `tabAccount` a on a.name = gl.account where posting_date >= %s and posting_date<=%s and a.root_type in ('Expense') 
            """
    expense_balance_data = frappe.db.sql(query,(from_date, to_date), as_dict = 1)
    
    profit = (income_balance_data[0].balance if (income_balance_data and income_balance_data[0].balance) else 0) - (expense_balance_data[0].balance if (expense_balance_data and expense_balance_data[0].balance ) else 0)
    
    
    data =[]
    for account in accounts:
        
        if account.name == "Accounts":
            continue
        
        # Include profit in the liability
        if account.name =="Liability":
            account.balance = account.balance + profit
       
        data.append(account)
    
    gp_data = {'name':'Provisional Profit','indent':2,'balance' :profit}
    data.append(gp_data)
    
    
    return data

def get_columns():
    return [
        {
            "fieldname": "name",
            "label": _("Account"),
            "fieldtype": "Data",
            "width": 400,
        },
        {
            "fieldname": "balance",
            "label": _("Amount"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 200,
        }
    ]


