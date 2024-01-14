# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):

	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_data(filters):

	data = ""

	# Constructing the base query
	base_query = """
		SELECT
			sl.item as item_code,
			i.item_name as item,
			sl.voucher,
			sl.voucher_no,
			posting_date,
			warehouse,
			qty_in,
			round(incoming_rate, 2) as 'incoming_rate',
			sl.unit as 'unit',
			round(qty_out, 2) as 'qty_out',
			round(outgoing_rate, 2) as 'outgoing_rate',
			round(valuation_rate, 2) as 'valuation_rate',
			round(change_in_stock_value, 2) as change_in_stock_value,
			round(balance_qty, 2) as 'balance_qty',
			round(balance_value, 2) as 'balance_value'
		FROM
			`tabStock Ledger` sl
		INNER JOIN
			`tabItem` i ON i.name = sl.item
	"""
	print("filters")
	print(filters)
	print("filters.get('item'")
	print(filters.get('item'))

	# Constructing the WHERE clause based on filters
	where_clause = ""
	if filters.get('item'):
		where_clause += f" AND sl.item = '{filters['item']}'"
	if filters.get('from_date') and filters.get('to_date'):
		where_clause += f" AND sl.posting_date BETWEEN '{filters['from_date']} 00:00:00' AND '{filters['to_date']} 23:59:59'"
	if filters.get('warehouse'):
		where_clause += f" AND sl.warehouse = '{filters['warehouse']}'"

	print("where_clause")    
	print(where_clause)

	# Finalizing the SQL query
	sql = f"{base_query} WHERE 1=1 {where_clause} ORDER BY i.item_name, sl.posting_date"

	print("sql")
	print(sql)

	# Executing the query
	data = frappe.db.sql(sql, as_dict=True)

	print("data")
	print(data)

	# Processing the data
	last_item = ""
	last_warehouse = ""
	last_qty = 0

	for dl in data:
		
		if not (dl.item == last_item and dl.warehouse == last_warehouse):
			sql ="""
				SELECT balance_qty
				FROM `tabStock Ledger`
				WHERE item = '{item}'
				AND warehouse = '{warehouse}'
				AND posting_date < '{date}'
				ORDER BY posting_date DESC
				LIMIT 1
				""".format(item=dl.item_code,warehouse= dl.warehouse, date=dl.posting_date)
    
			print(sql)
   
			result = frappe.db.sql(sql)

			opening_qty = result[0][0] if result and result[0] else 0

			dl.update({"opening_qty": round(opening_qty, 2)} if opening_qty else {"opening_qty": 0})
   
			print("opening_qty")
			print(opening_qty)			
		else:
			dl.update({"opening_qty": round(last_qty, 2)})

		last_item = dl.item
		last_qty = dl.balance_qty
		last_warehouse = dl.warehouse

	return data

def get_columns():
	return [
		{
			"fieldname": "item",
			"fieldtype": "Link",
			"label": "Item",
			"options": "Item",
			"width": 200,
		},
  		{
			"fieldname": "voucher",
			"fieldtype": "Link",
			"label": "Voucher Type",
			"options": "DocType",
			"width": 100,
		},
    	{
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"label": "Voucher No",
			"options": "voucher",
			"width": 100,
		},
     	{
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"label": "Date",
			"width": 100,
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
			"fieldname": "incoming_rate",
			"fieldtype": "Data",
			"label": "Incoming Rate",
			"width": 100,
		},
        {
			"fieldname": "unit",
			"fieldtype": "Link",
			"label": "Unit",
			"options": "Unit",
			"width": 80,
		},
        {
			"fieldname": "qty_out",
			"fieldtype": "Data",
			"label": "Qty Out",
			"width": 80,
		},
        {
			"fieldname": "outgoing_rate",
			"fieldtype": "Data",
			"label": "Outgoing Rate",
			"width": 80,
		},
        {
			"fieldname": "valuation_rate",
			"fieldtype": "Data",
			"label": "Valuation Rate",
			"width": 80,
		},
        {
			"fieldname": "change_in_stock_value",
			"fieldtype": "Data",
			"label": "Change In Stock Value",
			"width": 80,
		},
        {
			"fieldname": "balance_qty",
			"fieldtype": "Data",
			"label": "Balance Qty",
			"width": 80,
		},       
        {
			"fieldname": "balance_value",
			"fieldtype": "Data",
			"label": "Balance Value",
			"width": 80,
		},
	]
