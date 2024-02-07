import frappe
from frappe.utils import *

@frappe.whitelist()
def update_accounts_for_doc_type(doc_type, name):
    
    query = """
            SELECT distinct account from `tabGL Posting` gp where gp.voucher_type=%s and gp.voucher_no=%s
            """
    account_list = frappe.db.sql(query, (doc_type,name),as_dict=True)
    print("account_list")
    print(account_list)
    
    for account in account_list:
        update_account_balance(account.account)
        
def delete_gl_postings_for_cancel_doc_type(doc_type,name):
    
    query = """
        SELECT distinct account from `tabGL Posting` gp where gp.voucher_type=%s and gp.name=%s
        """
    account_list = frappe.db.sql(query, (doc_type,name),as_dict=True)
    
    frappe.db.delete("GL Posting",
                {"voucher_type": doc_type,
                  "voucher_no":name
                })
        
    for account in account_list:
        update_account_balance(account.account)

@frappe.whitelist()
def update_all_account_balances():
    
    query = """
            SELECT account_name from `tabAccount` where is_group = 0
            """
    data = frappe.db.sql(query, as_dict=True)
    
    for d in data:
        update_account_balance(d.account_name)
        
    update_all_parent_accounts()

@frappe.whitelist()    
def update_all_parent_accounts():
    print("Asset data updation")
    update_all_parent_accounts_for_the_root_type("Asset")
    print("Liability data updation")
    update_all_parent_accounts_for_the_root_type("Liability")
    print("Income data updation")
    update_all_parent_accounts_for_the_root_type("Income")
    print("Expense data updation")
    update_all_parent_accounts_for_the_root_type("Expense")
        
@frappe.whitelist()
def update_account_balance(account, update_parent_accounts=True):
    print("")
    print("")
    print("")
    
    print("account")
    print(account)
    
    if(account == "Accounts"):
        return
    
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

    account_doc.save()
    
    # if account_doc.root_type == None:
    #     frappe.throw("Root type not found for the account {}".format(account_doc.name))
        
    if update_parent_accounts:
        update_all_parent_accounts_for_the_root_type(account_doc.root_type)

# With this method all direct account groups will be upadated based on the gl_posting under the root_type. 
# And then will update each parent groups upto root
def update_all_parent_accounts_for_the_root_type(root_type):
    
    # Reset all parent_groups to zero
    query = """
    SELECT name from `tabAccount` where root_type= %s and is_group = 1    
    """    
    data = frappe.db.sql(query, (root_type,), as_dict = 1)
    
    for d in data:
        account = frappe.get_doc('Account',d.name)
        account.balance = 0
        account.balance_dr_cr = None
        account.save()
    
    # Query to get gl_postings balances for the account and  direct parent_account
    query = """
    SELECT
        a.parent_account,
        gp.account,
        SUM(debit_amount) - SUM(credit_amount) AS account_balance
    FROM
        `tabGL Posting` gp
    INNER JOIN
        `tabAccount` a ON gp.account = a.name
    WHERE
        a.root_type = '{root_type}'
    GROUP BY
        a.parent_account, gp.account
    HAVING
        SUM(debit_amount) <> SUM(credit_amount)
    """.format(root_type=root_type)

    data = frappe.db.sql(query, as_dict=True)
          
    direct_parent_accounts = {}
    parent_accounts = {}
    
    print("parent accounts and accounts")
    
    # Cummilate all the values of the direct_parent_accounts dictionary
    for d in data: 
        
        if d.parent_account not in direct_parent_accounts:
            direct_parent_accounts[d.parent_account] = d.account_balance
        else:
            direct_parent_accounts[d.parent_account] += d.account_balance
        
   
    #  Update corresponding direct_parent_account values to the table
    for key in direct_parent_accounts:
              
        account = frappe.get_doc('Account', key)
        account.balance = abs(direct_parent_accounts[key])
        
        if(direct_parent_accounts[key] == 0):    
            account.balance_dr_cr  = None
        else:    
            account.balance_dr_cr = 'Dr' if direct_parent_accounts[key] > 0 else 'Cr'
            
        account.save()
        
        # Save the direct_parent_account and balance to the generic parent_accounts dictionary
        parent_accounts[key] = direct_parent_accounts[key]
        update_parent_account_to_root_recursive(key,parent_accounts, parent_accounts[key])

    # After recursively update the balances to the parent_accounts dictionary save them to the database
    for key in parent_accounts:
        account = frappe.get_doc('Account', key)
        if(account):
            account.balance = abs(parent_accounts[key])
            
            if(parent_accounts[key] == 0):    
                account.balance_dr_cr  = None
            else:    
                account.balance_dr_cr = 'Dr' if parent_accounts[key] > 0 else 'Cr'
                
            account.save()
    
def update_parent_account_to_root_recursive(account, parent_accounts, account_balance):
      
    query="""
        SELECT parent_account from `tabAccount` where name=%s
        """
    data = frappe.db.sql(query, (account,), as_dict=True)
        
    # Need not update for root account
    if(data[0].parent_account == "Accounts"):
        return
      
    # Simply take the parent_account passing in and its balance to cummilate to its parent account    
    if(data[0].parent_account not in parent_accounts):
        parent_accounts[data[0].parent_account] = account_balance
    else:
        parent_accounts[data[0].parent_account] += account_balance
    
    update_parent_account_to_root_recursive(data[0].parent_account, parent_accounts, account_balance)

@frappe.whitelist()
def get_account_balances_for_period_closing(to_date):
    
    query = """Select a.name,sum(debit_amount)- sum(credit_amount) as balance from `tabGL Posting` gp inner join `tabAccount` a on a.name = gp.account where posting_date<%s and (a.root_type='Expense' or a.root_type='Income') group by a.name """
    
    data = frappe.db.sql(query,(to_date),as_dict= True)
    print("get_account_balances_for_period_closing")
    print(data)
    return data
    