# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime, timedelta

def execute(filters=None):
	columns = get_columns()
	data= None
	show_datewise = filters.get("show_datewise")
 
	from_date_str = filters.get('from_date')
	to_date_str = filters.get('to_date')

	# Convert string dates to datetime objects
	from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
	to_date = datetime.strptime(to_date_str, '%Y-%m-%d')

	# Set from_date to the first minute of the day
	from_date = from_date.replace(hour=0, minute=0)

	# Set to_date to the last minute of the day
	to_date = to_date.replace(hour=23, minute=59)

	# If you need to use them as strings later in your code:
	from_date_str = from_date.strftime('%Y-%m-%d %H:%M:%S')
	to_date_str = to_date.strftime('%Y-%m-%d %H:%M:%S')
	
	filters['from_date'] = from_date_str
	filters['to_date'] = to_date_str 
 
	if show_datewise:
		data = get_data_datewise(filters)
		columns = get_columns_date_wise()
	else:
		#print("get_data")
		data = get_data(filters)
		
	return columns, data

def get_columns():
    return [
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},  
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data","width": 250},       
        {"label": _("Opening Qty"), "fieldname": "opening_qty", "fieldtype": "Float", "width": 140},
        {"label": _("Stock Recon"), "fieldname": "stock_recon_qty", "fieldtype": "Float", "width": 140},
        {"label": _("Qty In"), "fieldname": "qty_in", "fieldtype": "Float", "width": 140},
        {"label": _("Qty Out"), "fieldname": "qty_out", "fieldtype": "Float", "width": 140},
        {"label": _("Balance Qty"), "fieldname": "balance_qty", "fieldtype": "Float", "width": 140},
        # Add other columns as needed
    ]
    
def get_columns_date_wise():
    return [
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},  
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data","width": 250}, 
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 120},
        {"label": _("Opening Qty"), "fieldname": "opening_qty", "fieldtype": "Float", "width": 140},
        {"label": _("Stock Recon"), "fieldname": "stock_recon_qty", "fieldtype": "Float", "width": 140},
        {"label": _("Qty In"), "fieldname": "qty_in", "fieldtype": "Float", "width": 140},
        {"label": _("Qty Out"), "fieldname": "qty_out", "fieldtype": "Float", "width": 140},
        {"label": _("Balance Qty"), "fieldname": "balance_qty", "fieldtype": "Float", "width": 140},
        # Add other columns as needed
    ]

def set_dates_for_items(data, transaction_item_dates):
    
	item_code = data.get('item_code')
	# Assuming posting_date is a string in ISO format, convert it to a date object first
	posting_date_time = data.get('posting_date')

	# Now convert the datetime object to a date object (or date string) to remove time part
	posting_date = posting_date_time.date()

	if item_code in transaction_item_dates:
		date_set = transaction_item_dates[item_code]
		if posting_date not in date_set:
			date_set.add(posting_date)
			transaction_item_dates[item_code] = date_set
	else:
		date_set = {posting_date}
		transaction_item_dates[item_code] = date_set

	return transaction_item_dates

def get_dates_for_item(item_code, transaction_item_dates):
    """
    Retrieve the posting dates associated with a specific item code.

    Parameters:
    - item_code (str): The item code for which posting dates are to be retrieved.
    - transaction_item_dates (dict): Dictionary containing item codes and corresponding posting dates.

    Returns:
    - List of posting dates for the specified item code, or None if the item code is not found.
    """
    dates = transaction_item_dates.get(item_code)
    return list(dates) if dates else None
    

def get_data_datewise(filters):
    
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	item = filters.get("item")
	warehouse = filters.get("warehouse")
	show_all = filters.get("show_all")
 
	#print("get_data_datewise")
	#print("from_date")
	#print(from_date)
	#print("to_date")
	#print(to_date)

	# Filter conditions
	item_condition = f" AND item = '{item}'" if item else ""
	warehouse_condition = f" AND warehouse = '{warehouse}'" if warehouse else ""

	# items query
	items_query = f"""
    SELECT DISTINCT sl.item AS item_code, i.item_name
    FROM `tabStock Ledger` sl
    INNER JOIN `tabItem` i ON i.name = sl.item
    WHERE sl.posting_date <= '{to_date}'
    {item_condition}
    {warehouse_condition}
    ORDER BY i.item_name"""
    
	items_data = frappe.db.sql(items_query, as_dict=1)
	
	# Fetch the opening quantity for all items based on the last record's balance quantity
	opening_balance_query = f"""
	SELECT
		sl.item as item_code,
		i.item_name,
		balance_qty as opening_qty
	FROM `tabStock Ledger` sl
	INNER JOIN 	`tabItem` i on i.name = sl.item
	WHERE (item, posting_date) IN (
		SELECT
			item,
			MAX(posting_date) as max_posting_date
		FROM `tabStock Ledger`
		WHERE posting_date < '{from_date}'
			{item_condition}
			{warehouse_condition}
		GROUP BY item order by item
	)
	{item_condition}
	{warehouse_condition}
	"""

	opening_balance_data = frappe.db.sql(opening_balance_query, as_dict=True)
 
	#print("opening_balance_data")
	#print(opening_balance_data)
 
	item_opening_balances = {}
	for opening_balance in opening_balance_data:		
		item_opening_balances[opening_balance.item_code] = opening_balance.opening_qty

	stock_recon_qty_query = f"""
		SELECT item as item_code,posting_date, SUM(balance_qty) as balance_qty,
   		SUM(qty_in) as qty_in,
        SUM(qty_out) as qty_out
		FROM `tabStock Ledger`
		WHERE voucher = 'Stock Reconciliation'
			AND posting_date >= '{from_date}'
			AND posting_date < '{to_date}'
			{item_condition}
			{warehouse_condition}
		GROUP BY item, posting_date order by item,posting_date
	"""

	stock_recon_qty_data = frappe.db.sql(stock_recon_qty_query, as_dict=True)
	transaction_item_dates = {}
	for data in stock_recon_qty_data:     
		transaction_item_dates = set_dates_for_items(data, transaction_item_dates) 
	
	purchase_qty_query = f"""
		SELECT item as item_code,posting_date, SUM(qty_in) as purchase_qty
		FROM `tabStock Ledger`
		WHERE voucher = 'Purchase Invoice'
			AND posting_date >= '{from_date}'
			AND posting_date < '{to_date}'
			{item_condition}
			{warehouse_condition}
		GROUP BY item, posting_date order by item,posting_date
	"""

	purchase_qty_data = frappe.db.sql(purchase_qty_query, as_dict=True)
  
	for data in purchase_qty_data:
		
		transaction_item_dates = set_dates_for_items(data, transaction_item_dates)
  
		# Fetch the purchase return quantity for all items within the specified date range
	purchase_return_qty_query = f"""
		SELECT item as item_code,posting_date, SUM(qty_out) as purchase_return_qty
		FROM `tabStock Ledger`
		WHERE voucher = 'Purchase Return'
			AND posting_date >= '{from_date}'
			AND posting_date < '{to_date}'
			{item_condition}
			{warehouse_condition}
		GROUP BY item, posting_date order by item,posting_date
	"""

	purchase_return_qty_data = frappe.db.sql(purchase_return_qty_query, as_dict=True)
	for data in purchase_return_qty_data:
		transaction_item_dates = set_dates_for_items(data, transaction_item_dates) 

	sales_qty_query = f"""
		SELECT item as item_code,posting_date, SUM(qty_out) as sales_qty
		FROM `tabStock Ledger`
		WHERE voucher = 'Sales Invoice'
			AND posting_date >= '{from_date}'
			AND posting_date < '{to_date}'
			{item_condition}
			{warehouse_condition}
		GROUP BY item, posting_date order by item,posting_date
	""".format(from_date=from_date,to_date=to_date, item_condition=item_condition,warehouse_condition=warehouse_condition)

	sales_qty_data = frappe.db.sql(sales_qty_query, as_dict=True)
 
	for data in sales_qty_data:
		transaction_item_dates = set_dates_for_items(data, transaction_item_dates)
 
	delivery_note_qty_query = f"""
		SELECT item as item_code,posting_date, SUM(qty_out) as sales_qty
		FROM `tabStock Ledger`
		WHERE voucher = 'Delivery Note'
			AND posting_date >= '{from_date}'
			AND posting_date < '{to_date}'
			{item_condition}
			{warehouse_condition}
		GROUP BY item, posting_date order by item,posting_date
	""".format(from_date=from_date,to_date=to_date, item_condition=item_condition,warehouse_condition=warehouse_condition)

	delivery_note_qty_data = frappe.db.sql(delivery_note_qty_query, as_dict=True)
  
	for data in delivery_note_qty_data:
		transaction_item_dates = set_dates_for_items(data, transaction_item_dates)

	# Fetch the sales return quantity for all items within the specified date range
	sales_return_qty_query = f"""
		SELECT item as item_code,posting_date, SUM(qty_in) as sales_return_qty
		FROM `tabStock Ledger`
		WHERE voucher = 'Sales Return'
			AND posting_date >= '{from_date}'
			AND posting_date < '{to_date}'

			{item_condition}
			{warehouse_condition}
		GROUP BY item, posting_date order by item,posting_date
	""".format(from_date=from_date,to_date=to_date, item_condition=item_condition,warehouse_condition=warehouse_condition)

	sales_return_qty_data = frappe.db.sql(sales_return_qty_query, as_dict=True)
	for data in sales_return_qty_data:
		transaction_item_dates = set_dates_for_items(data, transaction_item_dates) 

	transfer_in_qty_query = f"""
	SELECT item as item_code,posting_date, SUM(qty_in) as transfer_in_qty
	FROM `tabStock Ledger`
	WHERE voucher = 'Stock Transfer'
		AND (qty_in > 0)
		AND posting_date >= '{from_date}'
		AND posting_date < '{to_date}'
		{item_condition}
		{warehouse_condition}
	GROUP BY item, posting_date order by item,posting_date
	""".format(from_date=from_date,to_date=to_date, item_condition=item_condition,warehouse_condition=warehouse_condition)

	transfer_in_qty_data = frappe.db.sql(transfer_in_qty_query, as_dict=True)
	for data in transfer_in_qty_data:
		transaction_item_dates = set_dates_for_items(data, transaction_item_dates)  
 
	# Fetch the transfer out quantity for all items within the specified date range
	transfer_out_qty_query = f"""
		SELECT item as item_code,posting_date, SUM(qty_out) as transfer_out_qty
		FROM `tabStock Ledger`
		WHERE voucher = 'Stock Transfer'
			AND qty_out > 0
			AND posting_date >= '{from_date}'
			AND posting_date < '{to_date}'

			{item_condition}
			{warehouse_condition}
		GROUP BY item, posting_date order by item,posting_date
	"""

	transfer_out_qty_data = frappe.db.sql(transfer_out_qty_query, as_dict=True)
	
	for data in transfer_out_qty_data:
		transaction_item_dates = set_dates_for_items(data, transaction_item_dates)
 
	opening_value_exists = False
	transaction_value_exists = False
 
	data = []
	 
	for item_data in items_data:
		
		
		item_code = item_data.item_code
		item_name = item_data.item_name
    
		opening_balance_qty = item_opening_balances[item_code] if item_code in item_opening_balances else 0
		item_row = {"item_code":item_code, "item_name": item_name, "date":from_date, "opening_qty": opening_balance_qty, "closing_qty": 0, "purchase_qty": 0, "purchase_return_qty":0, "sales_qty":0, "sales_return_qty":0, "transfer_in_qty":0, "transfer_out_qty":0, "balance_qty":opening_balance_qty}
		
		transaction_exists = False
  
		date_list = None
  
		# If no transaction wise data exists for all items check for data exists 
		if not transaction_item_dates:
			if(opening_balance_qty !=0 and show_all):
				data.append(item_row)			
			continue

		else:
			# transaction wise data exists but fetching for the transaction dates of the item
			date_list = get_dates_for_item(item_code,transaction_item_dates)
	
			if date_list == None :
				if opening_balance_qty !=0 and show_all:
					data.append(item_row)
				continue
		
		date_list.sort()		
  
		balance_qty = opening_balance_qty
  
		first_row = True
    
		for transaction_date in date_list:
      
			item_row = {"item_code":item_code if first_row else "", "item_name": item_name if first_row else "", "date":None, "opening_qty": balance_qty, "closing_qty": 0, "purchase_qty": 0, "purchase_return_qty":0, "sales_qty":0, "sales_return_qty":0, "transfer_in_qty":0, "transfer_out_qty":0, "balance_qty":balance_qty}		
			       
			item_row["date"] = transaction_date
			opening_qty =  balance_qty			
			stock_recon_qty = 0
			qty_in  = 0
			qty_out = 0

			first_row = False
		
			# For reconciliation it can be qty_in and qty_out both needs to be considered for balance_qty
			for stock_recon_qty_row in stock_recon_qty_data:
       
				ledger_date_str = stock_recon_qty_row.posting_date.strftime('%Y-%m-%d')
				transaction_date_str = transaction_date.strftime('%Y-%m-%d')
       
				if stock_recon_qty_row.item_code == item_code and ledger_date_str == transaction_date_str:
					stock_recon_qty = stock_recon_qty_row.balance_qty
					balance_qty += stock_recon_qty_row.qty_in - stock_recon_qty_row.qty_out
					qty_in += stock_recon_qty_row.qty_in
					qty_out += stock_recon_qty_row.qty_out
					transaction_value_exists = True
					

			# Find the matching purchase_qty_row for the item
			for purchase_qty_row in purchase_qty_data:
       
				ledger_date_str = purchase_qty_row.posting_date.strftime('%Y-%m-%d')
				transaction_date_str = transaction_date.strftime('%Y-%m-%d')
           
				if purchase_qty_row.item_code == item_code and ledger_date_str == transaction_date_str:

					balance_qty += purchase_qty_row.purchase_qty
					qty_in += purchase_qty_row.purchase_qty

					if not transaction_value_exists:
						transaction_value_exists = purchase_qty_row.purchase_qty !=0

			# Find the matching purchase_return_qty_row for the item
			for purchase_return_qty_row in purchase_return_qty_data:
       
				ledger_date_str = purchase_return_qty_row.posting_date.strftime('%Y-%m-%d')
				transaction_date_str = transaction_date.strftime('%Y-%m-%d')
    
				if purchase_return_qty_row.item_code == item_code and ledger_date_str == transaction_date_str:

					balance_qty += (purchase_return_qty_row.purchase_return_qty * -1)
					qty_out += purchase_return_qty_row.purchase_return_qty

					if not transaction_value_exists:
						transaction_value_exists = purchase_return_qty_row.purchase_return_qty !=0
 
			# Find the matching sales_qty_row for the item
			for sales_qty_row in sales_qty_data:
              
				ledger_date_str = sales_qty_row.posting_date.strftime('%Y-%m-%d')
				transaction_date_str = transaction_date.strftime('%Y-%m-%d')
    
				if sales_qty_row.item_code == item_code and ledger_date_str == transaction_date_str:
        
					balance_qty += (sales_qty_row.sales_qty * -1)
					qty_out = qty_out + sales_qty_row.sales_qty					

					if not transaction_value_exists:
						transaction_value_exists = sales_qty_row.sales_qty !=0
      
			# Find the matching sales_qty_row for the item
			for delivery_note_qty_row in delivery_note_qty_data:
              
				ledger_date_str = delivery_note_qty_row.posting_date.strftime('%Y-%m-%d')
				transaction_date_str = transaction_date.strftime('%Y-%m-%d')
    
				if delivery_note_qty_row.item_code == item_code and ledger_date_str == transaction_date_str:
        
					balance_qty += (delivery_note_qty_row.sales_qty * -1)
					qty_out = qty_out + delivery_note_qty_row.sales_qty					

					if not transaction_value_exists:
						transaction_value_exists = delivery_note_qty_row.sales_qty !=0

			# Find the matching sales_return_qty_row for the item
			for sales_return_qty_row in sales_return_qty_data:
       
				ledger_date_str = sales_return_qty_row.posting_date.strftime('%Y-%m-%d')
				transaction_date_str = transaction_date.strftime('%Y-%m-%d')
    
				if sales_return_qty_row.item_code == item_code and ledger_date_str == transaction_date_str:
					balance_qty += sales_return_qty_row.sales_return_qty

					qty_in += sales_return_qty_row.sales_return_qty

					if not transaction_value_exists:
						transaction_value_exists = sales_return_qty_row.sales_return_qty !=0

			for transfer_in_qty_row in transfer_in_qty_data:
		
				ledger_date_str = transfer_in_qty_row.posting_date.strftime('%Y-%m-%d')
				transaction_date_str = transaction_date.strftime('%Y-%m-%d')
		
				if transfer_in_qty_row.item_code == item_code and ledger_date_str == transaction_date_str :
					
					#print("item code matching")
					#print("transfer_in_qty_row.transfer_in_qty")
					#print(transfer_in_qty_row.transfer_in_qty)

					balance_qty += transfer_in_qty_row.transfer_in_qty
					#print("balance_qty")
					#print(balance_qty)
					qty_in += transfer_in_qty_row.transfer_in_qty
					#print("qty_in")
					#print(qty_in)

					if not transaction_value_exists:
						transaction_value_exists = transfer_in_qty_row.transfer_in_qty !=0

			# Find the matching transfer_out_qty_row for the item
			for transfer_out_qty_row in transfer_out_qty_data:
       
				ledger_date_str = transfer_out_qty_row.posting_date.strftime('%Y-%m-%d')
				transaction_date_str = transaction_date.strftime('%Y-%m-%d')
    
				if transfer_out_qty_row.item_code == item_code and ledger_date_str == transaction_date_str:

					balance_qty += (transfer_out_qty_row.transfer_out_qty * -1)
					qty_out += transfer_out_qty_row.transfer_out_qty

					if not transaction_value_exists:
						transaction_value_exists = transfer_out_qty_row.transfer_out_qty !=0

			item_row["opening_qty"] = opening_qty
			item_row["stock_recon_qty"] = stock_recon_qty
			item_row["qty_in"] = qty_in
			item_row["qty_out"] = qty_out
			item_row["balance_qty"] = balance_qty
			
			data.append(item_row)
		      
	return data

def get_data(filters):
    
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	item = filters.get("item")
	warehouse = filters.get("warehouse")
	show_all = filters.get("show_all")
 
	#print("get_data")
	#print("from_date")
	#print(from_date)
	#print("to_date")
	#print(to_date)

	# Filter conditions
	item_condition = f" AND item = '{item}'" if item else ""
	warehouse_condition = f" AND warehouse = '{warehouse}'" if warehouse else ""

	# items query
	items_query = f"""
    SELECT DISTINCT sl.item AS item_code, i.item_name
    FROM `tabStock Ledger` sl
    INNER JOIN `tabItem` i ON i.name = sl.item
    WHERE sl.posting_date <= '{to_date}'
    {item_condition}
    {warehouse_condition}
    ORDER BY i.item_name"""
    
	items_data = frappe.db.sql(items_query, as_dict=1)
 
	#print("items_data")
	#print(items_data)
	
	# Fetch the opening quantity for all items based on the last record's balance quantity
	opening_balance_query = f"""
	SELECT
		sl.item as item_code,
		i.item_name,
		balance_qty as opening_qty
	FROM `tabStock Ledger` sl
	INNER JOIN 	`tabItem` i on i.name = sl.item
	WHERE (item, posting_date) IN (
		SELECT
			item,
			MAX(posting_date) as max_posting_date
		FROM `tabStock Ledger`
		WHERE posting_date < '{from_date}'
			{item_condition}
			{warehouse_condition}
		GROUP BY item order by item
	)
	{item_condition}
	{warehouse_condition}
	"""

	opening_balance_data = frappe.db.sql(opening_balance_query, as_dict=True)
 
	#print("opening_balance_data")
	#print(opening_balance_data)
 
	item_opening_balances = {}
	for opening_balance in opening_balance_data:		
		item_opening_balances[opening_balance.item_code] = opening_balance.opening_qty

	stock_recon_qty_query = f"""
		SELECT item as item_code,posting_date, SUM(balance_qty) as balance_qty,
   		SUM(qty_in) as qty_in,
        SUM(qty_out) as qty_out
		FROM `tabStock Ledger`
		WHERE voucher = 'Stock Reconciliation'
			AND posting_date >= '{from_date}'
			AND posting_date < '{to_date}'
			{item_condition}
			{warehouse_condition}
		GROUP BY item, posting_date order by item,posting_date
	"""

	stock_recon_qty_data = frappe.db.sql(stock_recon_qty_query, as_dict=True)	
	
	purchase_qty_query = f"""
		SELECT item as item_code,posting_date, SUM(qty_in) as purchase_qty
		FROM `tabStock Ledger`
		WHERE voucher = 'Purchase Invoice'
			AND posting_date >= '{from_date}'
			AND posting_date < '{to_date}'
			{item_condition}
			{warehouse_condition}
		GROUP BY item, posting_date order by item,posting_date
	"""

	purchase_qty_data = frappe.db.sql(purchase_qty_query, as_dict=True)
  
	for data in purchase_qty_data:
		
		transaction_item_dates = set_dates_for_items(data, transaction_item_dates)
  
		# Fetch the purchase return quantity for all items within the specified date range
	purchase_return_qty_query = f"""
		SELECT item as item_code,posting_date, SUM(qty_out) as purchase_return_qty
		FROM `tabStock Ledger`
		WHERE voucher = 'Purchase Return'
			AND posting_date >= '{from_date}'
			AND posting_date < '{to_date}'
			{item_condition}
			{warehouse_condition}
		GROUP BY item, posting_date order by item,posting_date
	"""

	purchase_return_qty_data = frappe.db.sql(purchase_return_qty_query, as_dict=True)
	
	sales_qty_query = f"""
		SELECT item as item_code,posting_date, SUM(qty_out) as sales_qty
		FROM `tabStock Ledger`
		WHERE voucher = 'Sales Invoice'
			AND posting_date >= '{from_date}'
			AND posting_date < '{to_date}'
			{item_condition}
			{warehouse_condition}
		GROUP BY item, posting_date order by item,posting_date
	""".format(from_date=from_date,to_date=to_date, item_condition=item_condition,warehouse_condition=warehouse_condition)

	sales_qty_data = frappe.db.sql(sales_qty_query, as_dict=True)
 	
	delivery_note_qty_query = f"""
		SELECT item as item_code,posting_date, SUM(qty_out) as sales_qty
		FROM `tabStock Ledger`
		WHERE voucher = 'Delivery Note'
			AND posting_date >= '{from_date}'
			AND posting_date < '{to_date}'
			{item_condition}
			{warehouse_condition}
		GROUP BY item, posting_date order by item,posting_date
	""".format(from_date=from_date,to_date=to_date, item_condition=item_condition,warehouse_condition=warehouse_condition)

	delivery_note_qty_data = frappe.db.sql(delivery_note_qty_query, as_dict=True)
  
	
	# Fetch the sales return quantity for all items within the specified date range
	sales_return_qty_query = f"""
		SELECT item as item_code,posting_date, SUM(qty_in) as sales_return_qty
		FROM `tabStock Ledger`
		WHERE voucher = 'Sales Return'
			AND posting_date >= '{from_date}'
			AND posting_date < '{to_date}'

			{item_condition}
			{warehouse_condition}
		GROUP BY item, posting_date order by item,posting_date
	""".format(from_date=from_date,to_date=to_date, item_condition=item_condition,warehouse_condition=warehouse_condition)

	sales_return_qty_data = frappe.db.sql(sales_return_qty_query, as_dict=True)
	
	transfer_in_qty_query = f"""
	SELECT item as item_code,posting_date, SUM(qty_in) as transfer_in_qty
	FROM `tabStock Ledger`
	WHERE voucher = 'Stock Transfer'
		AND (qty_in > 0)
		AND posting_date >= '{from_date}'
		AND posting_date < '{to_date}'
		{item_condition}
		{warehouse_condition}
	GROUP BY item, posting_date order by item,posting_date
	""".format(from_date=from_date,to_date=to_date, item_condition=item_condition,warehouse_condition=warehouse_condition)

	transfer_in_qty_data = frappe.db.sql(transfer_in_qty_query, as_dict=True)
	 
	# Fetch the transfer out quantity for all items within the specified date range
	transfer_out_qty_query = f"""
		SELECT item as item_code,posting_date, SUM(qty_out) as transfer_out_qty
		FROM `tabStock Ledger`
		WHERE voucher = 'Stock Transfer'
			AND qty_out > 0
			AND posting_date >= '{from_date}'
			AND posting_date < '{to_date}'

			{item_condition}
			{warehouse_condition}
		GROUP BY item, posting_date order by item,posting_date
	"""

	transfer_out_qty_data = frappe.db.sql(transfer_out_qty_query, as_dict=True)
	
	transaction_value_exists = False
 
	data = []
 	 
	for item_data in items_data:
		
		
		item_code = item_data.item_code
		item_name = item_data.item_name
    
		opening_balance_qty = item_opening_balances[item_code] if item_code in item_opening_balances else 0
		
		   
		# date_list = get_dates_for_item(item_code,transaction_item_dates)
  
		# if date_list == None :
		# 	if opening_balance_qty !=0:
		# 		data.append(item_row)
		# 	continue
		
		# date_list.sort()		
  
		balance_qty = opening_balance_qty
  
		first_row = True
          
		item_row = {"item_code":item_code,"item_name": item_name if first_row else "","opening_qty": balance_qty, "closing_qty": 0, "purchase_qty": 0, "purchase_return_qty":0, "sales_qty":0, "sales_return_qty":0, "transfer_in_qty":0, "transfer_out_qty":0, "balance_qty":balance_qty}		
		
		opening_qty =  balance_qty			
		stock_recon_qty = 0
		qty_in  = 0
		qty_out = 0

		first_row = False
	
		# For reconciliation it can be qty_in and qty_out both needs to be considered for balance_qty
		for stock_recon_qty_row in stock_recon_qty_data:
		
			if stock_recon_qty_row.item_code == item_code:
				stock_recon_qty = stock_recon_qty_row.balance_qty
				balance_qty += stock_recon_qty_row.qty_in - stock_recon_qty_row.qty_out
				qty_in += stock_recon_qty_row.qty_in
				qty_out += stock_recon_qty_row.qty_out
				transaction_value_exists = True
				

		# Find the matching purchase_qty_row for the item
		for purchase_qty_row in purchase_qty_data:
			
			if purchase_qty_row.item_code == item_code:

				balance_qty += purchase_qty_row.purchase_qty
				qty_in += purchase_qty_row.purchase_qty

				if not transaction_value_exists:
					transaction_value_exists = purchase_qty_row.purchase_qty !=0

		# Find the matching purchase_return_qty_row for the item
		for purchase_return_qty_row in purchase_return_qty_data:
	
			if purchase_return_qty_row.item_code == item_code :

				balance_qty += (purchase_return_qty_row.purchase_return_qty * -1)
				qty_out += purchase_return_qty_row.purchase_return_qty

				if not transaction_value_exists:
					transaction_value_exists = purchase_return_qty_row.purchase_return_qty !=0

		# Find the matching sales_qty_row for the item
		for sales_qty_row in sales_qty_data:
			
			
			if sales_qty_row.item_code == item_code:
	
				balance_qty += (sales_qty_row.sales_qty * -1)
				qty_out = qty_out + sales_qty_row.sales_qty					

				if not transaction_value_exists:
					transaction_value_exists = sales_qty_row.sales_qty !=0
	
		# Find the matching sales_qty_row for the item
		for delivery_note_qty_row in delivery_note_qty_data:
			
			
			if delivery_note_qty_row.item_code == item_code:
	
				balance_qty += (delivery_note_qty_row.sales_qty * -1)
				qty_out = qty_out + delivery_note_qty_row.sales_qty					

				if not transaction_value_exists:
					transaction_value_exists = delivery_note_qty_row.sales_qty !=0

		# Find the matching sales_return_qty_row for the item
		for sales_return_qty_row in sales_return_qty_data:
	
			
			if sales_return_qty_row.item_code == item_code:
				balance_qty += sales_return_qty_row.sales_return_qty

				qty_in += sales_return_qty_row.sales_return_qty

				if not transaction_value_exists:
					transaction_value_exists = sales_return_qty_row.sales_return_qty !=0

		for transfer_in_qty_row in transfer_in_qty_data:	
			
			if transfer_in_qty_row.item_code == item_code :
				
				#print("item code matching")
				#print("transfer_in_qty_row.transfer_in_qty")
				#print(transfer_in_qty_row.transfer_in_qty)

				balance_qty += transfer_in_qty_row.transfer_in_qty
				#print("balance_qty")
				#print(balance_qty)
				qty_in += transfer_in_qty_row.transfer_in_qty
				#print("qty_in")
				#print(qty_in)

				if not transaction_value_exists:
					transaction_value_exists = transfer_in_qty_row.transfer_in_qty !=0

		# Find the matching transfer_out_qty_row for the item
		for transfer_out_qty_row in transfer_out_qty_data:
	
			if transfer_out_qty_row.item_code == item_code:

				balance_qty += (transfer_out_qty_row.transfer_out_qty * -1)
				qty_out += transfer_out_qty_row.transfer_out_qty

				if not transaction_value_exists:
					transaction_value_exists = transfer_out_qty_row.transfer_out_qty !=0
     
			item_row["opening_qty"] = opening_qty
			item_row["stock_recon_qty"] = stock_recon_qty
			item_row["qty_in"] = qty_in
			item_row["qty_out"] = qty_out
			item_row["balance_qty"] = balance_qty
      
		if qty_in != 0 or qty_out !=0:  
			data.append(item_row)
		elif show_all and opening_balance_qty!=0:
			data.append(item_row)	
	      
	return data



