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
        
        print("hitting this")
        print("parent")
        print(parent)
        print("level")
        print(level)
        
        if level < depth:
            children = parent_children_map.get(parent) or []
            for child in children:
                child.indent = level
                filtered_accounts.append(child)
                add_to_list(child.name, level + 1)
                
    add_to_list(None, 0)
    
    print("filtered accounts")
    print(filtered_accounts)
    print("accounts_by_name")
    print(accounts_by_name)
    print("parent_Children_map")
    print(parent_children_map)
    return filtered_accounts, accounts_by_name, parent_children_map

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
