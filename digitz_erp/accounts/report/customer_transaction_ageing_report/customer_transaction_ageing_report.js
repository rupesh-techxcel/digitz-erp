// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Customer Transaction Ageing Report"] = {
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
			"label": "Show from Date",			
			"width": 150,	
		},

	]
};
