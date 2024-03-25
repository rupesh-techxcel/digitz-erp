// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Payment Allocation Report"] = {
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
			"default":frappe.datetime.month_end()
		},
	]
};
