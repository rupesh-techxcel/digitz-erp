// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Profit and Loss Statement"] = {
	"filters": [
		{
				"fieldname": "year_selection",
				"label": __("Year Selection"),
				"fieldtype": "Select",
				"options": "Date Range\nFiscal Year",
				"default": "Date Range",
				"on_change": function(query_report) {
					var year_selection = query_report.get_values().year_selection;
					if (!year_selection) {
						return;
					}
					get_posting_years()
				}
		},
		{
  		"fieldname": "select_year",
  		"label": "Select Year",
  		"fieldtype": "Select",
  		"options": get_posting_years(),
			"async": true,
  		"depends_on": "eval: doc.year_selection == 'Fiscal Year'"
		},
		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": "From Date",
			"depends_on": "eval: doc.year_selection == 'Date Range' ",
			"default":frappe.datetime.year_start()
		},
		{
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": "To Date",
			"depends_on": "eval: doc.year_selection == 'Date Range' ",
			"default":frappe.datetime.year_end()
		},
		{
			"fieldname": "accumulated_values",
			"fieldtype": "Check",
			"label": "Accumulated Values"			
		}
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
			frappe.query_reports["Profit and Loss Report"].filters[1].options = res.message;
		});
	return options;
}

