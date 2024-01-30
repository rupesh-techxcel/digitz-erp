import frappe
from frappe.utils import *

@frappe.whitelist()
def get_accounts_data(from_date,to_date):
   
    query = """
            SELECT parent_account, account_name, root_type
            FROM `tabAccount`
            WHERE is_group = 0 AND (root_type='Asset' OR root_type='Liability')
            ORDER BY FIELD(root_type, 'Assets', 'Liability')
            """
    data = frappe.db.sql(query, as_dict=True)
      
    accounts = {}
    
    for d in data:
               
        balance = get_account_balance(d.account_name,from_date,to_date)
                
        if(not balance):
            balance = 0
            
        if(d.root_type == "Liability"):
            balance = balance * -1
            
        accounts[d.account_name] = {
            "balance": balance            
        }
        
        if(d.parent_account in accounts):
            accounts[d.parent_account] = {"balance":accounts[d.parent_account]["balance"] + balance}
        else:
            accounts[d.parent_account] = {"balance":balance}
        
        update_parent_accounts_recursive(d.parent_account,accounts,d.account_name)
        
    return re_process_account_data(accounts)

# Method to update the parent account of the account passing in, not the account's 
# Means, currently passed in account's values already updated
def update_parent_accounts_recursive(account, accounts, account_name):
    account_doc = frappe.get_doc('Account',account)
    
    # The parent account intend to be updated is the root account and need not update
    if(account_doc.parent_account == None):
        return;
    
    parent_account = account_doc.parent_account
    
    if parent_account in accounts:
        accounts[parent_account] = {
            "balance": accounts[parent_account]['balance'] + accounts[account_name]['balance']}
    else:   
        accounts[parent_account] = {"balance": accounts[account_name]['balance'] }
    
    update_parent_accounts_recursive(parent_account,accounts,account_name)
    
    
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