# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from digitz_erp.accounts.report.digitz_erp import filter_accounts,sort_accounts
from digitz_erp.api.trial_balance_api import get_accounts_data

value_fields = (
	"opening_debit",
	"opening_credit",
	"debit",
	"credit",
	"closing_debit",
	"closing_credit",
)

def execute(filters=None):
    
	columns = get_columns()
	data_asset = get_data_for_root_type(filters,"Asset")
	data_liability = get_data_for_root_type(filters,"Liability")
	data_income = get_data_for_root_type(filters,"Income")
	data_expense = get_data_for_root_type(filters,"Expense")
	
	data =[]
	if data_asset:
		data.extend(data_asset)
	
	if data_liability:
		data.extend(data_liability)
  
	if data_income:
		data.extend(data_income)
  
	if data_expense:
		data.extend(data_expense)
	
	return columns,data

def fetch_account_hierarchy(root_types=None):
    # Determine root_types filter
    root_type_filter = root_types if root_types else ['Account', 'Liability', 'Income', 'Expense']

    # Fetch the specified root account with additional root_type filtering
    root_accounts = frappe.get_all('Account',
                                   filters={
                                       'parent_account': None,
                                       'root_type': ['in', root_type_filter]
                                   },
                                   fields=['name', 'parent_account', 'balance'])

    if not root_accounts:
        return "No root accounts found matching the specified types."

    # Initialize the hierarchy dictionary
    hierarchy = {}
    for root in root_accounts:
        hierarchy[root.name] = {
            'balance': root.balance,
            'children': {}
        }

    # Function to fetch child accounts recursively
    def add_children(parent_name, parent_dict):
        children = frappe.get_all('Account',
                                  filters={'parent_account': parent_name},
                                  fields=['name', 'parent_account', 'balance', 'is_group', 'include_in_gross_profit'])
        for child in children:
            # Only add groups or specific non-group accounts
            if child['is_group'] == 1 or (child['is_group'] == 0 and child['include_in_gross_profit'] == 0):
                parent_dict[child['name']] = {'balance': child['balance'], 'children': {}}
                add_children(child['name'], parent_dict[child['name']])  # Recurse to add further children

    # Start the recursion for each root account
    for root in root_accounts:
        add_children(root.name, hierarchy[root.name]['children'])

    return hierarchy
 
def get_data_for_root_type(filters, root_type):
     # data = get_data(filters)
	accounts = get_accounts_data(filters.get('from_date'), filters.get('to_date'),root_type)
	 
	accounts_from_table = frappe.db.sql(
    """
		SELECT
			`name`,
			`parent_account`,
			`lft`,
			`rgt`,
			0 AS `opening_debit`,
			0 AS `opening_credit`,
			0 AS `debit`, 
			0 AS `credit`,
			0 AS `closing_debit`,
			0 AS `closing_credit`
		FROM
			`tabAccount`
		WHERE
			`root_type` in (%s) OR `root_type` IS NULL
		ORDER BY
			`lft`
		""",(root_type), as_dict=True
	)
	
	for account in accounts_from_table:
		for account2 in accounts:
			if(account['name'] == account2['name']):
				account['opening_debit'] = account2['opening_debit']
				account['opening_credit'] = account2['opening_credit']
				account['debit'] = account2['debit']
				account['credit'] = account2['credit']
				account['closing_debit'] = account2['closing_debit']
				account['closing_credit'] = account2['closing_credit']
    
	# Remove entries with both opening_debit and opening_credit equal to 0
	# accounts_from_table = [account for account in accounts_from_table if account['opening_debit'] != 0 or account['opening_credit'] != 0 or  account['debit'] !=0 or account['credit'] !=0 or  account['closing_debit'] !=0 or  account['closing_credit'] !=0]
 
	accounts_from_table = [account for account in accounts_from_table if (any(account[field] != 0 for field in value_fields) or any(child[field] != 0 for child in accounts_from_table if child['parent_account'] == account['name'] for field in value_fields) )]
	
	condition_to_remove = {'name': 'Accounts'}
 
	accounts_from_table = [account for account in accounts_from_table if account != condition_to_remove]
 
	print("accounts_from_table")
	print(accounts_from_table)	
 
	# filter_accounts(accounts_from_table)
	accounts_from_table  = sort_accounts(accounts_from_table)
  
	data =[]
	for account in accounts_from_table:
     
		if account.name == "Accounts":
			continue
		else:
			data.append(account)
	

	return data

def prepare_data(accounts, filters, total_row, parent_children_map, accounts_by_name):
	data = []
	
	for account in accounts:
     
		data.append(account)
  
	return data

def get_columns():
	return [
		{
			"fieldname": "name",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 355,
		},
		{
			"fieldname": "opening_debit",
			"label": _("Opening (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "opening_credit",
			"label": _("Opening (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "debit",
			"label": _("Debit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 155,
		},
		{
			"fieldname": "credit",
			"label": _("Credit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": "closing_debit",
			"label": _("Closing (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": "closing_credit",
			"label": _("Closing (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		}
	]

def get_opening_balance(account, filters):
	query = """
		SELECT
			glp.account,
			SUM(glp.debit_amount) as debit,
			SUM(glp.credit_amount) as credit,
			CASE
				WHEN SUM(glp.debit_amount) > SUM(glp.credit_amount) THEN SUM(glp.debit_amount) - SUM(glp.credit_amount)
				ELSE 0
			END AS opening_debit,
			CASE
				WHEN SUM(glp.debit_amount) < SUM(glp.credit_amount) THEN SUM(glp.credit_amount) - SUM(glp.debit_amount)
				ELSE 0
			END AS opening_credit
		FROM
			`tabGL Posting` as glp,
			`tabAccount` as a
		WHERE
			(a.name = '{0}' or a.parent_account = '{0}') AND
			glp.account = a.name
	""".format(account)
	if filters.get('from_date'):
		query += "AND glp.posting_date < '{0}'".format(filters.get('from_date'))
	data = frappe.db.sql(query, as_dict=True)[0]
	return data

def accumulate_values_into_parents(accounts, accounts_by_name):
    for d in reversed(accounts):
        if d.parent_account:
            difference = d['debit'] - d['credit']
            if difference > 0:
                accounts_by_name[d.parent_account]['debit'] += difference
            elif difference < 0:
                accounts_by_name[d.parent_account]['credit'] -= difference
