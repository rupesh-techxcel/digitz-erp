// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Purchase Register"] = {
	"filters": [
		{
			"fieldname": "supplier",
			"fieldtype": "Link",
			"label": "Supplier",
			"options": "Supplier",
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
				"fieldname": "credit_purchase",
				"label": ("Credit Purchase"),
				"fieldtype": "Select",
				"options": "Credit\nCash\nAll"
		}
	]
};
