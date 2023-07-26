// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Trial Balance"] = {
	"filters": [
		{
				"fieldname": "company",
				"label": __("Company"),
				"fieldtype": "Link",
				"options": "Company",
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
	],
		"tree": true,
		"treeView": true,
		"name_field": "account",
		"parent_field": "parent_account",
		"initial_depth": 3
};
