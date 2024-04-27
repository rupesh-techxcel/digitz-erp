# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns, data = [], []
 	 
	summary_view = filters.get('summary_view') 
	data = get_data(filters)
 
	
		# # if (not filters.get('account')) and (not filters.get('customer')) and (not filters.get('supplier')):
		# 	frappe.throw("Please select at least one of the following: account, customer, or supplier for detailed view.")
	columns = get_columns()
	
	include_party = False
 
	if(filters.get('show_party')):
			include_party = True
  
	# Because for summary view there is no party column
	if not summary_view and not include_party:
		columns = [col for col in columns if col["fieldname"] != "party"]
  
	return columns, data

def get_data(filters):
   
	data = []

	# Filter for account, supplier and dates
	if filters.get('account') and filters.get('supplier') and filters.get('from_date') and filters.get('to_date'):
		
		sql = """
			SELECT SUM(debit_amount) - SUM(credit_amount) AS difference
			FROM `tabGL Posting` pi
			WHERE account = '{account}' and party='{supplier}' and pi.posting_date < '{from_date}'
		""".format(account = filters.get('account'), supplier=filters.get('supplier'), from_date = filters.get('from_date'))

		opening_data = frappe.db.sql(sql, as_dict = True)

		if opening_data and opening_data[0].difference:
			opening_balance = opening_data[0].difference
			dr_or_cr = "Dr" if opening_balance > 0 else "Cr"
			
			summary_row = {
				"voucher_type": "Opening",
				"voucher_no": "Balance",
				"posting_date": filters.get("from_date"),
				"account": "Supplier Opening Balance",
				"remarks": "",
				"debit_amount": opening_balance if dr_or_cr == "Dr" else 0,
				"credit_amount": abs(opening_balance) if dr_or_cr == "Cr" else 0,
			}

			data.append(summary_row)

		trans_data = frappe.db.sql("""
			SELECT
			voucher_type, voucher_no, posting_date,account,party, remarks, debit_amount, credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{supplier}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}'	ORDER BY pi.posting_date""".format(account = filters.get('account'), supplier=filters.get('supplier'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

		data.extend(trans_data)	

		sql = """
			SELECT SUM(debit_amount) - SUM(credit_amount) AS difference
			FROM `tabGL Posting` pi
			WHERE account = '{account}' and party='{supplier}' and pi.posting_date <= '{to_date}'
		""".format(account = filters.get('account'), supplier = filters.get('supplier'), to_date = filters.get('to_date'))

		closing_data = frappe.db.sql(sql, as_dict = True)
		if closing_data and closing_data[0].difference:
			closing_balance = closing_data[0].difference
			dr_or_cr = "Dr" if closing_balance > 0 else "Cr"

			# Create a summary row with the difference value and 'Supplier Opening Balance'
			summary_row = {
				"voucher_type": "Closing Balance",
				"voucher_no": "",
				"posting_date": filters.get("to_date"),
				"account": "Supplier Closing Balance",
				"remarks": "",
				"debit_amount": closing_balance if closing_balance>0 else 0,
				"credit_amount": abs(closing_balance) if closing_balance<0 else 0
			}

			data.append(summary_row)
	# Filters for account , customer and dates   
	elif filters.get('account') and filters.get('customer') and filters.get('from_date') and filters.get('to_date'):
     
		sql = """
			SELECT SUM(debit_amount) - SUM(credit_amount) AS difference
			FROM `tabGL Posting` pi
			WHERE account = '{account}' and party='{customer}' and pi.posting_date < '{from_date}'
		""".format(account = filters.get('account'), customer=filters.get('customer'), from_date = filters.get('from_date'))

		opening_data = frappe.db.sql(sql, as_dict = True)

		if opening_data and opening_data[0].difference:
			opening_balance = opening_data[0].difference
			dr_or_cr = "Dr" if opening_balance > 0 else "Cr"

			# Create a summary row with the difference value and 'Supplier Opening Balance'
			summary_row = {
				"voucher_type": "Opening",
				"voucher_no": "Balance",
				"posting_date": filters.get("from_date"),
				"account": "Customer Opening Balance",
				"remarks": "",
				"debit_amount": opening_balance if dr_or_cr == "Dr" else 0,
				"credit_amount": abs(opening_balance) if dr_or_cr == "Cr" else 0,
			}

			data.append(summary_row)

		trans_data = frappe.db.sql("""
			SELECT
			voucher_type, voucher_no, posting_date,account,party, remarks, debit_amount, credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{customer}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}'	ORDER BY pi.posting_date""".format(account = filters.get('account'), customer=filters.get('customer'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

		data.extend(trans_data)	

		sql = """
			SELECT SUM(debit_amount) - SUM(credit_amount) AS difference
			FROM `tabGL Posting` pi
			WHERE account = '{account}' and party='{customer}' and pi.posting_date <= '{to_date}'
		""".format(account = filters.get('account'), customer = filters.get('customer'), to_date = filters.get('to_date'))

		closing_data = frappe.db.sql(sql, as_dict = True)
		if closing_data and closing_data[0].difference:
			closing_balance = closing_data[0].difference
			dr_or_cr = "Dr" if closing_balance > 0 else "Cr"

			# Create a summary row with the difference value and 'Supplier Opening Balance'
			summary_row = {
				"voucher_type": "Closing Balance",
				"voucher_no": "Balance",
				"posting_date": filters.get("to_date"),
				"account": "Customer Closing Balance",
				"remarks": "",
				"debit_amount": closing_balance if dr_or_cr == "Dr" else 0,
				"credit_amount": abs(closing_balance) if dr_or_cr == "Cr" else 0,
			}

			data.append(summary_row)

	# Filter for supplier and dates
	elif filters.get('supplier') and filters.get('from_date') and filters.get('to_date'):
     	
		sql = """
			SELECT SUM(debit_amount) - SUM(credit_amount) AS difference
			FROM `tabGL Posting` pi
			WHERE party='{supplier}' and pi.posting_date < '{from_date}'
		""".format(supplier=filters.get('supplier'), from_date = filters.get('from_date'))

		opening_data = frappe.db.sql(sql, as_dict = True)

		if opening_data and opening_data[0].difference:
			opening_balance = opening_data[0].difference
			dr_or_cr = "Dr" if opening_balance > 0 else "Cr"

			# Create a summary row with the difference value and 'Supplier Opening Balance'
			summary_row = {
				"voucher_type": "Opening",
				"voucher_no": "Balance",
				"posting_date": filters.get("from_date"),
				"account": "Supplier Opening Balance",
				"remarks": "",
				"debit_amount": opening_balance if dr_or_cr == "Dr" else 0,
				"credit_amount": abs(opening_balance) if dr_or_cr == "Cr" else 0,
			}

			data.append(summary_row)

		trans_data = frappe.db.sql("""
			SELECT
			voucher_type, voucher_no, posting_date,account,party, remarks, debit_amount, credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE party='{supplier}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}'	ORDER BY pi.posting_date""".format(supplier=filters.get('supplier'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

		data.extend(trans_data)	

		sql = """
			SELECT SUM(debit_amount) - SUM(credit_amount) AS difference
			FROM `tabGL Posting` pi
			WHERE party='{supplier}' and pi.posting_date <= '{to_date}'
		""".format(supplier = filters.get('supplier'), to_date = filters.get('to_date'))

		closing_data = frappe.db.sql(sql, as_dict = True)
		if closing_data and closing_data[0].difference:
			closing_balance = closing_data[0].difference
			dr_or_cr = "Dr" if closing_balance > 0 else "Cr"

			# Create a summary row with the difference value and 'Supplier Opening Balance'
			summary_row = {
				"voucher_type":  "Closing Balance",
				"voucher_no": "Balance",
				"posting_date": filters.get("to_date"),
				"account": "Supplier Closing Balance",
				"remarks": "",
				"debit_amount": closing_balance if dr_or_cr == "Dr" else 0,
				"credit_amount": abs(closing_balance) if dr_or_cr == "Cr" else 0,
			}

			data.append(summary_row)

	# Filter for customer and dates
	elif filters.get('customer') and filters.get('from_date') and filters.get('to_date'):     
		
		sql = """
			SELECT SUM(debit_amount) - SUM(credit_amount) AS difference
			FROM `tabGL Posting` pi
			WHERE party='{customer}' and pi.posting_date < '{from_date}'
		""".format(customer=filters.get('customer'), from_date = filters.get('from_date'))

		opening_data = frappe.db.sql(sql, as_dict = True)

		if opening_data and opening_data[0].difference:
			opening_balance = opening_data[0].difference
			dr_or_cr = "Dr" if opening_balance > 0 else "Cr"

			# Create a summary row with the difference value and 'Supplier Opening Balance'
			summary_row = {
				"voucher_type": "Opening",
				"voucher_no": "Balance",
				"posting_date": filters.get("from_date"),
				"account": "Customer Opening Balance",
				"remarks": "",
				"debit_amount": opening_balance if dr_or_cr == "Dr" else 0,
				"credit_amount": abs(opening_balance) if dr_or_cr == "Cr" else 0,
			}

			data.append(summary_row)

		trans_data = frappe.db.sql("""
			SELECT
			voucher_type, voucher_no, posting_date,account,party, remarks, debit_amount, credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE party='{customer}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}'	ORDER BY pi.posting_date""".format(customer=filters.get('customer'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

		data.extend(trans_data)	

		sql = """
			SELECT SUM(debit_amount) - SUM(credit_amount) AS difference
			FROM `tabGL Posting` pi
			WHERE party='{customer}' and pi.posting_date <= '{to_date}'
		""".format(customer = filters.get('customer'), to_date = filters.get('to_date'))

		closing_data = frappe.db.sql(sql, as_dict = True)
		if closing_data and closing_data[0].difference:
			closing_balance = closing_data[0].difference
			dr_or_cr = "Dr" if closing_balance > 0 else "Cr"

			# Create a summary row with the difference value and 'Supplier Opening Balance'
			summary_row = {
				"voucher_type": "Closing Balance",
				"voucher_no": "Balance",
				"posting_date": filters.get("to_date"),
				"account": "Customer Closing Balance",
				"remarks": "",
				"debit_amount": closing_balance if dr_or_cr == "Dr" else 0,
				"credit_amount": abs(closing_balance) if dr_or_cr == "Cr" else 0,
			}

			data.append(summary_row)   

	elif filters.get('account') and  filters.get('from_date') and filters.get('to_date'):
     	
		sql = """
			SELECT SUM(debit_amount) - SUM(credit_amount) AS difference
			FROM `tabGL Posting` pi
			WHERE account = '{account}' and pi.posting_date < '{from_date}'
		""".format(account = filters.get('account'), from_date = filters.get('from_date'))

		print(sql)

		opening_data = frappe.db.sql(sql, as_dict = True)

		print("opening_data")
		print(opening_data)

		if opening_data and opening_data[0].difference:
			opening_balance = opening_data[0].difference
			dr_or_cr = "Dr" if opening_balance > 0 else "Cr"

			# Create a summary row with the difference value and 'Supplier Opening Balance'
			summary_row = {
				"voucher_type": "Opening Balance",
				"voucher_no": "",
				"posting_date": filters.get("from_date"),
				"account": filters.get('account'),
				"remarks": "",
				"debit_amount": opening_balance if dr_or_cr == "Dr" else 0,
				"credit_amount": abs(opening_balance) if dr_or_cr == "Cr" else 0,
			}

			data.append(summary_row)

		trans_data = frappe.db.sql("""
			SELECT
			voucher_type, voucher_no, posting_date,account,party, remarks, debit_amount, credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}'	ORDER BY pi.posting_date""".format(account = filters.get('account'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

		data.extend(trans_data)	

		sql = """
			SELECT SUM(debit_amount) - SUM(credit_amount) AS difference
			FROM `tabGL Posting` pi
			WHERE account = '{account}' and pi.posting_date <= '{to_date}'
		""".format(account = filters.get('account'), to_date = filters.get('to_date'))

		closing_data = frappe.db.sql(sql, as_dict = True)
		if closing_data and closing_data[0].difference:
			closing_balance = closing_data[0].difference
			dr_or_cr = "Dr" if closing_balance > 0 else "Cr"

			# Create a summary row with the difference value and 'Supplier Opening Balance'
			summary_row = {
				"voucher_type": "Closing Balance",
				"voucher_no":"" ,
				"posting_date": filters.get("to_date"),
				"account": filters.get('account'),
				"remarks": "",
				"debit_amount": closing_balance if dr_or_cr == "Dr" else 0,
				"credit_amount": abs(closing_balance) if dr_or_cr == "Cr" else 0,
			}

			data.append(summary_row)
	# # Filter dates
	# elif filters.get('from_date') and filters.get('to_date'):
     
	# 	frappe.msgprint("Account , Customer Or Supplier is mandatory.")
	# # New data query to calculate the difference and 'Dr Or Cr'
		
	# 	sql = """
	# 		SELECT SUM(debit_amount) - SUM(credit_amount) AS difference
	# 		FROM `tabGL Posting` pi
	# 		WHERE pi.posting_date < '{from_date}'
	# 	""".format(from_date = filters.get('from_date'))

	# 	opening_data = frappe.db.sql(sql, as_dict = True)

	# 	if opening_data and opening_data[0].difference:
	# 		opening_balance = opening_data[0].difference
	# 		dr_or_cr = "Dr" if opening_balance > 0 else "Cr"

	# 		# Create a summary row with the difference value and 'Supplier Opening Balance'
	# 		summary_row = {
	# 			"voucher_type": "Opening",
	# 			"voucher_no": "Balance",
	# 			"posting_date": filters.get("from_date"),
	# 			"account": "Opening Balance",
	# 			"remarks": "",
	# 			"debit_amount": opening_balance if dr_or_cr == "Dr" else 0,
	# 			"credit_amount": abs(opening_balance) if dr_or_cr == "Cr" else 0,
	# 		}

	# 		data.append(summary_row)

	# 	trans_data = frappe.db.sql("""
	# 		SELECT
	# 		voucher_type, voucher_no, posting_date,account,party, remarks, debit_amount, credit_amount		
	# 		FROM 
	# 		`tabGL Posting` pi		
	# 		WHERE pi.posting_date BETWEEN '{from_date}' and '{to_date}'	ORDER BY pi.posting_date""".format(from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

	# 	data.extend(trans_data)	

	# 	sql = """
	# 		SELECT SUM(debit_amount) - SUM(credit_amount) AS difference
	# 		FROM `tabGL Posting` pi
	# 		WHERE pi.posting_date <= '{to_date}'
	# 	""".format(to_date = filters.get('to_date'))

	# 	closing_data = frappe.db.sql(sql, as_dict = True)
	# 	if closing_data and closing_data[0].difference:
	# 		closing_balance = closing_data[0].difference
	# 		dr_or_cr = "Dr" if closing_balance > 0 else "Cr"

	# 		# Create a summary row with the difference value and 'Supplier Opening Balance'
	# 		summary_row = {
	# 			"voucher_type": "Closing",
	# 			"voucher_no": "Balance",
	# 			"posting_date": filters.get("to_date"),
	# 			"account": "Closing Balance",
	# 			"remarks": "",
	# 			"debit_amount": closing_balance if dr_or_cr == "Dr" else 0,
	# 			"credit_amount": abs(closing_balance) if dr_or_cr == "Cr" else 0,
	# 		}

	# 		data.append(summary_row)
	# # Not likely to occur
	else:		
		frappe.msgprint("Select Account , Customer Or Supplier.") 

	# Method to add running total and indicate if it's Debit or Credit
	def add_running_total(data):
		running_total = 0
		for row in data:
			if row['voucher_type'] in ['Closing Balance']:
				running_total = row['debit_amount'] if row['debit_amount'] else (row['credit_amount'] * -1 if row['credit_amount'] else 0)
			# 	continue  # Skip opening and closing balance rows for running total calculation
			elif 'debit_amount' in row and row['debit_amount']:
				running_total += row['debit_amount']
			elif 'credit_amount' in row and row['credit_amount']:
				running_total -= row['credit_amount']

			row['running_total_debit'] = running_total if running_total > 0 else 0
			row['running_total_credit'] = -running_total if running_total < 0 else 0
			
	# Call to add running total right before returning data
	add_running_total(data)
 
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
			{
			"fieldname": "running_total_debit",
			"fieldtype": "Currency",
			"label": "Closing Debit",
			"width": 110,	
			},
			{
			"fieldname": "running_total_credit",
			"fieldtype": "Currency",
			"label": "Closing Credit",
			"width": 110,	
		},
       
	]

def get_columns_for_summary():

	return [
		{		
			"fieldname": "account",
			"fieldtype": "Link",
			"label": "Account Ledger",	
			"options":"Account",
			"width": 230,	
		},				
		{
			"fieldname": "opening_debit",
			"fieldtype": "Currency",
			"label": "Opening Debit",
			"width": 110,	
		},
		{
			"fieldname": "opening_credit",
			"fieldtype": "Currency",
			"label": "Opening Credit",
			"width": 110,	
		},
		{
			"fieldname": "debit_amount",
			"fieldtype": "Currency",
			"label": "Debit Total",
			"width": 110,	
		},
		{
			"fieldname": "credit_amount",
			"fieldtype": "Currency",
			"label": "Credit Total",
			"width": 110,	
		},
		{
		"fieldname": "closing_debit",
		"fieldtype": "Currency",
		"label": "Closing Debit",
		"width": 110,	
		},
		{
		"fieldname": "closing_credit",
		"fieldtype": "Currency",
		"label": "Closing Credit",
		"width": 110,	
		},
       
	]
