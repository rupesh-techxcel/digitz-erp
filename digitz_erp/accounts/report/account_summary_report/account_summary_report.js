// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Account Summary Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": "From Date",
			"default":frappe.datetime.year_start()
		},
		{
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": "To Date",
			"default":frappe.datetime.month_end()
		},
		{
			"fieldname": "account_group",
			"fieldtype": "Link",
			"label": "Account Group",
			"options": "Account",
			"get_query": function() {
				return {
					filters: {
						'is_group': 1
					}
				};
			}
		},
		{
			"fieldname":"account",
			"fieldtype":"Link",
			"label":"Account",
			"options":"Account",
			"get_query": function() {
				return {
					filters: {
						'is_group': 0
					}
				};
			}
		}
],		
};
