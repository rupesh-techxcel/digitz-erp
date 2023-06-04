# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):

	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_data(filters):
    
	data = ""
	# item, dates, w/h
	if(filters.get('item')  and  filters.get('from_date') and filters.get('to_date') and filters.get('warehouse')):    
		print("case 1")
		data=frappe.db.sql(""" SELECT sl.item, warehouse,unit, sum(qty_in) as 'qty_in',sum(qty_out) as 'qty_out', sum(qty_in)- sum(qty_out) as 'balance_qty' FROM `tabStock Ledger` sl where sl.item = '{0}' and warehouse='{1}' and sl.posting_date BETWEEN '{2}' and '{3}' group by sl.item, sl.warehouse, sl.unit  order by sl.item, posting_date """.format(filters.get('item'),filters.get('warehouse'),filters.get('from_date'),filters.get('to_date')),as_dict=True)
	# item,dates
	elif (filters.get('item')  and  filters.get('from_date') and filters.get('to_date') and not filters.get('warehouse')):    
		print("case 2")
		data=frappe.db.sql(""" SELECT sl.item, warehouse, unit, sum(qty_in) as 'qty_in',sum(qty_out) as 'qty_out', sum(qty_in)- sum(qty_out) as 'balance_qty' FROM `tabStock Ledger` sl where sl.item = '{0}' and sl.posting_date BETWEEN '{1}' and '{2}' group by sl.item, sl.warehouse,sl.unit order by sl.item, posting_date """.format(filters.get('item'),filters.get('from_date'),filters.get('to_date')),as_dict=True)
	# item,w/h
	elif (filters.get('item')  and not(filters.get('from_date') and filters.get('to_date')) and filters.get('warehouse')):    
		print("case 3")
		data=frappe.db.sql(""" SELECT sl.item, warehouse,unit, sum(qty_in) as 'qty_in',sum(qty_out) as 'qty_out', sum(qty_in)- sum(qty_out) as 'balance_qty' FROM `tabStock Ledger` sl where sl.item = '{0}' and warehouse='{1}' group by sl.item, sl.warehouse,sl.unit order by sl.item, posting_date """.format(filters.get('item'),filters.get('warehouse')),as_dict=True)
	#   item 
	elif(not(filters.get('item'))  and not(filters.get('from_date') and filters.get('to_date')) and not(filters.get('warehouse'))):    
		print("case 4")
		data=frappe.db.sql(""" SELECT sl.item, warehouse,unit,sum(qty_in) as 'qty_in',sum(qty_out) as 'qty_out', sum(qty_in)- sum(qty_out) as 'balance_qty' FROM `tabStock Ledger` sl where sl.item='{0}' group by sl.item, sl,.warehouse, sl.unit order by sl.item, posting_date """.format(filters.get('item')),as_dict=True)
  	# w/h, from_date, to_date
	if(not(filters.get('item'))  and  filters.get('from_date') and filters.get('to_date') and filters.get('warehouse')):    
		print("case 5")
		data=frappe.db.sql(""" SELECT sl.item, warehouse,unit, sum(qty_in) as 'qty_in',sum(qty_out) as 'qty_out', sum(qty_in)- sum(qty_out) as 'balance_qty' FROM `tabStock Ledger` sl where sl.item = '{0}' and warehouse='{1}' and sl.posting_date BETWEEN '{2}' and '{3}' group by sl.item, sl.warehouse,sl.unit order by sl.item, posting_date """.format(filters.get('item'),filters.get('warehouse'),filters.get('from_date'),filters.get('to_date')),as_dict=True)
	# warehouse
	if(not (filters.get('item'))  and not(filters.get('from_date') and filters.get('to_date')) and filters.get('warehouse')):    
		print("case 6")
		data=frappe.db.sql(""" SELECT sl.item, warehouse,unit, sum(qty_in) as 'qty_in',sum(qty_out) as 'qty_out', sum(qty_in)- sum(qty_out) as 'balance_qty' FROM `tabStock Ledger` sl where sl.item = '{0}' and warehouse='{1}' and sl.posting_date BETWEEN '{2}' and '{3}' group by sl.item, sl.warehouse, sl.unit order by sl.item, posting_date """.format(filters.get('item'),filters.get('warehouse'),filters.get('from_date'),filters.get('to_date')),as_dict=True)  
	else:
		print("case 7")
		data=frappe.db.sql(""" SELECT sl.item, warehouse,unit,sum(qty_in) as 'qty_in',sum(qty_out) as 'qty_out', sum(qty_in)- sum(qty_out) as 'balance_qty' FROM `tabStock Ledger` sl group by sl.item, sl.warehouse,sl.unit order by sl.item, posting_date """,as_dict=True)  
		
	last_item = ""
	last_qty = 0
	for dl in data:		
		if(filters.get('from_date')):
			from_date = filters.get('from_date')
			opening_qty = frappe.get_value('Stock Ledger',{'item':dl.item,'warehouse':dl.warehouse, 'posting_date':['<', from_date]}, 'balance_qty',order_by='posting_date')
			if(opening_qty):
				dl.update({"opening_qty":opening_qty})
			else:
				dl.update({"opening_qty":0})
	
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
			"fieldname": "unit",
			"fieldtype": "Link",   
			"label": "Unit",			
			"options": "Unit",
			"width": 80,	
		},
		{		
			"fieldname": "balance_qty",
			"fieldtype": "Data",   
			"label": "Balance Qty",			
			"width": 80,	
		}
	]
