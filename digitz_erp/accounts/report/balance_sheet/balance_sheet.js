// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Balance Sheet"] = {
	"filters": [
		{
				"fieldname": "period_selection",
				"label": __("Period Selection"),
				"fieldtype": "Select",
				// "options": "Date Range\nFiscal Year",
				"options": "Date Range",
				"default": "Date Range",
				"on_change": function(query_report) {
					var period_selection = query_report.get_values().period_selection;
					console.log("1")
					if (!period_selection) {
						return;
					}
					
					get_posting_years()
					console.log("2")
				}
		},
		{
  		"fieldname": "select_year",
  		"label": "Select Year",
  		"fieldtype": "Select",
  		"options": get_posting_years(),
		"async": true,
  		"depends_on": "eval: doc.period_selection == 'Fiscal Year'"
		},
		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": "From Date",
			"depends_on": "eval: doc.period_selection == 'Date Range' ",
			"default":frappe.datetime.month_start()
		},
		{
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": "To Date",
			"depends_on": "eval: doc.period_selection == 'Date Range' ",
			"default":frappe.datetime.month_end()
		},
		{
			"fieldname": "accumulated_values",
			"fieldtype": "Check",
			"label": "Accumulated Values"
		},
		
	],
		"tree": true,
		"treeView": true,
		"name_field": "account",
		"parent_field": "parent_account",
		"initial_depth": 3
};

function get_posting_years() {
	let options = [];
	frappe.call('digitz_erp.accounts.report.digitz_erp.get_posting_years', {
	}).then((res) => {
			frappe.query_reports["Balance Sheet"].filters[1].options = res.message;
			console.log(res.message)
		});
	return options;
}
