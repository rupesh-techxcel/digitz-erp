# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from digitz_erp.api.settings_api import get_period_list
    
def execute(filters=None):
    
    if filters.get('filter_based_on') == "Fiscal Year" and not filters.get('year'):        
        frappe.throw("Select year for the Fiscal Year")
    
    data,columns = get_data(filters)
    return columns, data

def get_columns(period_list):
    columns = [
        {
            "fieldname": "account",
            "label": "Cash Flow",
            "fieldtype": "Data",
            "width": 300,
        },
        {
            "fieldname": "total",
            "label": "Amount",
            "fieldtype": "Currency",
            "width": 150,
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

def get_data(filters=None):
    
    cash_flow_accounts = get_cash_flow_accounts()

    data = []

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
    
    columns = get_columns(period_list)    

    # Assuming cash flow operations data is returned as a dictionary
    grand_total = 0

    for cash_flow_account in cash_flow_accounts:
        
        section_total = 0

        data.append(
            {
                "account": cash_flow_account["section_header"],
                "value":None,
                "indent": 0.0				
            }
        )
        
        if len(data) == 1:
            
            net_profit_data,total = get_net_profit_period_wise (period_list)
            net_profit_data.update(                
                {
                    "account": "Profit for the period",
                    "indent": 1
                }
            )
            
            section_total = section_total + total
            
            data.append(net_profit_data)            
        
        
        # Add total value to the first column
        
        
        for account in cash_flow_account["account_types"]:

            account_type_data,total = get_account_type_period_wise_data(account["account_type"], period_list, account["cash_impact"])
            
            print("total")
            print(total)
        
            account_type_data.update(                
                {
                    "account": account["label"],
                    "indent": 1
                }
            )
        
            data.append(account_type_data)
            
            section_total = section_total + total
            
            grand_total = grand_total + total
            
            print("section_total")
            print(section_total)

        data.append(
        {
                "account": cash_flow_account["section_footer"],
                "total":section_total,
                "indent": 0.0				
            }
         )
        
        print("section completed")

    data.append(
            {
                "account": "Net Change In Cash",
                "total": grand_total,
                "indent": 0.0				
            }
        )

    print("Process completed")
    
    print(data)

    return data, columns

def get_net_profit(from_date, to_date):
    
    query = """
            SELECT sum(credit_amount) - sum(debit_amount) as balance 
            FROM `tabGL Posting` gl 
            INNER JOIN `tabAccount` a ON a.name = gl.account 
            WHERE posting_date >= %s AND posting_date <= %s AND a.root_type = 'Income'
            """
    income_balance_data = frappe.db.sql(query, (from_date, to_date), as_dict=1)

    query = """
            SELECT sum(debit_amount) - sum(credit_amount) as balance 
            FROM `tabGL Posting` gl 
            INNER JOIN `tabAccount` a ON a.name = gl.account 
            WHERE posting_date >= %s AND posting_date <= %s AND a.root_type = 'Expense'
            """
    expense_balance_data = frappe.db.sql(query, (from_date, to_date), as_dict=1)

    income_balance = income_balance_data[0]['balance'] if income_balance_data and 'balance' in income_balance_data[0] else 0
    expense_balance = expense_balance_data[0]['balance'] if expense_balance_data and 'balance' in expense_balance_data[0] else 0
    
    net_profit = (income_balance if income_balance else 0) - (expense_balance if expense_balance else 0)
        
    return net_profit

def get_cash_flow_accounts():
    
    # Deperciation is a non-cash expense , so to make the effect treating it as cash_out_flow, to reduce it from the net income.
    operation_accounts = {
            "section_name": "Operations",
            "section_footer": "Net Cash from Operations",
            "section_header": "Cash Flow from Operations",
            "account_types": [
            {"account_type": "Depreciation", "label": "Depreciation", "cash_impact": "Cash Outflow"},
            {"account_type": "Receivable", "label": "Net Change in Accounts Receivable", "cash_impact": "Cash Outflow"},
            {"account_type": "Payable", "label": "Net Change in Accounts Payable", "cash_impact": "Cash Inflow"},
            {"account_type": "Stock", "label": "Net Change in Inventory", "cash_impact": "Cash Outflow"},
            {"account_type": "Accrued Expense", "label": "Net Change in Accrued Expense", "cash_impact": "Cash Inflow"},
            {"account_type": "Deferred Income", "label": "Net Change in Deferred Income", "cash_impact": "Cash Inflow"}
            ],
        }

    investing_accounts = {
            "section_name": "Investing",
            "section_footer": "Net Cash from Investing",
            "section_header": "Cash Flow from Investing",
            "account_types": [
            {"account_type": "Fixed Asset", "label": "Net Change in Fixed Asset", "cash_impact": "Cash Outflow"},            
            {"account_type": "Investment", "label": "Net Change in Investments", "cash_impact": "Cash Outflow"},
            {"account_type": "Loans Given", "label": "Net Cash Used in Loans Given", "cash_impact": "Cash Outflow"}
            ],
        }

    financing_accounts = {
            "section_name": "Financing",
            "section_footer": "Net Cash from Financing",
            "section_header": "Cash Flow from Financing",
            "account_types": [
            {"account_type": "Long Term Liablity", "label": "Net Change In Long Term Liability", "cash_impact": "Cash Inflow"},
            {"account_type": "Equity", "label": "Net Change In Equity", "cash_impact": "Cash Inflow"}
            ],
        }

	# combine all cash flow accounts for iteration
    return [operation_accounts, investing_accounts, financing_accounts]

def get_net_profit_period_wise(period_list):
    
    data = {}
    
    total_net_profit = 0
    
    for period in period_list:
    
        net_profit_for_period = get_net_profit(period["from_date"], period["to_date"])    
        data.setdefault(period["key"], net_profit_for_period)
        total_net_profit = total_net_profit + net_profit_for_period
        
    data["total"] = total_net_profit
    
    return data,total_net_profit

def get_account_type_period_wise_data(account_type, period_list, cash_flow_impact):    
    
    total = 0
    data = {}
    
    for period in period_list:        
                
        amount = get_account_type_period_wise_gl_data(account_type,period["from_date"], period["to_date"])
        
        data.setdefault(period["key"], amount if cash_flow_impact== "Cash Inflow" else amount * -1)
        
        total = (total + amount) if cash_flow_impact == "Cash Inflow"  else (total-amount)
        
    data["total"] = total
    
    return data,total

# Only taking the transactions done between the dates and not with comparison from previous period
def get_account_type_period_wise_gl_data(account_type, from_date,to_date):
    
    query = """
            SELECT a.root_type,sum(debit_amount) - sum(credit_amount) as balance 
            FROM `tabGL Posting` gl 
            INNER JOIN `tabAccount` a ON a.account_name = gl.account 
            WHERE a.account_type = %s 
            AND posting_date >= %s 
            AND posting_date <= %s
            GROUP BY a.root_type
            """
    # Execute the query
    data = frappe.db.sql(query, (account_type, from_date,to_date), as_dict=True)
    
    account_type_total = 0
    for gl_data in data:
        
        if gl_data.root_type == "Asset" and gl_data.balance < 0:  #Asset with credit balance            
            account_type_total = account_type_total - gl_data.balance
        elif  gl_data.root_type == "Expense" and gl_data.balance < 0: #Expense with credit balance            
            account_type_total = account_type_total - gl_data.balance
        elif  gl_data.root_type == "Liability" and gl_data.balance > 0: #Liability with debit balance            
            account_type_total = account_type_total - gl_data.balance
        elif  gl_data.root_type == "Income" and gl_data.balance > 0: #Income with debit balance            
            account_type_total = account_type_total - gl_data.balance            
        else:
            account_type_total = account_type_total + gl_data.balance
            

    # Make the Abs value of the total
    if account_type_total<0:
        account_type_total  = account_type_total * -1
        
    return account_type_total
