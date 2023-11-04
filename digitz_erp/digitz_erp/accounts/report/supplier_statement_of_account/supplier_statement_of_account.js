// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Supplier Statement Of Account"] = {
	"filters": [
		{		
			"fieldname": "supplier",
			"fieldtype": "Link",
			"label": "Supplier",
			"options": "Supplier",			      
			"width": 150		
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
			"default":frappe.datetime.month_start()	
		},
		{
			"fieldname": "group_by",
			"fieldtype": "Select",
			"label": "Group By",
			"width": 150,
			"options": "Invoice\nSupplier",
			"default" : "Invoice"
		},
		{
			"fieldname": "show_pending_only",
			"fieldtype": "Check",
			"label": "Show Pending Only",
			"width": 150			
		}
	]
};