// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Daily Stock Report"] = {
	"filters": [
		{
			"fieldname": "item",
			"fieldtype": "Link",
			"label": "Item",
			"options": "Item",
			"width": 150,
		},
		{
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"label": "Posting Date",
			"width": 150
		},
		{
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"label": "Warehouse",
			"options": "Warehouse",
			"width": 150,
		}
	]
};
