# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from digitz_erp.accounts.report.digitz_erp import filter_accounts,sort_accounts
from digitz_erp.api.balance_sheet_api import get_accounts_data
from datetime import datetime, timedelta
from digitz_erp.api.settings_api import get_period_list

def execute(filters=None):
    
    print("from Balance Sheet")
    # columns = get_columns()
    data,columns,summary = get_data(filters)
    
    print(data)
    
    # chart = get_chart_data(filters)
    return columns, data, None, None, summary

def get_data(filters=None):
    
    print("from get_data")
    
    from_date = None
    to_date = None

    if filters.get('filter_based_on') == "Fiscal Year":
        
        year = filters.get('year')        
        from_date = f'{year}-01-01'
        to_date = f'{year}-12-31'
    else:
        from_date = filters.get('from_date')
        to_date = filters.get('to_date')
        
    periodicity = filters.get('periodicity')   
        
    period_list = get_period_list(from_date,to_date,  periodicity)
    
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
        
        from_date = datetime(filters.get('select_year'),1,1)
        to_date = datetime(filters.get('select_year',12,31))
        
    if filters.get('accumulated_values'):
        from_date = datetime(2000,1,1)
        
    print("before bs_accounts")
        
    bs_accounts = get_accounts_data(from_date, to_date, period_list)    
        
    print("bs_accounts")
    print(bs_accounts)
    #print("accounts")
    
    #print(accounts)
    
    indices_to_remove = []
    
     # Iterate through accounts and update with data from bs_accounts
    for i,account in enumerate(accounts):
        account_name = account['name']
        if account_name in bs_accounts:            
            # Initialize period data for each key from period_list
            for period in period_list:
                key = period['key']
                # Set data from bs_accounts or zero if not present
                account[key] = bs_accounts[account_name].get(key, 0)
        else:
            
            indices_to_remove.append(i)    
            
    # Remove rows based on indices
    for index in reversed(indices_to_remove):
        del accounts[index]
      
    # filter_accounts(accounts)
    
    accounts= sort_accounts(accounts)    
    
    gp_data = {'name': 'Provisional Profit', 'indent': 2}

    for period in period_list:
        income_query = """
            SELECT SUM(credit_amount) - SUM(debit_amount) AS balance
            FROM `tabGL Posting` gl
            INNER JOIN `tabAccount` a ON a.name = gl.account
            WHERE posting_date >= %s AND posting_date <= %s AND a.root_type = 'Income'
        """
        income_balance_data = frappe.db.sql(income_query, (from_date, period["to_date"]), as_dict=True)

        expense_query = """
            SELECT SUM(debit_amount) - SUM(credit_amount) AS balance
            FROM `tabGL Posting` gl
            INNER JOIN `tabAccount` a ON a.name = gl.account
            WHERE posting_date >= %s AND posting_date <= %s AND a.root_type = 'Expense'
        """
        expense_balance_data = frappe.db.sql(expense_query, (from_date, period["to_date"]), as_dict=True)

        # Safe handling of potential None values in balance data
        income_balance = income_balance_data[0]['balance'] if income_balance_data and income_balance_data[0]['balance'] is not None else 0
        expense_balance = expense_balance_data[0]['balance'] if expense_balance_data and expense_balance_data[0]['balance'] is not None else 0

        profit = income_balance - expense_balance
        gp_data[period["key"]] = profit    
        
    data =[]
    
    assets_total = 0
    liabilities_total = 0
    profit = 0
    
    # Assuming period_list is not empty and each dictionary has a 'key'
    last_period = period_list[-1]  # Access the last dictionary in the list
    last_key = last_period['key']  # Retrieve the value of 'key' from the last dictionary
    
    for account in accounts:
        
        if account.name == "Accounts":
            continue
        
        if account.name == "Asset":
            assets_total = account[last_key]
        
        # Include profit in the liability
        # Include profit in the liability
        if account['name'] == "Liability":
            for period in period_list:
                key = period['key']
                # Ensure there's a default value of 0 for both account and gp_data before adding
                account[key] = account.get(key, 0) + gp_data.get(key, 0)
        
            liabilities_total = account[last_key]
                
        data.append(account)
        
    profit = gp_data[last_key]
    
    data.append(gp_data)
    
    columns = get_columns(period_list)
    
    summary_data = []
    
    summary_data.append({            
          
            "label": "Total Asset",
            "value": assets_total,
            "datatype": "Currency",            
            "currency": "AED"        
        })
    
    summary_data.append({            
          
            "label": "Total Liability",
            "value": liabilities_total,
            "datatype": "Currency",            
            "currency": "AED"        
        })
    
    summary_data.append({            
          
            "label": "Provisional Profit/Loss",
            "value": profit,
            "datatype": "Currency",            
            "currency": "AED",
            "indicator": "Green" if profit > 0 else  ("Red" if profit<0 else "Black")
        })
    
    
    print("eof get_data")
    return data,columns,summary_data

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

def get_columns(period_list):
    columns = [
        {
            "fieldname": "name",
            "label": _("Account"),
            "fieldtype": "Data",
            "width": 400,
        }        
    ]
    
    if period_list:
        for period in period_list:
            columns.append(
                {
                    "fieldname": period.key,
                    "label": period.label,
                    "fieldtype": "Currency",
                    "options": "currency",
                    "width": 150,
                }
            )
    return columns


