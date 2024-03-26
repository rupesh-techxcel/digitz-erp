// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Payment Schedule Report"] = {
	"filters": [
		{		
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": "From Date",						
			"default":frappe.datetime.month_start(),
			"mandatory":1
		},
		{		
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": "To Date",			
			"default":frappe.datetime.month_end(),	
			"mandatory":1
		},
		{		
			"fieldname": "supplier",
			"fieldtype": "Link",
			"label": "Supplier",
			"options": "Supplier"			
		},
		{
            fieldname: 'group_by',
            label: __('Group By'),
            fieldtype: 'Select',
            options: 'None\nDate\nSupplier\nSupplier And Date',
            default: 'Supplier And Date'
        },
	]
};
