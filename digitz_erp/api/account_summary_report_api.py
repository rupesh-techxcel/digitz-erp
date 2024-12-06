import frappe
from frappe.utils import *

@frappe.whitelist()
def get_accounts_data(from_date,to_date, root_type, account_ledger,account_group):
    
    query = """
            SELECT parent_account,account_name from `tabAccount` where is_group = 0 and root_type=%s
            """
    data = frappe.db.sql(query,(root_type), as_dict=True)
    
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
        
    parent_accounts = []
    
    if account_ledger:
        
        parent_accounts.append(account_ledger)
        
        def get_parent_accounts(account):
            
            #print(account)
            
            if account == "Accounts":
                return
            
            parent_account = frappe.get_value("Account", account,['parent_account'])
            
            parent_accounts.append(parent_account)
            
            get_parent_accounts(parent_account)
        
        get_parent_accounts(account_ledger)
        
    if account_group:
        
        def get_child_accounts_and_groups(parent_account):
        
        # Query to fetch accounts under the specified parent account
            accounts_in_group = frappe.db.sql("""SELECT name,is_group FROM `tabAccount` WHERE parent_account=%s""", (parent_account,), as_dict=True)
            
            # Appending each account to the parent_accounts list
            for account in accounts_in_group:            
                parent_accounts.append(account.name)
                if(account.is_group):
                    get_child_accounts_and_groups(account.name)
                    
        parent_accounts.append(account_group)
        get_child_accounts_and_groups(account_group)
        
        def get_parent_accounts_to_root_for_group(account):   
            
            parent_account = frappe.get_value("Account", account,['parent_account'])
            
            if parent_account == None:
                return
            
            parent_accounts.append(parent_account)
            
            get_parent_accounts_to_root_for_group(parent_account)
        
        get_parent_accounts_to_root_for_group(account_group)
    
    return re_process_account_data(accounts, parent_accounts)

def re_process_account_data(accounts,parent_accounts):
    
    data = []
    
    for account in accounts:  
        
        if parent_accounts !=[] and account not in parent_accounts:
            
            continue
        
        parent_account = frappe.db.get_value('Account',account,['parent_account'])
        
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
        
def get_opening_balance(account, from_date):
    
    query="""
    SELECT sum(debit_amount)-sum(credit_amount) as opening_balance from `tabGL Posting` gl where gl.account = %s and posting_date < %s
    """
    
    data = frappe.db.sql(query,(account,from_date), as_dict=True)
    if data and data[0]:
        return data[0].opening_balance
    else:
        return 0

def get_transaction_debit(account, from_date, to_date):
    
    query="""
    SELECT sum(debit_amount) as debit_amount from `tabGL Posting` gl where gl.account = '{account}' and posting_date >= '{from_date}' and posting_date<='{to_date}'
    """.format(account=account,from_date=from_date, to_date=to_date)
    
    data = frappe.db.sql(query, as_dict=True)
    if data and data[0]:
        return data[0].debit_amount
    else:
        return 0

def get_transaction_credit(account, from_date, to_date):
    
    query="""
    SELECT sum(credit_amount) as credit_amount from `tabGL Posting` gl where gl.account = '{account}' and posting_date >= '{from_date}' and posting_date<='{to_date}'
    """.format(account=account,from_date=from_date, to_date=to_date)
    
    data = frappe.db.sql(query, as_dict=True)
    if data and data[0]:
        return data[0].credit_amount
    else:
        return 0
    
