# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
import functools
from frappe import _
from six import itervalues

def filter_accounts(accounts, depth=20):
    parent_children_map = {}
    accounts_by_name = {}
    
    for d in accounts:
        
        accounts_by_name[d.name] = d
        parent_children_map.setdefault(d.parent_account or None, []).append(d)
        
    filtered_accounts = []    

    def add_to_list(parent, level):
        
        if level < depth:
            children = parent_children_map.get(parent) or []
            for child in children:
                child.indent = level
                filtered_accounts.append(child)
                add_to_list(child.name, level + 1)
                
    add_to_list(None, 0)    
   
    return filtered_accounts, accounts_by_name, parent_children_map

def sort_accounts(accounts):
    
    sort_accounts=[]
    
    for account in accounts:
        if account["name"] == "Accounts":
            sort_accounts.append(account)
            print("here 1")
            break
        
    print("here 0")
    print(accounts)
    
    def add_to_parent_account(account, indent):
        print("here 2")
        for account_in_accounts in accounts:
            print("here 3")
            if account_in_accounts["parent_account"] == account:
                print("here 4")
                account_in_accounts["added"] = 1
                account_in_accounts["indent"] = indent + 1
                sort_accounts.append(account_in_accounts)
                add_to_parent_account(account_in_accounts["name"],indent+1)
                print(indent)
    
    add_to_parent_account("Accounts",0) 
    
    return sort_accounts

@frappe.whitelist()
def get_posting_years():
    years = []
    data = frappe.db.sql("""
        SELECT
            DISTINCT YEAR(posting_date) AS posting_year
        FROM
            `tabGL Posting`
        ORDER BY
            posting_date
        """, as_dict=True)
    for d in data:
        years.append(str(d.get('posting_year')))
    return years
