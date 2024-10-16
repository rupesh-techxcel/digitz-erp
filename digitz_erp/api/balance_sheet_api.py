import frappe
from frappe.utils import *

@frappe.whitelist()
def get_accounts_data(from_date, to_date, period_list):
   
    query = """
            SELECT parent_account, account_name, root_type
            FROM `tabAccount`
            WHERE is_group = 0 AND (root_type='Asset' OR root_type='Liability')
            ORDER BY FIELD(root_type, 'Asset', 'Liability'), lft
            """
    data = frappe.db.sql(query, as_dict=True)
      
    accounts = {}
    
    for d in data:
        # Initialize dictionary for account if not already done
        # if d.account_name not in accounts:
            # accounts[d.account_name] = {"parent": d.parent_account}

        for period in period_list:
            
            period_from_date = from_date #Always to use from date to get the correct value for 'as on the to_date'
            
            period_to_date = period["to_date"]
            
            balance = get_account_balance(d.account_name, period_from_date, period_to_date)
            balance = 0 if balance is None else balance
            balance = -balance if d.root_type == "Liability" and balance != 0 else balance
            
            if balance == 0:
                continue
            
            if d.account_name not in accounts:
                accounts[d.account_name] = {}
                   
            accounts[d.account_name][period["key"]] = balance
            
            # Initialize parent account if not already done
            if d.parent_account not in accounts:
                accounts[d.parent_account] = {}
            # Add balance to existing period balance or initialize if does not exist
            accounts[d.parent_account][period["key"]] = accounts[d.parent_account].get(period["key"], 0) + balance
                
            update_parent_accounts_recursive(d.parent_account, accounts, d.account_name,balance, period)
    
    return accounts


# Method to update the parent account of the account passing in, not the account's 
# Means, currently passed in account's values already updated
def update_parent_accounts_recursive(account, accounts, account_name,balance, period):
    
    account_doc = frappe.get_doc('Account',account)
    
    # The parent account intend to be updated is the root account and need not update
    if(account_doc.parent_account == None):
        return;
    
    parent_account = account_doc.parent_account
        
    # Initialize parent account if not already done
    if parent_account not in accounts:
            accounts[parent_account] = {"parent": parent_account}
            
    # Add balance to existing period balance or initialize if does not exist
    accounts[parent_account][period["key"]] = accounts[parent_account].get(period["key"], 0) + balance
    
    update_parent_accounts_recursive(parent_account,accounts,account_name, balance, period)
    
def get_account_balance(account, from_date,to_date):
    
    query="""
    SELECT sum(debit_amount)-sum(credit_amount) as balance from `tabGL Posting` gl where gl.account = %s and posting_date >= %s and posting_date<=%s
    """
    
    data = frappe.db.sql(query,(account,from_date,to_date), as_dict=True)
    if data and data[0]:
        return data[0].balance
    else:
        return 0
    
def re_process_account_data(accounts):
        
    data = []
    for account in accounts:  
        
        parent_account = frappe.db.get_value('Account',account,['parent_account'])
        
        balance = accounts[account]['balance'] if accounts[account]['balance'] else 0
        
        if(balance == 0):
            continue
                
        account_data = {'name':account,'parent_account':parent_account, 'balance':balance}
        
        data.append(account_data)
    
    return data
    