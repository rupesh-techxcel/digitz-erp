import frappe
from frappe.utils import *

@frappe.whitelist()
def get_accounts_data(for_gp, period_list):
    
    query = ""
    
    if for_gp:
        query = """
               SELECT parent_account, account_name, root_type
                FROM `tabAccount`
                WHERE is_group = 0 AND (root_type='Expense' OR root_type='Income') AND include_in_gross_profit=1
                ORDER BY FIELD(root_type, 'Income', 'Expense')
                """
    else:
         query = """
                SELECT parent_account, account_name, root_type
                FROM `tabAccount`
                WHERE is_group = 0 AND (root_type='Expense' OR root_type='Income') AND include_in_gross_profit=0
                ORDER BY FIELD(root_type, 'Income', 'Expense')
                """
        
    data = frappe.db.sql(query, as_dict=True)
      
    accounts = {}
    
    for d in data:
        
        for period in period_list:
            
            period_from_date = period["from_date"] #Always to use from date to get the correct value for 'as on the to_date'
            
            period_to_date = period["to_date"]
                
            balance = get_account_balance(d.account_name,period_from_date,period_to_date)
                    
            if(not balance):
                balance = 0
                
            if(d.root_type == "Income"):
                balance = balance * -1
                
            if balance == 0:
                continue
            
            if d.account_name not in accounts:
                accounts[d.account_name] = {}
            
            accounts[d.account_name][period["key"]] = balance
            
            if d.parent_account not in accounts:
                accounts[d.parent_account] = {}
            
            accounts[d.parent_account][period["key"]] = accounts[d.parent_account].get(period["key"], 0) + balance
                        
            update_parent_accounts_recursive(d.parent_account,accounts,d.account_name, balance, period)
        
    return accounts

# Method to update the parent account of the account passing in, not the account's 
# Means, currently passed in account's values already updated
def update_parent_accounts_recursive(account, accounts, account_name, balance, period):
    account_doc = frappe.get_doc('Account',account)
    
    # The parent account intend to be updated is the root account and need not update
    if(account_doc.parent_account == None):
        return;
    
    parent_account = account_doc.parent_account
    
    # Initialize parent account if not already done
    if parent_account not in accounts:
            accounts[parent_account] = {"parent": parent_account}
    
    accounts[parent_account][period["key"]] = accounts[parent_account].get(period["key"], 0) + balance
    
    update_parent_accounts_recursive(parent_account,accounts,account_name, balance, period)
    
def get_account_balance(account, from_date,to_date):
    
    query =""
                
    query="""
    SELECT sum(debit_amount)-sum(credit_amount) as balance from `tabGL Posting` gl where gl.account = %s and posting_date >= %s and posting_date<=%s
    """
    
    data = frappe.db.sql(query,(account,from_date,to_date), as_dict=True)
    if data and data[0]:
        return data[0].balance
    else:
        return 0
