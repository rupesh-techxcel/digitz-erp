# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):

	columns = get_columns()

	if(filters.get("show_current_balance_qty", False) == False):
		columns = [col for col in columns if col['fieldname'] != 'current_balance_qty']
  
	data = get_data(filters)
	return columns, data

def get_data(filters):
	# Start with the SELECT and FROM clauses, which are fixed
 
	sql_query ="""
	SELECT
		i.name AS item,
		i.item_name,
		w.name AS warehouse,
		COALESCE(i.base_unit) AS unit		
	FROM
		`tabItem` i
	CROSS JOIN `tabWarehouse` w ORDER BY i.item_name,w.warehouse
	"""
	# sql_query = """
	# SELECT
	# 	i.name AS item,
	# 	i.item_name,
	# 	w.name AS warehouse,
	# 	COALESCE(sl.unit, i.base_unit) AS unit,
	# 	SUM(COALESCE(sl.qty_in, 0)) AS qty_in,
	# 	SUM(COALESCE(sl.qty_out, 0)) AS qty_out,
	# 	SUM(COALESCE(sl.qty_in, 0)) - SUM(COALESCE(sl.qty_out, 0)) AS balance_qty
	# FROM
	# 	`tabItem` i
	# CROSS JOIN `tabWarehouse` w
 
	# LEFT JOIN
	# 	`tabStock Ledger` sl ON sl.item = i.name and sl.warehouse = w.name
	# """

	# # Initialize the list to hold JOIN conditions and parameters for the query
	# join_conditions = []
	# parameters = []

	# # Add conditions to JOIN based on provided filters
	# if filters.get('from_date'):
	# 	join_conditions.append("sl.posting_date >= %s")
	# 	parameters.append(filters['from_date'])

	# if filters.get('to_date'):
	# 	join_conditions.append("sl.posting_date <= %s")
	# 	parameters.append(filters['to_date'])
		
	# if filters.get('item'):
	# 	join_conditions.append("i.name = %s")
	# 	parameters.append(filters['item'])

	# if filters.get('warehouse'):
	# 	join_conditions.append("sl.warehouse = %s")
	# 	parameters.append(filters['warehouse'])

	# if join_conditions:
	# 	sql_query += " AND " + " AND ".join(join_conditions)

	# sql_query += """
	# GROUP BY
	# 	i.name, sl.warehouse, COALESCE(sl.unit, i.base_unit)
	# ORDER BY
	# 	i.name, sl.posting_date
	# """

	# Execute the query
	# data = frappe.db.sql(sql_query, parameters, as_dict=True)
 
	data = frappe.db.sql(sql_query, as_dict=True)
 
	for dl in data:
		
		from_date = filters.get('from_date')
		to_date = filters.get('to_date')
   
		result = frappe.db.sql("""
		SELECT SUM(COALESCE(sl.qty_in, 0)) AS qty_in,
		SUM(COALESCE(sl.qty_out, 0)) AS qty_out,
  		SUM(COALESCE(sl.qty_in, 0))- SUM(COALESCE(sl.qty_out, 0)) AS balance_qty FROM `tabStock Ledger` sl WHERE sl.item = %s AND sl.warehouse = %s AND sl.posting_date >= %s AND sl.posting_date <=%s
		ORDER BY sl.posting_date DESC
		LIMIT 1
	""", (dl['item'], dl['warehouse'], from_date,to_date), as_dict=True)
  
		qty_in = result[0]['qty_in'] if result else 0
		qty_out = result[0]['qty_out'] if result else 0
		balance_qty = result[0]['balance_qty'] if result else 0
  
		qty_in = qty_in if qty_in else 0
		qty_out = qty_out if qty_in else 0
		balance_qty = balance_qty if balance_qty else 0
  
		result = frappe.db.sql("""SELECT stock_qty from `tabStock Balance` where item=%s and warehouse=%s """, (dl["item"], dl["warehouse"]), as_dict = True)
  
		current_balance_qty = result[0]['stock_qty'] if result else 0
  
		dl.update({
				"qty_in": round(qty_in, 2),
				"qty_out": round(qty_out, 2),
				"balance_qty": round(balance_qty,2),
				"current_balance_qty": round(current_balance_qty,2)
			})
	
	for dl in data:
		
		if filters.get('from_date'):
			from_date = filters.get('from_date')
   
			print(dl['item'])
			print(dl['warehouse'])
   
			result = frappe.db.sql("""
            SELECT balance_qty FROM `tabStock Ledger` sl
            WHERE sl.item = %s AND sl.warehouse = %s AND sl.posting_date < %s
            ORDER BY sl.posting_date DESC
            LIMIT 1
        """, (dl['item'], dl['warehouse'], from_date), as_dict=True)
   
   
			# When the record do not have any value in stock_ledger dl[warehouse] is none so handling it here
			# if(dl['warehouse'] == None and not filters.get('warehouse')):
			# 	frappe.throw("Please select warehouse to get the result in this date range")
			# elif dl['warehouse'] == None:
			# 	dl['warehouse'] = filters.get('warehouse')


			# Execute the SQL query to get the opening quantity
			result = frappe.db.sql("""
            SELECT balance_qty FROM `tabStock Ledger` sl
            WHERE sl.item = %s AND sl.warehouse = %s AND sl.posting_date < %s
            ORDER BY sl.posting_date DESC
            LIMIT 1
        """, (dl['item'], dl['warehouse'], from_date), as_dict=True)

			print(result)
   
			# Extract balance_qty from the result if available, otherwise default to 0
			opening_qty = result[0]['balance_qty'] if result else 0
   
			# Update the dictionary with the opening quantity and adjusted balance quantity
			dl.update({
				"opening_qty": round(opening_qty, 2),
				"balance_qty": round(dl['balance_qty'] + opening_qty, 2)
			})
     
	
				
	filtered_data = []
 
	print(data)

	# Iterate over each record and filter based on your conditions
	for dl in data:
		# Assume opening_qty has been calculated and added to dl, and balance_qty has been updated accordingly
  
		if filters.get('item') and (dl.get('item') != filters.get('item')):
			continue

		if filters.get('warehouse') and (dl.get('warehouse') != filters.get('warehouse')):
			continue

		# Check if any of the required fields have a non-zero value
		if dl.get('qty_in', 0) != 0 or dl.get('qty_out', 0) != 0 or dl.get('opening_qty', 0) != 0 or dl.get('balance_qty', 0) != 0:
			filtered_data.append(dl)

	# Return the filtered list of records
	return filtered_data
	

def get_columns():
	return [
     	{		
			"fieldname": "item",
			"fieldtype": "Link",
			"label": "Item",
			"options": "Item",
			"width": 100,	
		},
		{		
			"fieldname": "item_name",
			"fieldtype": "Link",
			"label": "Item Name",
			"options": "Item",
			"width": 200,	
		},
  		{		
			"fieldname": "unit",
			"fieldtype": "Link",   
			"label": "Unit",			
			"options": "Unit",
			"width": 80,	
		},
		{		
			"fieldname": "warehouse",
			"fieldtype": "Link",   
			"label": "W/H",
			"options": "Warehouse",
			"width": 100,	
		},
		{		
			"fieldname": "opening_qty",
			"fieldtype": "Data",   
			"label": "Opening Qty",			
			"width": 100,	
		},
		{		
			"fieldname": "qty_in",
			"fieldtype": "Data",   
			"label": "Qty In",			
			"width": 100,	
		},
		{		
			"fieldname": "qty_out",
			"fieldtype": "Data",
			"label": "Qty Out",						
			"width": 80,	
		},  		
		{		
			"fieldname": "balance_qty",
			"fieldtype": "Data",   
			"label": "Balance Qty",			
			"width": 80,	
		},
		{		
			"fieldname": "current_balance_qty",
			"fieldtype": "Data",   
			"label": "Current Balance Qty",			
			"width": 80,	
		}
	]
