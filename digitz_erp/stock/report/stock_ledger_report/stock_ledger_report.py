# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):

	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_data(filters):
	data = ""	
	if(filters.get('item'))  and  filters.get('from_date') and filters.get('to_date') and filters.get('warehouse'):
		data = frappe.db.sql(""" SELECT sl.item, sl.voucher, sl.voucher_no,posting_date,warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl where sl.item = '{0}' and warehouse='{1}' and sl.posting_date BETWEEN '{2}' and '{3}' """.format(filters.get('item'),filters.get('warehouse'),filters.get('from_date'),filters.get('to_date')),as_dict=True)
	
	elif(filters.get('item'))  and  filters.get('from_date') and filters.get('to_date'):
		data = frappe.db.sql(""" SELECT sl.item, sl.voucher, sl.voucher_no,posting_date,warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl where sl.item = '{0}'  and sl.posting_date BETWEEN '{1}' and '{2}' """.format(filters.get('item'),filters.get('from_date'),filters.get('to_date')),as_dict=True)
  	
	elif(filters.get('item'))  and  filters.get('warehouse'):
		data = frappe.db.sql(""" SELECT sl.item, sl.voucher, sl.voucher_no,posting_date,warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl where sl.item = '{0}'  and sl.warehouse='{1}'""".format(filters.get('item'),filters.get('warehouse')),as_dict=True)
  
	elif(filters.get('from_date') and filters.get('to_date')):
		data = frappe.db.sql(""" SELECT sl.item, sl.voucher, sl.voucher_no, posting_date, warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl where sl.posting_date BETWEEN '{0}' and '{1}' """.format(filters.get('from_date'),filters.get('to_date')),as_dict=True)
	elif(filters.get('from_date')):
		data = frappe.db.sql(""" SELECT sl.item,sl.voucher, sl.voucher_no,posting_date, warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl where sl.posting_date >= '{0}' """.format(filters.get('from_date')),as_dict=True)  
	elif (filters.get('item')):
		data = frappe.db.sql(""" SELECT sl.item,sl.voucher, sl.voucher_no, posting_date, warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl where sl.item = '{0}'""".format(filters.get('item')),as_dict=True)
	elif (filters.get('warehouse')):
		data = frappe.db.sql(""" SELECT sl.item,sl.voucher, sl.voucher_no, posting_date, warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl where sl.warehouse = '{0}'""".format(filters.get('warehouse')),as_dict=True)
	else:
		data = frappe.db.sql(""" SELECT sl.item,sl.voucher, sl.voucher_no, posting_date, warehouse,qty_in, round(incoming_rate,2)  as 'incoming_rate', sl.unit  as 'unit', round(qty_out,2)  as 'qty_out', round(outgoing_rate,2)  as 'outgoing_rate', round(valuation_rate,2) as 'valuation_rate', round(balance_qty,2)  as 'balance_qty', round(balance_value,2) as 'balance_value' FROM `tabStock Ledger` sl """,as_dict=True)
	
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
 