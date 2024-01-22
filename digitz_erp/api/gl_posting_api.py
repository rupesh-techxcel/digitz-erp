import frappe
from frappe.utils import *

@frappe.whitelist()
def update_account_balance(account):
    
    print("account")
    print(account)
    
    query = """
        SELECT
            SUM(debit_amount) - SUM(credit_amount) AS account_balance
        FROM
            `tabGL Posting`
        WHERE
            account = %s
    """
    data = frappe.db.sql(query, (account,), as_dict=True)
    
    print("data")
    print(data)
    
    account_balance = data[0].get('account_balance') if data and data[0].get('account_balance') else 0
    account_doc = frappe.get_doc('Account', account)
    
    print("account_doc")
    print(account_doc)   
    print(account_doc.account_name)
    print(account_doc.balance)
    print(account_doc.balance_dr_cr)
     
    if account_balance >= 0:
        account_doc.balance = account_balance
        account_doc.balance_dr_cr = 'Dr'
    else:
        account_doc.balance = -account_balance
        account_doc.balance_dr_cr = 'Cr'

    account_doc.save()
    
    print("account_balance")
    print(account_balance)
    
    print("account_doc")
    print(account_doc)
    
    print("account_doc.account_name")
    print(account_doc.account_name)
    print("account_doc.balance")
    print(account_doc.balance)
    print("account_doc.balance_dr_cr")
    print(account_doc.balance_dr_cr)
    
    if account_doc.root_type == None:
        frappe.throw("Root type not found for the account {}".format(account_doc.name))
    
    update_all_direct_parent_accounts_from_gl_postings_for_the_root_type(account_doc.root_type)

# With this method all direct account groups will be upadated based on the gl_posting under the root_type. 
# And then will update each parent groups upto root
def update_all_direct_parent_accounts_from_gl_postings_for_the_root_type(root_type):
    
    # Reset all parent_groups to zero
    query = """
    UPDATE `tabAccount` set balance = 0 where root_type= %s and is_group = 1    
    """    
    frappe.db.sql(query, (root_type,))
    
    query = """
    SELECT
    a.parent_account,
    SUM(debit_amount) - SUM(credit_amount) AS account_balance
    FROM
    `tabGL Posting` gp
    INNER JOIN `tabAccount` a on gp.account = a.name
    WHERE
    a.root_type = '{root_type}'
    GROUP BY a.parent_account
    """.format(root_type=root_type)
    
    print("query")
    print(query)
    
    data = frappe.db.sql(query , as_dict=True)   
    print("data")
    print(data)
    
    for d in data:
        print(d.parent_account)
        account = frappe.get_doc('Account', d.parent_account)
        if(account):
            account.balance = 0    
            account.save()
            print("account on update")
            print(account)
            print(account.balance)
    
    
    for d in data:
        print(d.parent_account)
        account = frappe.get_doc('Account', d.parent_account)
        if(account):            
            print("account after update")
            print(account)
            print(account.balance)
            
    data = frappe.db.sql(query , as_dict=True)   
    print("data 2")
    print(data)
        
    parent_accounts = {}
    
    for d in data:
        # Note that each parent account getting here may or may not have child parent accounts
        account = frappe.get_doc('Account', d.parent_account)
        account.balance= abs(d.account_balance)
        if account.balance == 0:
            account.balance_dr_cr = None
        else:
            account.balance_dr_cr = "Dr" if account.balance > 0 else "Cr"
        
        account.save()
        
        # Here also we check the value exists in the dictionary because for parent_accounts which 
        # has child parent group already exists the parent_account may be already exists in the dictionary
        if d.parent_account not in parent_accounts:
            parent_accounts[d.parent_account] = d.account_balance
        else:
            parent_accounts[d.parent_account] += d.account_balance
        
        # Direct parent accounts are already updated in this loop but still adds to the dictionary
        # because those parent accounts may also contain group which can have accounts with values
        # so the value cummilation needs to occur again.
        
        update_parent_account_to_root_recursive(d.parent_account, parent_accounts)
        
    for key in parent_accounts:
        
        account = frappe.get_doc('Account', key)
        account.balance = abs(parent_accounts[key])
        if account.balance == 0:
            account.balance_dr_cr = None
        else:
            account.balance_dr_cr = "Dr" if parent_accounts[key] > 0 else "Cr"
        
        account.save()
    
def update_parent_account_to_root_recursive(parent_account, parent_accounts):
   
    # Note that we take only parent accounts and not considering the child account groups of each
    # parent account since from the calling method we consider all the gl_postings and start with
    # the direct parent account of each account in the gl_postings. So only backward (to the top) 
    # recursion is required. Because it considre all the accounts in gl_postings the balances will 
    # be correct
    query="""
        SELECT parent_account from `tabAccount` where name=%s
        """
    data = frappe.db.sql(query, (parent_account,), as_dict=True)
    
    data[0].parent_account
    
    # When it reached the root need to go further.
    if(data == None or data[0].parent_account ==None):
        return
    
    # Simply take the parent_account passing in and its balance to cummilate to its parent account    
    if(data[0].parent_account not in parent_accounts):
        parent_accounts[data[0].parent_account] = parent_accounts[parent_account]
    else:
        parent_accounts[data[0].parent_account] += parent_accounts[parent_account]
        
    update_parent_account_to_root_recursive(data[0].parent_account, parent_accounts)

    

    
    
    
    
    
      