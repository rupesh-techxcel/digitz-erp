# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns, data = [], []
 
	include_party = False
 
	# if(filters.get('show_party')):
	# 	include_party = True
 
	# if(filters.get('summary_view')):
	# 	data = get_transactions_summary_data(filters)
	# 	columns = get_columns_for_summary()
    
	# elif(filters.get('condensed_view')):     
	# 	data = get_transactions_condensed_data(filters)
	# 	columns = get_columns_for_condensed()		
	# else:
 
	data = get_transactions_data(filters)
	columns = get_columns()

	include_party = False
 
	if(filters.get('show_party')):
			include_party = True
  
	if not include_party:
		columns = [col for col in columns if col["fieldname"] != "party"]
   

	return columns, data

def get_transactions_data(filters):
   
	data = []

	# Filter for account, supplier and dates
	if filters.get('account') and filters.get('supplier') and filters.get('from_date') and filters.get('to_date'):
		print("case 1")
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
				"voucher_type": "Closing",
				"voucher_no": "Balance",
				"posting_date": filters.get("to_date"),
				"account": "Supplier Closing Balance",
				"remarks": "",
				"debit_amount": closing_balance if dr_or_cr == "Dr" else 0,
				"credit_amount": abs(closing_balance) if dr_or_cr == "Cr" else 0,
			}

			data.append(summary_row)
	# Filters for account , customer and dates   
	elif filters.get('account') and filters.get('customer') and filters.get('from_date') and filters.get('to_date'):
		print("case 2")
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
				"voucher_type": "Closing",
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
     
		print("case 3")
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
				"voucher_type": "Closing",
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
     
			print("case 4")
   
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
					"voucher_type": "Closing",
					"voucher_no": "Balance",
					"posting_date": filters.get("to_date"),
					"account": "Customer Closing Balance",
					"remarks": "",
					"debit_amount": closing_balance if dr_or_cr == "Dr" else 0,
					"credit_amount": abs(closing_balance) if dr_or_cr == "Cr" else 0,
				}

				data.append(summary_row)   
  
	elif filters.get('account') and  filters.get('from_date') and filters.get('to_date'):
		# New data query to calculate the difference and 'Dr Or Cr'
  
		print("case 5")
		
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
			   
			print("dr_or_cr")
			print(dr_or_cr)

			# Create a summary row with the difference value and 'Supplier Opening Balance'
			summary_row = {
				"voucher_type": "Opening",
				"voucher_no": "Balance",
				"posting_date": filters.get("from_date"),
				"account": "Account Opening Balance",
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
				"voucher_type": "Closing",
				"voucher_no": "Balance",
				"posting_date": filters.get("to_date"),
				"account": "Account Closing Balance",
				"remarks": "",
				"debit_amount": closing_balance if dr_or_cr == "Dr" else 0,
				"credit_amount": abs(closing_balance) if dr_or_cr == "Cr" else 0,
			}

			data.append(summary_row)
	# # Filter dates
	elif filters.get('from_date') and filters.get('to_date'):
	# New data query to calculate the difference and 'Dr Or Cr'
 
		print("case 6")
		
		sql = """
			SELECT SUM(debit_amount) - SUM(credit_amount) AS difference
			FROM `tabGL Posting` pi
			WHERE pi.posting_date < '{from_date}'
		""".format(from_date = filters.get('from_date'))

		opening_data = frappe.db.sql(sql, as_dict = True)

		if opening_data and opening_data[0].difference:
			opening_balance = opening_data[0].difference
			dr_or_cr = "Dr" if opening_balance > 0 else "Cr"

			# Create a summary row with the difference value and 'Supplier Opening Balance'
			summary_row = {
				"voucher_type": "Opening",
				"voucher_no": "Balance",
				"posting_date": filters.get("from_date"),
				"account": "Opening Balance",
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
			WHERE pi.posting_date BETWEEN '{from_date}' and '{to_date}'	ORDER BY pi.posting_date""".format(from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

		data.extend(trans_data)	

		sql = """
			SELECT SUM(debit_amount) - SUM(credit_amount) AS difference
			FROM `tabGL Posting` pi
			WHERE pi.posting_date <= '{to_date}'
		""".format(to_date = filters.get('to_date'))

		closing_data = frappe.db.sql(sql, as_dict = True)
		if closing_data and closing_data[0].difference:
			closing_balance = closing_data[0].difference
			dr_or_cr = "Dr" if closing_balance > 0 else "Cr"

			# Create a summary row with the difference value and 'Supplier Opening Balance'
			summary_row = {
				"voucher_type": "Closing",
				"voucher_no": "Balance",
				"posting_date": filters.get("to_date"),
				"account": "Closing Balance",
				"remarks": "",
				"debit_amount": closing_balance if dr_or_cr == "Dr" else 0,
				"credit_amount": abs(closing_balance) if dr_or_cr == "Cr" else 0,
			}

			data.append(summary_row)
	# Not likely to occur
	else:
		frappe.throw("Unknown filter condition") 
  	
	return data

def get_transactions_summary_data(filters):
   
	data = []	
	merged_data = []

	# Filter for account, supplier and dates
	if filters.get('account') and filters.get('supplier') and filters.get('from_date') and filters.get('to_date'):		
   
		trans_data = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{supplier}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format(account = filters.get('account'), supplier=filters.get('supplier'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)
  
		trans_data_opening = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{supplier}' and  pi.posting_date < '{from_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format(account = filters.get('account'), supplier=filters.get('supplier'), from_date=filters.get('from_date')), as_dict=True)  
		
		for td_opening in trans_data_opening:
			for td in trans_data:
				if td_opening['account'] == td['account'] and td_opening['party'] == td['party']:
					opening_debit = td_opening['debit_amount'] - td_opening['credit_amount'] if td_opening['debit_amount'] > td_opening['credit_amount'] else 0
					opening_credit = td_opening['credit_amount'] - td_opening['debit_amount'] if td_opening['credit_amount'] > td_opening['debit_amount'] else 0

					data.append({
						'account': td_opening['account'],
						'party': td_opening['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': opening_debit,
						'opening_credit': opening_credit
					})
     
		trans_data_closing = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{supplier}' and  pi.posting_date <= '{to_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format(account = filters.get('account'), supplier=filters.get('supplier'), to_date=filters.get('to_date')), as_dict=True)

		I = 0
		for td_closing in trans_data_closing:
			for td in data:
       
				print(td)
				
				if td_closing['account'] == td['account'] and td_closing['party'] == td['party']:

					closing_debit = td_closing['debit_amount'] - td_closing['credit_amount'] if td_closing['debit_amount'] > td_closing['credit_amount'] else 0
					closing_credit = td_closing['credit_amount'] - td_closing['debit_amount'] if td_closing['credit_amount'] > td_closing['debit_amount'] else 0
          
					merged_data.append({
						'account': td['account'],
						'party': td['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': td['opening_debit'],
						'opening_credit': td['opening_credit'],						
						'closing_debit': closing_debit ,
      					'closing_credit' : closing_credit
					})
     
		print("merged_data")
		print(merged_data)
  
  # Filter for account, supplier and dates
	elif filters.get('account') and filters.get('customer') and filters.get('from_date') and filters.get('to_date'):		
   
		trans_data = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{customer}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format(account = filters.get('account'), customer=filters.get('customer'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)
  
		trans_data_opening = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{customer}' and  pi.posting_date < '{from_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format(account = filters.get('account'), customer=filters.get('customer'), from_date=filters.get('from_date')), as_dict=True)  
		
		for td_opening in trans_data_opening:
			for td in trans_data:
				if td_opening['account'] == td['account'] and td_opening['party'] == td['party']:
					opening_debit = td_opening['debit_amount'] - td_opening['credit_amount'] if td_opening['debit_amount'] > td_opening['credit_amount'] else 0
					opening_credit = td_opening['credit_amount'] - td_opening['debit_amount'] if td_opening['credit_amount'] > td_opening['debit_amount'] else 0

					data.append({
						'account': td_opening['account'],
						'party': td_opening['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': opening_debit,
						'opening_credit': opening_credit
					})
     
		trans_data_closing = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{customer}' and  pi.posting_date <= '{to_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format(account = filters.get('account'), customer=filters.get('customer'),  to_date=filters.get('to_date')), as_dict=True)

		I = 0
		for td_closing in trans_data_closing:
			for td in data:
       
				print(td)
				
				if td_closing['account'] == td['account'] and td_closing['party'] == td['party']:

					closing_debit = td_closing['debit_amount'] - td_closing['credit_amount'] if td_closing['debit_amount'] > td_closing['credit_amount'] else 0
					closing_credit = td_closing['credit_amount'] - td_closing['debit_amount'] if td_closing['credit_amount'] > td_closing['debit_amount'] else 0
          
					merged_data.append({
						'account': td['account'],
						'party': td['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': td['opening_debit'],
						'opening_credit': td['opening_credit'],						
						'closing_debit': closing_debit ,
      					'closing_credit' : closing_credit
					})
     
		print("merged_data")
		print(merged_data)
	
	# Filter for supplier and dates
	elif filters.get('supplier') and filters.get('from_date') and filters.get('to_date'):		
   
		trans_data = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE  party='{supplier}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format( supplier=filters.get('supplier'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)
  
		trans_data_opening = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE  party='{supplier}' and  pi.posting_date < '{from_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format(supplier=filters.get('supplier'), from_date=filters.get('from_date')), as_dict=True)  
		
		for td_opening in trans_data_opening:
			for td in trans_data:
				if td_opening['account'] == td['account'] and td_opening['party'] == td['party']:
					opening_debit = td_opening['debit_amount'] - td_opening['credit_amount'] if td_opening['debit_amount'] > td_opening['credit_amount'] else 0
					opening_credit = td_opening['credit_amount'] - td_opening['debit_amount'] if td_opening['credit_amount'] > td_opening['debit_amount'] else 0

					data.append({
						'account': td_opening['account'],
						'party': td_opening['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': opening_debit,
						'opening_credit': opening_credit
					})
     
		trans_data_closing = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE party='{supplier}' and  pi.posting_date <= '{to_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format(supplier=filters.get('supplier'),  to_date=filters.get('to_date')), as_dict=True)

		I = 0
		for td_closing in trans_data_closing:
			for td in data:
       
				print(td)
				
				if td_closing['account'] == td['account'] and td_closing['party'] == td['party']:

					closing_debit = td_closing['debit_amount'] - td_closing['credit_amount'] if td_closing['debit_amount'] > td_closing['credit_amount'] else 0
					closing_credit = td_closing['credit_amount'] - td_closing['debit_amount'] if td_closing['credit_amount'] > td_closing['debit_amount'] else 0
          
					merged_data.append({
						'account': td['account'],
						'party': td['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': td['opening_debit'],
						'opening_credit': td['opening_credit'],						
						'closing_debit': closing_debit ,
      					'closing_credit' : closing_credit
					})
     
		print("merged_data")
		print(merged_data)
  
   
	# Filter for customer and dates
	elif filters.get('customer') and filters.get('from_date') and filters.get('to_date'):		
   
		trans_data = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE  party='{customer}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format( customer=filters.get('customer'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)
  
		trans_data_opening = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE  and party='{customer}' and  pi.posting_date < '{from_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format(customer=filters.get('customer'), from_date=filters.get('from_date')), as_dict=True)  
		
		for td_opening in trans_data_opening:
			for td in trans_data:
				if td_opening['account'] == td['account'] and td_opening['party'] == td['party']:
					opening_debit = td_opening['debit_amount'] - td_opening['credit_amount'] if td_opening['debit_amount'] > td_opening['credit_amount'] else 0
					opening_credit = td_opening['credit_amount'] - td_opening['debit_amount'] if td_opening['credit_amount'] > td_opening['debit_amount'] else 0

					data.append({
						'account': td_opening['account'],
						'party': td_opening['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': opening_debit,
						'opening_credit': opening_credit
					})
     
		trans_data_closing = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE party='{customer}' and  pi.posting_date <= '{to_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format(customer=filters.get('customer'),  to_date=filters.get('to_date')), as_dict=True)

		I = 0
		for td_closing in trans_data_closing:
			for td in data:
       
				print(td)
				
				if td_closing['account'] == td['account'] and td_closing['party'] == td['party']:

					closing_debit = td_closing['debit_amount'] - td_closing['credit_amount'] if td_closing['debit_amount'] > td_closing['credit_amount'] else 0
					closing_credit = td_closing['credit_amount'] - td_closing['debit_amount'] if td_closing['credit_amount'] > td_closing['debit_amount'] else 0
          
					merged_data.append({
						'account': td['account'],
						'party': td['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': td['opening_debit'],
						'opening_credit': td['opening_credit'],						
						'closing_debit': closing_debit ,
      					'closing_credit' : closing_credit
					})
     
		print("merged_data")
		print(merged_data)
	# Filter for account and dates
	elif filters.get('account') and filters.get('from_date') and filters.get('to_date'):		
		trans_data = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE  account='{account}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format( account=filters.get('account'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)
  
		trans_data_opening = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE account='{account}' and  pi.posting_date < '{from_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format(account=filters.get('account'), from_date=filters.get('from_date')), as_dict=True)  
		
		for td_opening in trans_data_opening:
			for td in trans_data:
				if td_opening['account'] == td['account'] and td_opening['party'] == td['party']:
					opening_debit = td_opening['debit_amount'] - td_opening['credit_amount'] if td_opening['debit_amount'] > td_opening['credit_amount'] else 0
					opening_credit = td_opening['credit_amount'] - td_opening['debit_amount'] if td_opening['credit_amount'] > td_opening['debit_amount'] else 0

					data.append({
						'account': td_opening['account'],
						'party': td_opening['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': opening_debit,
						'opening_credit': opening_credit
					})
     
		trans_data_closing = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE account='{account}' and  pi.posting_date <= '{to_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format(account=filters.get('account'),  to_date=filters.get('to_date')), as_dict=True)

		I = 0
		for td_closing in trans_data_closing:
			for td in data:
       
				print(td)
				
				if td_closing['account'] == td['account'] and td_closing['party'] == td['party']:

					closing_debit = td_closing['debit_amount'] - td_closing['credit_amount'] if td_closing['debit_amount'] > td_closing['credit_amount'] else 0
					closing_credit = td_closing['credit_amount'] - td_closing['debit_amount'] if td_closing['credit_amount'] > td_closing['debit_amount'] else 0
          
					merged_data.append({
						'account': td['account'],
						'party': td['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': td['opening_debit'],
						'opening_credit': td['opening_credit'],						
						'closing_debit': closing_debit ,
      					'closing_credit' : closing_credit
					})
     
		print("merged_data")
		print(merged_data)
  
		
	## Filter dates	
	elif filters.get('from_date') and filters.get('to_date'):		
		trans_data = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.posting_date BETWEEN '{from_date}' and '{to_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format( from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)
  
		trans_data_opening = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.posting_date < '{from_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format(from_date=filters.get('from_date')), as_dict=True)  
		
		for td_opening in trans_data_opening:
			for td in trans_data:
				if td_opening['account'] == td['account'] and td_opening['party'] == td['party']:
					opening_debit = td_opening['debit_amount'] - td_opening['credit_amount'] if td_opening['debit_amount'] > td_opening['credit_amount'] else 0
					opening_credit = td_opening['credit_amount'] - td_opening['debit_amount'] if td_opening['credit_amount'] > td_opening['debit_amount'] else 0

					data.append({
						'account': td_opening['account'],
						'party': td_opening['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': opening_debit,
						'opening_credit': opening_credit
					})
     
		trans_data_closing = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE  pi.posting_date <= '{to_date}' GROUP BY account,party	ORDER BY pi.posting_date """.format(to_date=filters.get('to_date')), as_dict=True)

		I = 0
		for td_closing in trans_data_closing:
			for td in data:
       
				print(td)
				
				if td_closing['account'] == td['account'] and td_closing['party'] == td['party']:

					closing_debit = td_closing['debit_amount'] - td_closing['credit_amount'] if td_closing['debit_amount'] > td_closing['credit_amount'] else 0
					closing_credit = td_closing['credit_amount'] - td_closing['debit_amount'] if td_closing['credit_amount'] > td_closing['debit_amount'] else 0
          
					merged_data.append({
						'account': td['account'],
						'party': td['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': td['opening_debit'],
						'opening_credit': td['opening_credit'],						
						'closing_debit': closing_debit ,
      					'closing_credit' : closing_credit
					})
     
		print("merged_data")
		print(merged_data)
  	
	# Not likely to occur
	else:
		frappe.throw("Unknown filter condition")
   
	return merged_data

def get_transactions_condensed_data(filters):
   
	data = []	
	merged_data = []

	# Filter for account, supplier and dates
	if filters.get('account') and filters.get('supplier') and filters.get('from_date') and filters.get('to_date'):		
   
		trans_data = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{supplier}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}' GROUP BY account	ORDER BY pi.posting_date """.format(account = filters.get('account'), supplier=filters.get('supplier'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)
  
		trans_data_opening = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{supplier}' and  pi.posting_date < '{from_date}' GROUP BY account	ORDER BY pi.posting_date """.format(account = filters.get('account'), supplier=filters.get('supplier'), from_date=filters.get('from_date')), as_dict=True)  
		
		for td_opening in trans_data_opening:
			for td in trans_data:
				if td_opening['account'] == td['account'] and td_opening['party'] == td['party']:
					opening_debit = td_opening['debit_amount'] - td_opening['credit_amount'] if td_opening['debit_amount'] > td_opening['credit_amount'] else 0
					opening_credit = td_opening['credit_amount'] - td_opening['debit_amount'] if td_opening['credit_amount'] > td_opening['debit_amount'] else 0

					data.append({
						'account': td_opening['account'],
						'party': td_opening['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': opening_debit,
						'opening_credit': opening_credit
					})
     
		trans_data_closing = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{supplier}' and  pi.posting_date <= '{to_date}' GROUP BY account ORDER BY pi.posting_date """.format(account = filters.get('account'), supplier=filters.get('supplier'), to_date=filters.get('to_date')), as_dict=True)

		I = 0
		for td_closing in trans_data_closing:
			for td in data:
       
				print(td)
				
				if td_closing['account'] == td['account'] and td_closing['party'] == td['party']:

					closing_debit = td_closing['debit_amount'] - td_closing['credit_amount'] if td_closing['debit_amount'] > td_closing['credit_amount'] else 0
					closing_credit = td_closing['credit_amount'] - td_closing['debit_amount'] if td_closing['credit_amount'] > td_closing['debit_amount'] else 0
          
					merged_data.append({
						'account': td['account'],
						'party': td['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': td['opening_debit'],
						'opening_credit': td['opening_credit'],						
						'closing_debit': closing_debit ,
      					'closing_credit' : closing_credit
					})
     
		print("merged_data")
		print(merged_data)
  
  # Filter for account, supplier and dates
	elif filters.get('account') and filters.get('customer') and filters.get('from_date') and filters.get('to_date'):		
   
		trans_data = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{customer}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}' GROUP BY account	ORDER BY pi.posting_date """.format(account = filters.get('account'), customer=filters.get('customer'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)
  
		trans_data_opening = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{customer}' and  pi.posting_date < '{from_date}' GROUP BY account	ORDER BY pi.posting_date """.format(account = filters.get('account'), customer=filters.get('customer'), from_date=filters.get('from_date')), as_dict=True)  
		
		for td_opening in trans_data_opening:
			for td in trans_data:
				if td_opening['account'] == td['account'] and td_opening['party'] == td['party']:
					opening_debit = td_opening['debit_amount'] - td_opening['credit_amount'] if td_opening['debit_amount'] > td_opening['credit_amount'] else 0
					opening_credit = td_opening['credit_amount'] - td_opening['debit_amount'] if td_opening['credit_amount'] > td_opening['debit_amount'] else 0

					data.append({
						'account': td_opening['account'],
						'party': td_opening['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': opening_debit,
						'opening_credit': opening_credit
					})
     
		trans_data_closing = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.account = '{account}' and party='{customer}' and  pi.posting_date <= '{to_date}' GROUP BY account	ORDER BY pi.posting_date """.format(account = filters.get('account'), customer=filters.get('customer'),  to_date=filters.get('to_date')), as_dict=True)

		I = 0
		for td_closing in trans_data_closing:
			for td in data:
       
				print(td)
				
				if td_closing['account'] == td['account'] and td_closing['party'] == td['party']:

					closing_debit = td_closing['debit_amount'] - td_closing['credit_amount'] if td_closing['debit_amount'] > td_closing['credit_amount'] else 0
					closing_credit = td_closing['credit_amount'] - td_closing['debit_amount'] if td_closing['credit_amount'] > td_closing['debit_amount'] else 0
          
					merged_data.append({
						'account': td['account'],
						'party': td['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': td['opening_debit'],
						'opening_credit': td['opening_credit'],						
						'closing_debit': closing_debit ,
      					'closing_credit' : closing_credit
					})
     
		print("merged_data")
		print(merged_data)
	
	# Filter for supplier and dates
	elif filters.get('supplier') and filters.get('from_date') and filters.get('to_date'):		
   
		trans_data = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE  party='{supplier}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}' GROUP BY account	ORDER BY pi.posting_date """.format( supplier=filters.get('supplier'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)
  
		trans_data_opening = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE  party='{supplier}' and  pi.posting_date < '{from_date}' GROUP BY account	ORDER BY pi.posting_date """.format(supplier=filters.get('supplier'), from_date=filters.get('from_date')), as_dict=True)  
		
		for td_opening in trans_data_opening:
			for td in trans_data:
				if td_opening['account'] == td['account'] and td_opening['party'] == td['party']:
					opening_debit = td_opening['debit_amount'] - td_opening['credit_amount'] if td_opening['debit_amount'] > td_opening['credit_amount'] else 0
					opening_credit = td_opening['credit_amount'] - td_opening['debit_amount'] if td_opening['credit_amount'] > td_opening['debit_amount'] else 0

					data.append({
						'account': td_opening['account'],
						'party': td_opening['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': opening_debit,
						'opening_credit': opening_credit
					})
     
		trans_data_closing = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE party='{supplier}' and  pi.posting_date <= '{to_date}' GROUP BY account ORDER BY pi.posting_date """.format(supplier=filters.get('supplier'),  to_date=filters.get('to_date')), as_dict=True)

		I = 0
		for td_closing in trans_data_closing:
			for td in data:
       
				print(td)
				
				if td_closing['account'] == td['account'] and td_closing['party'] == td['party']:

					closing_debit = td_closing['debit_amount'] - td_closing['credit_amount'] if td_closing['debit_amount'] > td_closing['credit_amount'] else 0
					closing_credit = td_closing['credit_amount'] - td_closing['debit_amount'] if td_closing['credit_amount'] > td_closing['debit_amount'] else 0
          
					merged_data.append({
						'account': td['account'],
						'party': td['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': td['opening_debit'],
						'opening_credit': td['opening_credit'],						
						'closing_debit': closing_debit ,
      					'closing_credit' : closing_credit
					})
     
		print("merged_data")
		print(merged_data)
  
   
	# Filter for customer and dates
	elif filters.get('customer') and filters.get('from_date') and filters.get('to_date'):		
   
		trans_data = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE  party='{customer}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}' GROUP BY account	ORDER BY pi.posting_date """.format( customer=filters.get('customer'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)
  
		trans_data_opening = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE  and party='{customer}' and  pi.posting_date < '{from_date}' GROUP BY account	ORDER BY pi.posting_date """.format(customer=filters.get('customer'), from_date=filters.get('from_date')), as_dict=True)  
		
		for td_opening in trans_data_opening:
			for td in trans_data:
				if td_opening['account'] == td['account'] and td_opening['party'] == td['party']:
					opening_debit = td_opening['debit_amount'] - td_opening['credit_amount'] if td_opening['debit_amount'] > td_opening['credit_amount'] else 0
					opening_credit = td_opening['credit_amount'] - td_opening['debit_amount'] if td_opening['credit_amount'] > td_opening['debit_amount'] else 0

					data.append({
						'account': td_opening['account'],
						'party': td_opening['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': opening_debit,
						'opening_credit': opening_credit
					})
     
		trans_data_closing = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE party='{customer}' and  pi.posting_date <= '{to_date}' GROUP BY account	ORDER BY pi.posting_date """.format(customer=filters.get('customer'),  to_date=filters.get('to_date')), as_dict=True)

		I = 0
		for td_closing in trans_data_closing:
			for td in data:
       
				print(td)
				
				if td_closing['account'] == td['account'] and td_closing['party'] == td['party']:

					closing_debit = td_closing['debit_amount'] - td_closing['credit_amount'] if td_closing['debit_amount'] > td_closing['credit_amount'] else 0
					closing_credit = td_closing['credit_amount'] - td_closing['debit_amount'] if td_closing['credit_amount'] > td_closing['debit_amount'] else 0
          
					merged_data.append({
						'account': td['account'],
						'party': td['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': td['opening_debit'],
						'opening_credit': td['opening_credit'],						
						'closing_debit': closing_debit ,
      					'closing_credit' : closing_credit
					})
     
		print("merged_data")
		print(merged_data)
	# Filter for account and dates
	elif filters.get('account') and filters.get('from_date') and filters.get('to_date'):		
		trans_data = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE  account='{account}' and  pi.posting_date BETWEEN '{from_date}' and '{to_date}' GROUP BY account	ORDER BY pi.posting_date """.format( account=filters.get('account'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)
  
		trans_data_opening = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE  account='{account}' and  pi.posting_date < '{from_date}' GROUP BY account	ORDER BY pi.posting_date """.format(account=filters.get('account'), from_date=filters.get('from_date')), as_dict=True)  
		
		for td_opening in trans_data_opening:
			for td in trans_data:
				if td_opening['account'] == td['account'] and td_opening['party'] == td['party']:
					opening_debit = td_opening['debit_amount'] - td_opening['credit_amount'] if td_opening['debit_amount'] > td_opening['credit_amount'] else 0
					opening_credit = td_opening['credit_amount'] - td_opening['debit_amount'] if td_opening['credit_amount'] > td_opening['debit_amount'] else 0

					data.append({
						'account': td_opening['account'],
						'party': td_opening['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': opening_debit,
						'opening_credit': opening_credit
					})
     
		trans_data_closing = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE account='{account}' and  pi.posting_date <= '{to_date}' GROUP BY account	ORDER BY pi.posting_date """.format(account=filters.get('account'),  to_date=filters.get('to_date')), as_dict=True)

		I = 0
		for td_closing in trans_data_closing:
			for td in data:
       
				print(td)
				
				if td_closing['account'] == td['account'] and td_closing['party'] == td['party']:

					closing_debit = td_closing['debit_amount'] - td_closing['credit_amount'] if td_closing['debit_amount'] > td_closing['credit_amount'] else 0
					closing_credit = td_closing['credit_amount'] - td_closing['debit_amount'] if td_closing['credit_amount'] > td_closing['debit_amount'] else 0
          
					merged_data.append({
						'account': td['account'],
						'party': td['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': td['opening_debit'],
						'opening_credit': td['opening_credit'],						
						'closing_debit': closing_debit ,
      					'closing_credit' : closing_credit
					})
     
		print("merged_data")
		print(merged_data)  
		
	## Filter dates	
	elif filters.get('from_date') and filters.get('to_date'):		
		trans_data = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.posting_date BETWEEN '{from_date}' and '{to_date}' GROUP BY account ORDER BY pi.posting_date """.format( from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)
  
		trans_data_opening = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE pi.posting_date < '{from_date}' GROUP BY account	ORDER BY pi.posting_date """.format(from_date=filters.get('from_date')), as_dict=True)  
		
		for td_opening in trans_data_opening:
			for td in trans_data:
				if td_opening['account'] == td['account'] and td_opening['party'] == td['party']:
					opening_debit = td_opening['debit_amount'] - td_opening['credit_amount'] if td_opening['debit_amount'] > td_opening['credit_amount'] else 0
					opening_credit = td_opening['credit_amount'] - td_opening['debit_amount'] if td_opening['credit_amount'] > td_opening['debit_amount'] else 0

					data.append({
						'account': td_opening['account'],
						'party': td_opening['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': opening_debit,
						'opening_credit': opening_credit
					})
     
		trans_data_closing = frappe.db.sql("""
			SELECT
			account,party, sum(debit_amount) as debit_amount, sum(credit_amount) as credit_amount		
			FROM 
			`tabGL Posting` pi		
			WHERE  pi.posting_date <= '{to_date}' GROUP BY account	ORDER BY pi.posting_date """.format(to_date=filters.get('to_date')), as_dict=True)

		I = 0
		for td_closing in trans_data_closing:
			for td in data:
       
				print(td)
				
				if td_closing['account'] == td['account'] and td_closing['party'] == td['party']:

					closing_debit = td_closing['debit_amount'] - td_closing['credit_amount'] if td_closing['debit_amount'] > td_closing['credit_amount'] else 0
					closing_credit = td_closing['credit_amount'] - td_closing['debit_amount'] if td_closing['credit_amount'] > td_closing['debit_amount'] else 0
          
					merged_data.append({
						'account': td['account'],
						'party': td['party'],
						'debit_amount': td['debit_amount'],
						'credit_amount': td['credit_amount'],
						'opening_debit': td['opening_debit'],
						'opening_credit': td['opening_credit'],						
						'closing_debit': closing_debit ,
      					'closing_credit' : closing_credit
					})
     
		print("merged_data")
		print(merged_data)
  	
	# Not likely to occur
	else:
		frappe.throw("Unknown filter condition")
   
	return merged_data

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
    		# {
			# 	"fieldname": "opening_debit",
			# 	"fieldtype": "Currency",
			# 	"label": "Opening Debit",
			# 	"width": 110,	
			# },
			# {
			# 	"fieldname": "opening_credit",
			# 	"fieldtype": "Currency",
			# 	"label": "Opening Credit",
			# 	"width": 110,	
			# },
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
   			# {
			# 	"fieldname": "closing_debit",
			# 	"fieldtype": "Currency",
			# 	"label": "Closing Debit",
			# 	"width": 110,	
			# },
			# {
			# 	"fieldname": "closing_credit",
			# 	"fieldtype": "Currency",
			# 	"label": "Closing Credit",
			# 	"width": 110,	
			# },
       
	]
 
def get_columns_for_summary():
 
	return [
			{		
				"fieldname": "account",
				"fieldtype": "Data",
				"label": "Account Ledger",	
				"options":"Account",
				"width": 200,	
			},			
			{
				"fieldname": "party",
				"fieldtype": "Data",
				"label": "Party",
				"width": 200,	
			},
			{
				"fieldname": "opening_debit",
				"fieldtype": "Currency",
				"label": "Opening Debit",
				"width": 150,	
			},
			{
				"fieldname": "opening_credit",
				"fieldtype": "Currency",
				"label": "Opening Credit",
				"width": 150,	
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
	
def get_columns_for_condensed():     
 
	return [
			{		
				"fieldname": "account",
				"fieldtype": "Data",
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