# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from digitz_erp.accounts.report.digitz_erp import filter_accounts, sort_accounts
from digitz_erp.api.profit_and_loss_statement_api import get_accounts_data
from datetime import datetime, timedelta
from digitz_erp.api.settings_api import get_period_list

def execute(filters=None):
    
    data,columns = get_data(filters)    
   
    chart = get_chart_data(filters)
    
    report_summary = get_report_summary(filters)
    
    return columns, data, None,chart, report_summary
    # return columns, data
# , None,None, report_summary

def get_chart_data(filters=None):
    
     # Net Profit
    query = """
            SELECT sum(credit_amount)-sum(debit_amount) as balance from `tabGL Posting` gl inner join `tabAccount` a on a.name = gl.account where posting_date >= %s and posting_date<=%s and a.root_type in ('Income') 
            """
    income_balance_data = frappe.db.sql(query,(filters.get('from_date'), filters.get('to_date')), as_dict = 1)
    
    query = """
            SELECT sum(debit_amount)-sum(credit_amount) as balance from `tabGL Posting` gl inner join `tabAccount` a on a.name = gl.account where posting_date >= %s and posting_date<=%s and a.root_type in ('Expense') 
            """
    expense_balance_data = frappe.db.sql(query,(filters.get('from_date'), filters.get('to_date')), as_dict = 1)
    
    profit = (income_balance_data[0].balance if income_balance_data and income_balance_data[0].balance else 0) - expense_balance_data[0].balance if expense_balance_data and expense_balance_data[0].balance else 0
    
    datasets = []
    values = []
    labels = ['Income', 'Expense', 'Net Profit/Loss']
    values.append(income_balance_data[0].balance if income_balance_data and income_balance_data[0].balance else 0)
    values.append(expense_balance_data[0].balance if expense_balance_data and expense_balance_data[0].balance else 0)
    values.append(profit)
    
    # for d in data:
    #     if d.get('account') == 'Total Income (Credit)':
    #         values.append(d.get('amount'))
    #     if d.get('account') == 'Total Expense (Debit)':
    #         values.append(d.get('amount'))
    #     if d.get('account') == 'Net Profit':
    #         values.append(d.get('amount'))
            
    datasets.append({'values': values})
    chart = {"data": {"labels": labels, "datasets": datasets}, "type": "bar"}
    chart["fieldtype"] = "Currency"
    return chart

def get_report_summary(filters=None):

    profit_label = _("Net Profit")
    income_label = _("Total Income")
    expense_label = _("Total Expense")
    
    query = """
            SELECT sum(credit_amount)-sum(debit_amount) as balance from `tabGL Posting` gl inner join `tabAccount` a on a.name = gl.account where posting_date >= %s and posting_date<=%s and a.root_type in ('Income') 
            """
    income_balance_data = frappe.db.sql(query,(filters.get('from_date'), filters.get('to_date')), as_dict = 1)
    
    net_income =income_balance_data[0].balance if income_balance_data and income_balance_data[0].balance else 0
    
    query = """
            SELECT sum(debit_amount)-sum(credit_amount) as balance from `tabGL Posting` gl inner join `tabAccount` a on a.name = gl.account where posting_date >= %s and posting_date<=%s and a.root_type in ('Expense') 
            """
    expense_balance_data = frappe.db.sql(query,(filters.get('from_date'), filters.get('to_date')), as_dict = 1)
    
    net_expense = expense_balance_data[0].balance if expense_balance_data and expense_balance_data[0].balance else 0
    
    net_profit = (income_balance_data[0].balance if income_balance_data and income_balance_data[0].balance else 0) - expense_balance_data[0].balance if expense_balance_data and expense_balance_data[0].balance else 0
    
    currency = "AED"
    
    return [
		{"value": net_income, "label": income_label, "datatype": "Currency", "currency": currency},
		{"type": "separator", "value": "-"},
		{"value": net_expense, "label": expense_label, "datatype": "Currency", "currency": currency},
		{"type": "separator", "value": "=", "color": "blue"},
		{
			"value": net_profit,
			"indicator": "Green" if net_profit > 0 else "Red",
			"label": profit_label,
			"datatype": "Currency",
			"currency": currency,
		},
	]
    
  
def get_data(filters= None):
      
    accounts = frappe.db.sql(
        """
            select
                name,
                parent_account,
                lft,
                rgt,
                balance,
                is_group,
                root_type
            from
                `tabAccount` 
            where root_type in ('Expense','Income')  or name = 'Accounts' and (is_group=1 or (is_group=0 and include_in_gross_profit =1))
            ORDER BY FIELD(root_type, 'Income', 'Expense'),lft,rgt
        """, as_dict=True
    )
    
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')
    
    periodicity = filters.get('periodicity')   
        
    period_list = get_period_list(from_date,to_date,  periodicity)
    
    if(filters.get('period_selection')== "Fiscal Year"):
                
        from_date = datetime(filters.get('select_year'),1,1)
        to_date = datetime(filters.get('select_year',12,31))
    
    gp_accounts = get_accounts_data(for_gp=True,period_list= period_list)
    
    indices_to_remove = []
    
     # Iterate through accounts and update with data from bs_accounts
    for i,account in enumerate(accounts):
        account_name = account['name']
        if account_name in gp_accounts:            
            # Initialize period data for each key from period_list
            for period in period_list:
                key = period['key']
                # Set data from bs_accounts or zero if not present
                account[key] = gp_accounts[account_name].get(key, 0)
        else:
            
            indices_to_remove.append(i)    

    # Remove rows based on indices
    for index in reversed(indices_to_remove):
        del accounts[index]
        
    # filter_accounts(accounts)
    accounts  = sort_accounts(accounts)
    #print("accounts sorted")
    #print(accounts)
    
    data =[]
    
    for account in accounts:
        
        if account.name == "Accounts":
            continue
        else:
            # if(account.name == "Income"):
            #     account.name = "Revenue"
                
            data.append(account)
    
    profit = 0    
   
    gp_data = {'name':'Gross Profit','indent':2}
    
    for period in period_list:    
        query = """
                SELECT sum(credit_amount)-sum(debit_amount) as balance from `tabGL Posting` gl inner join `tabAccount` a on a.name = gl.account where posting_date >= %s and posting_date<=%s and a.root_type in ('Income') and a.include_in_gross_profit = 1
                """
        income_balance_data = frappe.db.sql(query,(period['from_date'],period['to_date']), as_dict = 1)
        
        query = """
                SELECT sum(debit_amount)-sum(credit_amount) as balance from `tabGL Posting` gl inner join `tabAccount` a on a.name = gl.account where posting_date >= %s and posting_date<=%s and a.root_type in ('Expense') and a.include_in_gross_profit = 1
                """
        expense_balance_data = frappe.db.sql(query,(period['from_date'], period['to_date']), as_dict = 1)
        
        
        income_balance = income_balance_data[0]['balance'] if income_balance_data and income_balance_data[0]['balance'] is not None else 0
        expense_balance = expense_balance_data[0]['balance'] if expense_balance_data and expense_balance_data[0]['balance'] is not None else 0

        profit = income_balance - expense_balance        
        
        gp_data[period["key"]] = profit            
    
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
            ORDER BY FIELD(root_type, 'Income', 'Expense'),lft,rgt
        """, as_dict=True
    )
    
    indices_to_remove = []
    np_accounts = get_accounts_data(for_gp=False, period_list=period_list)
      
    for i,account in enumerate(accounts):
        account_name = account['name']
        if account_name in np_accounts:
            # Initialize period data for each key from period_list
            for period in period_list:
                key = period['key']
                # Set data from bs_accounts or zero if not present
                account[key] = np_accounts[account_name].get(key, 0)
        else:
            
            indices_to_remove.append(i)    

    # Remove rows based on indices
    for index in reversed(indices_to_remove):
        del accounts[index]
    
    # filter_accounts(accounts)
    accounts  = sort_accounts(accounts)
    
    for account in accounts:
        
        if account.name == "Accounts":
            continue
        else:
            # if(account.name == "Income"):
            #     account.name = "Revenue"
                
            data.append(account)

    gp_data = {'name':'Net Profit','indent':2}
    
    for period in period_list:
        # Net Profit
        query = """
                SELECT sum(credit_amount)-sum(debit_amount) as balance from `tabGL Posting` gl inner join `tabAccount` a on a.name = gl.account where posting_date >= %s and posting_date<=%s and a.root_type in ('Income') 
                """
        income_balance_data = frappe.db.sql(query,(period['from_date'], period['to_date']), as_dict = 1)
        
        query = """
                SELECT sum(debit_amount)-sum(credit_amount) as balance from `tabGL Posting` gl inner join `tabAccount` a on a.name = gl.account where posting_date >= %s and posting_date<=%s and a.root_type in ('Expense') 
                """
        expense_balance_data = frappe.db.sql(query,(filters.get('from_date'), filters.get('to_date')), as_dict = 1)
        
        
        income_balance = income_balance_data[0]['balance'] if income_balance_data and income_balance_data[0]['balance'] is not None else 0
        expense_balance = expense_balance_data[0]['balance'] if expense_balance_data and expense_balance_data[0]['balance'] is not None else 0

        profit = income_balance - expense_balance        
        
        gp_data[period["key"]] = profit
    
    data.append(gp_data)
    
    #print("data")
    
    #print(data)
    
    columns = get_columns(period_list)
        
    return data,columns

def get_columns(period_list):
    columns = [
        {
            "fieldname": "name",
            "label": _("Account"),
            "fieldtype": "Data",
            "width": 600,
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


