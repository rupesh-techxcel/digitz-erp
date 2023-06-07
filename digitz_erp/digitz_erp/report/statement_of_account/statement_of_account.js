// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Statement Of Account"] = {
	"filters": [
		{		
			"fieldname": "customer",
			"fieldtype": "Link",
			"label": "Customer",
			"options": "Customer",
			"width": 150,
	
		},
		{
		
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": "From Date",
			"width": 150,
	
		},
		{
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": "To Date",
			"width": 150,
	
		},
		{
			"fieldname": "show_all_invoices",
			"fieldtype": "Check",
			"label": "Show All Invoices",
			"width": 150,
	
		},

	]
};
