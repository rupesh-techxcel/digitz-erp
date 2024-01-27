import frappe
from frappe.utils import *

@frappe.whitelist()
def get_accounts_data(from_date,to_date,for_gp):
    
    query = ""
    if for_gp:
        query = """
                SELECT parent_account,account_name,root_type from `tabAccount` where is_group = 0 and (root_type='Expense' or root_type='Income') and include_in_gross_profit=1
                """
    else:
         query = """
                SELECT parent_account,account_name,root_type from `tabAccount` where is_group = 0 and (root_type='Expense' or root_type='Income') and include_in_gross_profit=0
                """
        
    data = frappe.db.sql(query, as_dict=True)
    print("data")
    print(data)
    
    accounts = {}
    
    for d in data:
        balance = get_account_balance(d.account,from_date,to_date)
        
        if(not balance):
            balance = 0
            
        if(d.root_type == "Income"):
            balance = balance * -1
            
        accounts[d.account_name] = {
            "balance": balance
        }
        
        update_parent_accounts_recursive(d.parent_account,accounts,d.account_name)
        
    print("final accounts")
    print(accounts)
    
    data = []
    for key in accounts:
        
        print("account")
        print(key)
    
        d = {"account": key, "balance": accounts[key]["balance"]}    
        data.append(d)
    
    print(data)
            
def update_parent_accounts_recursive(account, accounts, account_name):
    account_doc = frappe.get_doc('Account',account)
    if(account_doc.parent_account == 'Accounts'):
        return;
    parent_account = account_doc.parent_account
    
    if parent_account in accounts:
        accounts[parent_account] = {
            "balance": accounts[parent_account] + accounts[account_name]['balance']}
    else:   
        accounts[parent_account] = {"balance": 100}
        
    update_parent_accounts_recursive(parent_account,accounts,account_name)
    
           
    
def get_account_balance(account, from_date,to_date):
    
    query="""
    SELECT sum(debit_amount)-sum(credit_amount) as opening_balance from `tabGL Posting` gl where gl.account = %s and posting_date >= %s and posting_date<=%s
    """
    
    data = frappe.db.sql(query,(account,from_date,to_date), as_dict=True)
    if data and data[0]:
        return data[0].opening_balance
    else:
        return 0