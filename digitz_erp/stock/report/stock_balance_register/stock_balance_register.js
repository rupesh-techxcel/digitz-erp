// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock Balance Register"] = {
	"filters": [
		{
			"fieldname": "item",
			"fieldtype": "Link",
			"label": "Item",
			"options": "Item",
			"width": 150,
		},
		{
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"label": "W/H",
			"options": "Warehouse",
			"width": 150,
		}
	]
};
