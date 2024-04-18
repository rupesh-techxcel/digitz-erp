// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt
// "default":frappe.datetime.year_start(),
// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Cash Flow Report"] = {
	onload: function(report) {
		frappe.call({
			method: "digitz_erp.api.settings_api.get_fiscal_years",
			callback: function(r) {
				console.log("API Response:", r.message);
	
				if (r.message && Array.isArray(r.message) && r.message.length > 0) {
					var year_field = frappe.query_report.get_filter('year');
					// Ensure options are set as a newline-separated string if it's an array
					year_field.df.options = r.message;
					// Set the first fiscal year as the default if not set
					
					year_field.refresh();
				} else {
					frappe.msgprint(__('No fiscal years found.'));
				}
			},
			error: function(r) {
				console.error("Error fetching fiscal years: ", r);
				frappe.msgprint(__('There was a problem fetching fiscal years.'));
			}
		});		
		
	},	
	
    filters: [
        {
            "fieldname": "filter_based_on",
            "fieldtype": "Select",
            // "options": "Fiscal Year\nDate Range",
            "options": "Date Range",
            "default": "Date Range"	
        },
        {
            "fieldname": "year",
            "fieldtype": "Select",
            "depends_on": "eval:doc.filter_based_on == 'Fiscal Year'"				
        },
        {
            "fieldname": "from_date",
            "fieldtype": "Date",
            "label": "From Date",
            "default": frappe.datetime.year_start(),
			"depends_on": "eval:doc.filter_based_on == 'Date Range'"
        },
        {
            "fieldname": "to_date",
            "fieldtype": "Date",
            "label": "To Date",
            "default": frappe.datetime.year_end(),
			"depends_on": "eval:doc.filter_based_on == 'Date Range'"
        },
        {
            "fieldname": "periodicity",
            "label": "Periodicity",
            "fieldtype": "Select",
            "options": [                
                { "value": "Monthly", "label": "Monthly" },
                { "value": "Quarterly", "label": "Quarterly" },
                { "value": "Half-Yearly", "label": "Half-Yearly" },
                { "value": "Yearly", "label": "Yearly" }
            ],
            "default": "Monthly",
            "reqd": 1
        }
    ]
};
