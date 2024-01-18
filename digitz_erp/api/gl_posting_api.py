import frappe
from frappe.utils import *

@frappe.whitelist()
def update_account_balance(account):
    
    query = """
        SELECT
            SUM(debit_amount) - SUM(credit_amount) AS account_balance
        FROM
            `tabGL Posting`
        WHERE
            account = %s
    """
    data = frappe.db.sql(query, (account,), as_dict=True)
    account_balance = data[0].get('account_balance') if data and data[0].get('account_balance') else 0
    account_doc = frappe.get_doc('Account', account)
    if account_balance >= 0:
        account_doc.balance = account_balance
        account_doc.balance_dr_cr = 'Dr'
    else:
        account_doc.balance = -account_balance
        account_doc.balance_dr_cr = 'Cr'
        print(account_balance)
    account_doc.save()
    
    print("here")
    
    update_parent_and_inner_group_balances(account_doc.parent_account)
    
    return account_balance

def get_ledger_balances_for_parent_account(parent_account):
    
    query = """
        SELECT
            SUM(gl.debit_amount) - SUM(gl.credit_amount) AS account_balance
        FROM
            `tabGL Posting` gl INNER JOIN `tabAccount` a on a.name= gl.account
        WHERE
            a.parent_account = %s
    """
    data = frappe.db.sql(query, (parent_account,), as_dict=True)
    balance = data[0].get('account_balance') if data and data[0].get('account_balance') else 0
    
    return balance

# This method get the balance of all ledgers and inner group ledgers with recurssion
def get_account_balance_recursive_for_parent_account(parent_account):
    
    balance = get_ledger_balances_for_parent_account(parent_account)
    
    inner_groups_query = """
            SELECT account_name from `tabAccount` a where a.parent_account = %s and a.is_group = 1 
    """
    
    data = frappe.db.sql(inner_groups_query, (parent_account,), as_dict=True)
    
    for d in data:
         balance = balance + get_account_balance_recursive_for_parent_account(d.name)
         
    return balance
        
# This method recursively iterate through the groups and get the balances from the get_account_balance_recursive_for_parent_account method for each group and update it to the account 
def update_parent_and_inner_group_balances(parent_account):
    
    if(parent_account == None):
        return
    
    print("parent_account")
    print(parent_account)
    
    balance = get_account_balance_recursive_for_parent_account(parent_account)
    
    account_doc = frappe.get_doc('Account', parent_account)
    if balance >= 0:
        account_doc.balance = balance
        account_doc.balance_dr_cr = 'Dr'
    else:
        account_doc.balance = -balance
        account_doc.balance_dr_cr = 'Cr'
                
    account_doc.save()
    
    inner_groups_query = """
            SELECT account_name from `tabAccount` a where a.parent_account = %s and a.is_group = 1 
    """
    
    data = frappe.db.sql(inner_groups_query, (parent_account,), as_dict=True)
    
    for d in data:
       update_parent_and_inner_group_balances(d.name)
         