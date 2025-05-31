frappe.query_reports["Salary Register"] = {
    "filters": [
        {
            "fieldname": "employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee"
        },
        {
            "fieldname": "year",
            "label": __("Year"),
            "fieldtype": "Select",
            "reqd": 1,
            "options": []  // To be filled dynamically
        },
        {
            "fieldname": "month",
            "label": __("Month"),
            "fieldtype": "Select",
            "reqd": 1,
            "options": [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ],
        }
    ],
    onload: function(report) {
        // Fetch distinct years from Salary Slip doctype
        frappe.call({
            method: 'digitz_erp.api.employee_api.get_distinct_years',
            callback: function(r) {
                if (r.message) {
                    let year_filter = report.get_filter('year');
                    year_filter.df.options = r.message.join('\n');
                    year_filter.refresh();
                    year_filter.set_input(year_filter.df.options.split('\n')[0]);  // Set default to the first option
                }
            }
        });

		// Set default month to the current month
        let current_month_index = new Date().getMonth();
        let month_filter = report.get_filter('month');
        let month_options = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];
        month_filter.set_input(month_options[current_month_index]);
		month_filter.refresh();
        
        // Refresh the report
        report.refresh();
    }
};
