# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):

	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_data(filters):
    
	data = ""	
	# Item, from_date, to_date, warehouse
	if(filters.get('item')  and  filters.get('from_date') and filters.get('to_date') and filters.get('warehouse')):
		data = frappe.db.sql(""" SELECT sl.item, sl.voucher, sl.voucher_no,posting_date,warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl where sl.item = '{0}' and warehouse='{1}' and sl.posting_date BETWEEN '{2}' and '{3}' order by sl.item, posting_date """.format(filters.get('item'),filters.get('warehouse'),filters.get('from_date'),filters.get('to_date')),as_dict=True)
	# Item, from_date, to_date
	elif(filters.get('item')  and  filters.get('from_date') and filters.get('to_date') and not( filters.get('warehouse'))):
		data = frappe.db.sql(""" SELECT sl.item, sl.voucher, sl.voucher_no,posting_date,warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl where sl.item = '{0}'  and sl.posting_date BETWEEN '{1}' and '{2}' order by sl.item, posting_date """.format(filters.get('item'),filters.get('from_date'),filters.get('to_date')),as_dict=True)
	# Item, warehouse
	elif(filters.get('item')  and  filters.get('warehouse') and not(filters.get('from_date') and filters.get('to_date'))):
		data = frappe.db.sql(""" SELECT sl.item, sl.voucher, sl.voucher_no,posting_date,warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl where sl.item = '{0}'  and sl.warehouse='{1}' order by sl.item, posting_date """.format(filters.get('item'),filters.get('warehouse')),as_dict=True)
	# from_date, to_date
	elif(filters.get('from_date') and filters.get('to_date') and not(filters.get('item'))  and not(filters.get('warehouse'))):
		data = frappe.db.sql(""" SELECT sl.item, sl.voucher, sl.voucher_no, posting_date, warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl where sl.posting_date BETWEEN '{0}' and '{1}' order by sl.item, posting_date  """.format(filters.get('from_date'),filters.get('to_date')),as_dict=True)
  # from_date
	elif(filters.get('from_date') and not(filters.get('item') and not(filters.get('warehouse') and not(filters('to_date'))))):
		data = frappe.db.sql(""" SELECT sl.item,sl.voucher, sl.voucher_no,posting_date, warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl where sl.posting_date >= '{0}' order by sl.item, posting_date """.format(filters.get('from_date')),as_dict=True)  
  # Item
	elif (filters.get('item') and not(filters.get('warehouse')) and not(filters.get('from_date') and filters.get('to_date'))) :
		data = frappe.db.sql(""" SELECT sl.item,sl.voucher, sl.voucher_no, posting_date, warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl where sl.item = '{0}' order by sl.item, posting_date """.format(filters.get('item')),as_dict=True)
  #warehouse
	elif (filters.get('warehouse') and not(filters.get('item') and not(filters.get('from_date') and filters.get('to_date'))) ):
		data = frappe.db.sql(""" SELECT sl.item,sl.voucher, sl.voucher_no, posting_date, warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl where sl.warehouse = '{0}' order by sl.item, posting_date """.format(filters.get('warehouse')),as_dict=True)
	else:
		data = frappe.db.sql(""" SELECT sl.item,sl.voucher, sl.voucher_no, posting_date, warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl order by sl.item, posting_date  """,as_dict=True)
	
	last_item = ""
	last_warehouse = ""
	last_qty = 0
	for dl in data:
		if not(dl.item == last_item and dl.warehouse == last_warehouse):
			print(dl.item)
			print(dl.warehouse)

			opening_qty = frappe.get_value('Stock Ledger',{'item':dl.item,'warehouse':dl.warehouse, 'posting_date':['<', dl.posting_date]}, 'balance_qty')
			if(opening_qty):
				dl.update({"opening_qty":opening_qty})
			else:
				dl.update({"opening_qty":0})
    
			print(opening_qty)
		else:
			dl.update({"opening_qty":last_qty})

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
			"fieldtype": "Data",
			"label": "Voucher Type",			
			"width": 100,	
		},
    	{		
			"fieldname": "voucher_no",
			"fieldtype": "Data",
			"label": "Voucher No",			
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
 