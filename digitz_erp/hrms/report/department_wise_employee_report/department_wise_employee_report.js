// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Department wise Employee Report"] = {
	"filters": [
		{		
			"fieldname": "employee",
			"fieldtype": "Link",
			"label": "Employee",
			"options": "Employee",
			"width": 150,	
		},
		{		
			"fieldname": "designation",
			"fieldtype": "Link",
			"label": "Designation",
			"options": "Designation",
			"width": 150,	
		},
		{		
			"fieldname": "department",
			"fieldtype": "Link",
			"label": "Department",
			"options": "Department",
			"width": 150,	
		},
		{
			"fieldname":"status",
			"fieldtype":"Select",
			"label":"Status",
			"options": "\nOn Boarding\nOn Training\nOn Probation\nOn Job\nResigned\nTerminated"
		}

	]
};
