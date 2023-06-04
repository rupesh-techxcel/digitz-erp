// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock Movement Report"] = {
	"filters": [
		{		
			"fieldname": "item",
			"fieldtype": "Link",
			"label": "Item",
			"options": "Item",
			"width": 150,	
		},
		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": "From Date",
			"width": 150,
			"default":frappe.datetime.month_start()
		},
		{		
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": "To Date",
			"width": 150,	
			"default":frappe.datetime.month_end()
		},
		{		
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"label": "W/H",
			"options": "Warehouse",
			"width": 150,	
		}
	]
};
