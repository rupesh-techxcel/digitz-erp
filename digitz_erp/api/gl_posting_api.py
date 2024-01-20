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

    account_doc.save()
    
    update_direct_groups_recursive(account_doc.root_type)
    # update_parent_groups(account_doc.parent_account, account_balances)
    
    # update_parent_groups("Indirect Expense", account_balances)
    
    
# def update_parent_groups(parent_account, account_balances):    
    
#     update_parent_and_inner_group_balances(parent_account, account_balances)    
    
#     # account_doc = frappe.get_doc('Account', parent_account)
    
#     # if(account_doc.parent_account != None):
#     #     update_parent_groups(account_doc.parent_account, account_balances)
        

# # This method recursively iterate through the groups and get the balances from the get_account_balance_recursive_for_parent_account method for each group and update it to the account 
# def update_parent_and_inner_group_balances(parent_account, account_balances):
    
#     if(parent_account == None):
#         return
    
#     # if(parent_account in account_balances):
#     #     balance = account_balances[parent_account]
#     # else:
    
#     balance = get_account_balance_recursive_for_parent_account(parent_account,0)

#     account_doc = frappe.get_doc('Account', parent_account)
#     if balance >= 0:
#         account_doc.balance = balance
#         account_doc.balance_dr_cr = 'Dr'
#     else:
#         account_doc.balance = -balance
#         account_doc.balance_dr_cr = 'Cr'
                
#     account_doc.save()        
#     account_balances[parent_account] = balance
        
    
#     inner_groups_query = """
#             SELECT account_name from `tabAccount` a where a.parent_account = %s and a.is_group = 1 
#     """
    
#     data = frappe.db.sql(inner_groups_query, (parent_account,), as_dict=True)
    
#     for d in data:
#        update_parent_and_inner_group_balances(d.name, account_balances)

# # This method get the balance of all ledgers and inner group ledgers with recurssion
# def get_account_balance_recursive_for_parent_account(parent_account,parent_account_balance):
        
#     balance = get_ledger_balances_for_parent_account(parent_account)
    
#     print("parent account ledger balance")    
#     print(parent_account)
#     print(balance)
    
#     inner_groups_query = """
#           SELECT account_name from `tabAccount` a where a.parent_account = %s and a.is_group = 1 
#     """
    
#     data = frappe.db.sql(inner_groups_query, (parent_account,), as_dict=True)
    
#     for d in data:
#         balance = balance + get_account_balance_recursive_for_parent_account(d.name,0)
    
#     parent_account_balance = parent_account_balance + balance
         
#     print("parent account total balance")    
#     print(parent_account_balance)
    
#     return parent_account_balance

# def get_ledger_balances_for_parent_account(parent_account):
    
#     query = """
#         SELECT
#             SUM(gl.debit_amount) - SUM(gl.credit_amount) AS account_balance
#         FROM
#             `tabGL Posting` gl INNER JOIN `tabAccount` a on a.name= gl.account
#         WHERE
#             a.parent_account = %s
#     """
#     data = frappe.db.sql(query, (parent_account,), as_dict=True)
#     balance = data[0].get('account_balance') if data and data[0].get('account_balance') else 0
    
#     return balance


# def update_direct_groups_recursive(root_type):
    
#     # # Update immediate parent_account of all gl postings which is in the the root_type as the param
     
#     group_balances_query = """
#         SELECT
#             a.parent_account,
#             SUM(gl.debit_amount) - SUM(gl.credit_amount) AS group_balance
#         FROM
#             `tabGL Posting` gl
#         INNER JOIN
#             `tabAccount` a ON a.name = gl.account
#         WHERE
#             a.root_type = %s
#         GROUP BY
#             a.parent_account
#     """

#     group_balances = frappe.db.sql(group_balances_query, (root_type,), as_dict=True)
    #  >= 0 THEN %s ELSE -%s END
#     # Update immediate parent accounts with group balances
#     for entry in group_balances:
#         parent_account = entry.get("parent_account")
#         group_balance = entry.get("group_balance")

#     # Determine the balance_dr_cr value based on group_balance
#     balance_dr_cr = "Dr" if group_balance > 0 else "Cr"

#     update_query = """
#         UPDATE
#             `tabAccount`
#         SET
#             balance = CASE WHEN %s >= 0 THEN %s ELSE -%s END,
#             balance_dr_cr = %s
#         WHERE
#             name = %s
#     """

#     # Use abs() to get the absolute value of group_balance
#     frappe.db.sql(update_query, (group_balance, abs(group_balance), abs(group_balance), balance_dr_cr, parent_account))

def update_direct_groups_recursive(root_type):
    # Step 1: Update immediate parent_account groups
    update_direct_groups(root_type)

    # Step 2: Cumulative update to parent accounts recursively
    update_query = """
    UPDATE
        `tabAccount` a
    SET
        balance = COALESCE((
            SELECT
                SUM(b.balance)
            FROM
                `tabAccount` b
            WHERE
                b.parent_account = a.name
        ), 0),
        balance_dr_cr = CASE WHEN COALESCE(SUM(b.balance), 0) >= 0 THEN 'Dr' ELSE 'Cr' END
    WHERE
        a.parent_account IS NULL
        AND a.root_type = %s
        AND a.is_group = 1
    """

    # Execute the update query
    frappe.db.sql(update_query, (root_type,))

def update_direct_groups(root_type):
    # Update immediate parent_account groups
    group_balances_query = """
        SELECT
            a.parent_account,
            SUM(gl.debit_amount) - SUM(gl.credit_amount) AS group_balance
        FROM
            `tabGL Posting` gl
        INNER JOIN
            `tabAccount` a ON a.name = gl.account
        WHERE
            a.root_type = %s
        GROUP BY
            a.parent_account
    """

    group_balances = frappe.db.sql(group_balances_query, (root_type,), as_dict=True)

    # Update immediate parent accounts with group balances
    for entry in group_balances:
        parent_account = entry.get("parent_account")
        group_balance = entry.get("group_balance")

        # Determine the balance_dr_cr value based on group_balance
        balance_dr_cr = "Dr" if group_balance > 0 else "Cr"

        update_query = """
            UPDATE
                `tabAccount`
            SET
                balance = %s,
                balance_dr_cr = %s
            WHERE
                name = %s
                AND root_type = %s
        """

        # Use abs() to get the absolute value of group_balance
        frappe.db.sql(update_query, (abs(group_balance), balance_dr_cr, parent_account, root_type))
