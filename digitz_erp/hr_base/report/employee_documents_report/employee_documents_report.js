// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Documents Report"] = {
	"filters": [
		{
			"fieldname": "employee",
			"fieldtype": "Link",
			"label": "Employee",
			"options":"Employee"						
		},
		{
			"fieldname": "status",
			"fieldtype": "Select",
			"label": "Status",
			"options": "Active\nExpired"					
		}
	]
};
