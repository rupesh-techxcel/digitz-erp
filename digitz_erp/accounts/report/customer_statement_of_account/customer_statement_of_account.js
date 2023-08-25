// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Customer Statement Of Account"] = {
	"filters": [
		{		
			"fieldname": "customer",
			"fieldtype": "Link",
			"label": "Customer",
			"options": "Customer",			      
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
			"options": "Invoice\nCustomer",
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
