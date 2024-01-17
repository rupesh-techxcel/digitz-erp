// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Chart Of Accounts"] = {
	"filters": [
		{
			"fieldname": "Company",
			"fieldtype": "Link",
			"label": "Company",
			"options": "Company",
			"width": 200,
			"default": "Dolphin Chemicals"
		},
	],
		"tree": true,
		"treeView": true,
		"name_field": "account",
		"parent_field": "parent_account",
		"initial_depth": 3

};
