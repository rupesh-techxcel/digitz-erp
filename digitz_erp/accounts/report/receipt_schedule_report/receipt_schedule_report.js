// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Receipt Schedule Report"] = {
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
			"fieldname": "customer",
			"fieldtype": "Link",
			"label": "Customer",
			"options": "Customer"
		},
		{
            fieldname: 'group_by',
            label: __('Group By'),
            fieldtype: 'Select',
            options: 'None\nDate\nCustomer\nCustomer And Date',
            default: 'Customer And Date'
        },
	]
};
