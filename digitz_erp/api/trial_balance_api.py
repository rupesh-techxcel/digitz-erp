import frappe
from frappe.utils import *

@frappe.whitelist()
def get_accounts_data(from_date,to_date, root_type,project=None):
    
    query = """
            SELECT parent_account,account_name from `tabAccount` where is_group = 0 and root_type=%s
            """
    data = frappe.db.sql(query,(root_type), as_dict=True)
    #print("data")
    #print(data)
    
    accounts = {}
    
    for d in data:      
          
        opening_balance = get_opening_balance(d.account_name, from_date)
        
        if not opening_balance:
            opening_balance = 0

        opening_balance_debit = max(0, opening_balance)
        opening_balance_credit = abs(min(0, opening_balance))

        transaction_debit = get_transaction_debit(d.account_name, from_date,to_date)
        
        if not transaction_debit:
            transaction_debit = 0
        
        transaction_credit = get_transaction_credit(d.account_name, from_date,to_date)
        
        if not transaction_credit:
            transaction_credit = 0

        closing_balance = opening_balance + transaction_debit - transaction_credit

        if not closing_balance:
            closing_balance = 0
        closing_balance_debit = max(0, closing_balance )
        closing_balance_credit = abs(min(0, closing_balance))

        accounts[d.account_name] = {
            'opening_debit': opening_balance_debit,
            'opening_credit': opening_balance_credit,
            'debit': transaction_debit,
            'credit': transaction_credit,
            'closing_debit': closing_balance_debit,
            'closing_credit': closing_balance_credit
        }

        if d.parent_account in accounts:
            accounts[d.parent_account] = {
                'opening_debit': accounts[d.parent_account]['opening_debit'] + opening_balance_debit,
                'opening_credit': accounts[d.parent_account]['opening_credit'] + opening_balance_credit,
                'debit': accounts[d.parent_account]['debit'] + transaction_debit,
                'credit': accounts[d.parent_account]['credit'] + transaction_credit,
                'closing_debit': accounts[d.parent_account]['closing_debit'] + closing_balance_debit,
                'closing_credit': accounts[d.parent_account]['closing_credit'] + closing_balance_credit
            }
        else:
            accounts[d.parent_account] = {
                'opening_debit': opening_balance_debit,
                'opening_credit': opening_balance_credit,
                'debit': transaction_debit,
                'credit': transaction_credit,
                'closing_debit': closing_balance_debit,
                'closing_credit': closing_balance_credit
            }
        # opening
        if(accounts[d.parent_account]['opening_debit'] == accounts[d.parent_account]['opening_credit']):
            accounts[d.parent_account]['opening_debit'] = 0
            accounts[d.parent_account]['opening_credit'] = 0
        elif(accounts[d.parent_account]['opening_debit']> accounts[d.parent_account]['opening_credit']):
            accounts[d.parent_account]['opening_debit'] = accounts[d.parent_account]['opening_debit'] - accounts[d.parent_account]['opening_credit'] 
            accounts[d.parent_account]['opening_credit'] = 0
            
        elif(accounts[d.parent_account]['opening_debit']< accounts[d.parent_account]['opening_credit']):
            accounts[d.parent_account]['opening_credit'] = accounts[d.parent_account]['opening_credit'] - accounts[d.parent_account]['opening_debit'] 
            accounts[d.parent_account]['opening_debit'] = 0
        
         # closing
        if(accounts[d.parent_account]['closing_debit'] == accounts[d.parent_account]['closing_credit']):
            accounts[d.parent_account]['closing_debit'] = 0
            accounts[d.parent_account]['closing_credit'] = 0
        elif(accounts[d.parent_account]['closing_debit']> accounts[d.parent_account]['closing_credit']):
            accounts[d.parent_account]['closing_debit'] = accounts[d.parent_account]['closing_debit'] - accounts[d.parent_account]['closing_credit'] 
            accounts[d.parent_account]['closing_credit'] = 0
            
        elif(accounts[d.parent_account]['closing_debit']< accounts[d.parent_account]['closing_credit']):
            accounts[d.parent_account]['closing_credit'] = accounts[d.parent_account]['closing_credit'] - accounts[d.parent_account]['closing_debit'] 
            accounts[d.parent_account]['closing_debit'] = 0
        
        update_parent_accounts_recursive(d.parent_account,accounts,d.account_name)
    
    return re_process_account_data(accounts)

def re_process_account_data(accounts):
    
    data = []
    for account in accounts:  
        
        parent_account = frappe.db.get_value('Account',account,['parent_account'])
        
        #print(accounts[account]['opening_debit'])     
        account_data = {'name':account,'parent_account':parent_account, 'opening_debit':accounts[account]['opening_debit'], 'opening_credit':accounts[account]['opening_credit'], 'debit':accounts[account]['debit'], 'credit':accounts[account]['credit'],'closing_debit': accounts[account]['closing_debit'],'closing_credit':accounts[account]['closing_credit']}
        
        data.append(account_data)
     
    return data

# Method to update the parent account of the account passing in, not the account's 
# Means, currently passed in account's values already updated
def update_parent_accounts_recursive(account, accounts, account_name):
    
    account_doc = frappe.get_doc('Account',account)
    
    # The parent account intend to be updated is the root account and need not update
    if(account_doc.parent_account == 'Accounts'):
        return;
    
    parent_account = account_doc.parent_account
    
    if parent_account in accounts:
            accounts[parent_account] = {
                'opening_debit': accounts[parent_account]['opening_debit'] + accounts[account_name]['opening_debit'],
                'opening_credit': accounts[parent_account]['opening_credit'] + accounts[account_name]['opening_credit'],
                'debit': accounts[parent_account]['debit'] + accounts[account_name]['debit'],
                'credit': accounts[parent_account]['credit'] + accounts[account_name]['credit'],
                'closing_debit': accounts[parent_account]['closing_debit'] + accounts[account_name]['closing_debit'],
                'closing_credit': accounts[parent_account]['closing_credit'] + accounts[account_name]['closing_credit']            }
    else:
            accounts[parent_account] = {
                'opening_debit': accounts[account_name]['opening_debit'],
                'opening_credit': accounts[account_name]['opening_credit'],
                'debit': accounts[account_name]['debit'],
                'credit': accounts[account_name]['credit'],
                'closing_debit': accounts[account_name]['closing_debit'],
                'closing_credit': accounts[account_name]['closing_credit'] }
    
    # Opening balances 
    if(accounts[parent_account]['opening_debit']== accounts[parent_account]['opening_credit']):
        accounts[parent_account]['opening_debit'] = 0
        accounts[parent_account]['opening_credit'] = 0
    
    elif (accounts[parent_account]['opening_debit']> accounts[parent_account]['opening_credit'] ):
        accounts[parent_account]['opening_debit'] = accounts[parent_account]['opening_debit'] - accounts[parent_account]['opening_credit']
        accounts[parent_account]['opening_credit'] = 0
        
    elif (accounts[parent_account]['opening_debit']< accounts[parent_account]['opening_credit'] ):
        accounts[parent_account]['opening_credit'] = accounts[parent_account]['opening_credit'] - accounts[parent_account]['opening_debit']
        accounts[parent_account]['opening_debit'] = 0
        
    # Closing balances 
    if(accounts[parent_account]['closing_debit']== accounts[parent_account]['closing_credit']):
        accounts[parent_account]['closing_debit'] = 0
        accounts[parent_account]['closing_credit'] = 0
    
    elif (accounts[parent_account]['closing_debit']> accounts[parent_account]['closing_credit'] ):
        accounts[parent_account]['closing_debit'] = accounts[parent_account]['closing_debit'] - accounts[parent_account]['closing_credit']
        accounts[parent_account]['closing_credit'] = 0
        
    elif (accounts[parent_account]['closing_debit']< accounts[parent_account]['closing_credit'] ):
        accounts[parent_account]['closing_credit'] = accounts[parent_account]['closing_credit'] - accounts[parent_account]['closing_debit']
        accounts[parent_account]['closing_debit'] = 0
            
    update_parent_accounts_recursive(parent_account,accounts,account_name)
        
def get_opening_balance(account, from_date, project=None):
    # Initialize query and values
    query = """
        SELECT 
            SUM(debit_amount) - SUM(credit_amount) AS opening_balance 
        FROM 
            `tabGL Posting` gl 
        WHERE 
            gl.account = %s AND gl.posting_date < %s
    """
    values = [account, from_date]

    # Add the optional project filter
    if project:  # Check if the project filter is provided
        query += " AND gl.project = %s"
        values.append(project)

    # Execute the query with parameterized values
    data = frappe.db.sql(query, values, as_dict=True)

    # Return the opening balance or 0 if no data is found
    if data and data[0]:
        return data[0].get('opening_balance', 0)
    else:
        return 0

def get_transaction_debit(account, from_date, to_date, project=None):
    # Base query
    query = """
        SELECT 
            SUM(debit_amount) AS debit_amount 
        FROM 
            `tabGL Posting` gl 
        WHERE 
            gl.account = %s 
            AND gl.posting_date >= %s 
            AND gl.posting_date <= %s
    """

    # Parameters for the query
    values = [account, from_date, to_date]

    # Add the optional project filter
    if project:  # Check if a project filter is provided
        query += " AND gl.project = %s"
        values.append(project)

    # Execute the query with parameterized values
    data = frappe.db.sql(query, values, as_dict=True)

    # Return the debit amount or 0 if no data is found
    if data and data[0]:
        return data[0].get('debit_amount', 0)
    else:
        return 0


def get_transaction_credit(account, from_date, to_date, project=None):
    # Base query
    query = """
        SELECT 
            SUM(credit_amount) AS credit_amount 
        FROM 
            `tabGL Posting` gl 
        WHERE 
            gl.account = %s 
            AND posting_date >= %s 
            AND posting_date <= %s
    """

    # Parameters for the query
    values = [account, from_date, to_date]

    # Add the optional project filter
    if project:  # Check if a project filter is provided
        query += " AND gl.project = %s"
        values.append(project)

    # Execute the query with parameterized values
    data = frappe.db.sql(query, values, as_dict=True)
    
    # Return the credit amount or 0 if no data is found
    if data and data[0]:
        return data[0].get('credit_amount', 0)
    else:
        return 0

    
