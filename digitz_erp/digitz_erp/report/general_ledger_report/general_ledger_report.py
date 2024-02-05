# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_data(filters):
   
	data = []

	order_by = "posting_date"
	if(filters.get("order_by_account")):
		order_by = "account,posting_date"
	
	# Filter for account, supplier and dates
	if filters.get('account') and filters.get('supplier') and filters.get('from_date') and filters.get('to_date'):
		print("case 1")
		   
		trans_data = frappe.db.sql("""
			SELECT
			voucher_type, voucher_no, posting_date,account,party, remarks, debit_amount, credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{supplier}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}' ORDER BY {order_by}""".format(account = filters.get('account'), supplier=filters.get('supplier'), from_date=filters.get('from_date'), to_date=filters.get('to_date'),order_by=order_by), as_dict=True)
  
		data.extend(trans_data)	
  
		
	# Filters for account , customer and dates   
	elif filters.get('account') and filters.get('customer') and filters.get('from_date') and filters.get('to_date'):
		
		trans_data = frappe.db.sql("""
			SELECT
			voucher_type, voucher_no, posting_date,account,party, remarks, debit_amount, credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{customer}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}'	ORDER BY {order_by}""".format(account = filters.get('account'), customer=filters.get('customer'), from_date=filters.get('from_date'), to_date=filters.get('to_date'),order_by=order_by), as_dict=True)

		data.extend(trans_data)	

		   
	# Filter for supplier and dates
	elif filters.get('supplier') and filters.get('from_date') and filters.get('to_date'):
     
		   
		trans_data = frappe.db.sql("""
			SELECT
			voucher_type, voucher_no, posting_date,account,party, remarks, debit_amount, credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE party='{supplier}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}'	ORDER BY {order_by}""".format(supplier=filters.get('supplier'), from_date=filters.get('from_date'), to_date=filters.get('to_date'),order_by=order_by), as_dict=True)
  
		data.extend(trans_data)	
  
		   
	# Filter for customer and dates
	elif filters.get('customer') and filters.get('from_date') and filters.get('to_date'):
     
			trans_data = frappe.db.sql("""
				SELECT
				voucher_type, voucher_no, posting_date,account,party, remarks, debit_amount, credit_amount		
				FROM 
				`tabGL Posting` pi		
				WHERE party='{customer}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}'	ORDER BY {order_by}""".format(customer=filters.get('customer'), from_date=filters.get('from_date'), to_date=filters.get('to_date'),order_by=order_by), as_dict=True)

			data.extend(trans_data)	
  
	elif filters.get('account') and  filters.get('from_date') and filters.get('to_date'):
		# New data query to calculate the difference and 'Dr Or Cr'
    
		trans_data = frappe.db.sql("""
			SELECT
			voucher_type, voucher_no, posting_date,account,party, remarks, debit_amount, credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}'	ORDER BY {order_by}""".format(account = filters.get('account'), from_date=filters.get('from_date'), to_date=filters.get('to_date'),order_by=order_by), as_dict=True)
  
		data.extend(trans_data)	
  
	# # Filter dates
	elif filters.get('from_date') and filters.get('to_date'):
	# New data query to calculate the difference and 'Dr Or Cr'
 
		trans_data = frappe.db.sql("""
			SELECT
			voucher_type, voucher_no, posting_date,account,party, remarks, debit_amount, credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.posting_date BETWEEN '{from_date}' and '{to_date}'	ORDER BY {order_by}""".format(from_date=filters.get('from_date'), to_date=filters.get('to_date'),order_by=order_by), as_dict=True)

		data.extend(trans_data)	

		sql = """
			SELECT SUM(debit_amount) - SUM(credit_amount) AS difference
			FROM `tabGL Posting` pi
			WHERE pi.posting_date <= '{to_date}' ORDER BY ORDER BY {order_by}
		""".format(to_date = filters.get('to_date'),order_by=order_by, as_dict=True)

		# Not likely to occur
	else:
		frappe.throw("Unknown filter condition") 
  	
	return data

def get_columns():
   
	return [
		{		
			"fieldname": "account",
			"fieldtype": "Link",
			"label": "Account Ledger",	
			"options":"Account",
			"width": 230,	
		},		
		{		
			"fieldname": "voucher_type",
			"fieldtype": "Link",
			"label": "Voucher Type",
   			"options":"DocType",
			"width": 110,	
		},
  		{		
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"label": "Voucher No",
			"options" : "voucher_type",
			"width": 130,	
		},
		{
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"label": "Date",
			"width": 100,	
		},
   		{
			"fieldname": "party",
			"fieldtype": "Data",
			"label": "Party",
			"width": 110,	
		},
  		{
			"fieldname": "remarks",
			"fieldtype": "Data",
			"label": "Remarks",
			"width": 210,	
		},    		
		{
			"fieldname": "debit_amount",
			"fieldtype": "Currency",
			"label": "Debit",
			"width": 110,	
		},
		{
			"fieldname": "credit_amount",
			"fieldtype": "Currency",
			"label": "Credit",
			"width": 110,	
		},
   			
       
	]
