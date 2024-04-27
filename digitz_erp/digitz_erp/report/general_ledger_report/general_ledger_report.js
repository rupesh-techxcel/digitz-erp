// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["General Ledger Report"] = {
	"filters": [
		{		
			"fieldname": "account",
            "fieldtype": "Link",
            "label": "Account",
            "options": "Account",
            "width": 200,
            "get_query": function() {
                return {
                    filters: [
                        ["is_group", "=", 0]  // Filter accounts where "is_group" is True
                    ]
                };
            }
		},
		{		
			"fieldname": "supplier",
			"fieldtype": "Link",
			"label": "Supplier",
			"options": "Supplier",			      
			"width": 200		
		},
		{		
			"fieldname": "customer",
			"fieldtype": "Link",
			"label": "Customer",
			"options": "Customer",			      
			"width": 200		
		},				
		{		
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": "From Date",						
			"default":frappe.datetime.month_start()			
		},
		{		
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": "To Date",			
			"default":frappe.datetime.month_end()	
		},
		{		
			"fieldname": "order_by_account",
			"fieldtype": "Check",
			"label": "Sort by account"
		},

	]
};
