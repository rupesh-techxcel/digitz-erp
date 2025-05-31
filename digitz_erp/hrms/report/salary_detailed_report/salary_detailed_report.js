// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Salary Detailed Report"] = {	
    "filters": [
        {
            "fieldname": "employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            "default": "",
            "reqd": 0,
            "get_query": function() {
                return {
                    "filters": {
                        "status": "On Job"
                    }
                };
            }
        },
        {
            "fieldname": "salary_group",
            "label": __("Salary Group"),
            "fieldtype": "Link",
            "options": "Salary Group",
            "default": "",
            "reqd": 0
        },
        {
            "fieldname": "payroll_date",
            "label": __("Payroll Date"),
            "fieldtype": "Date",
            "reqd": 1
        }
    ],
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.fieldname == "employee_name" && data["is_group"] == 1) {
            value = `<span style="font-weight: bold;">${value}</span>`;
        }
        return value;
    },
    "get_data": function(filters) {
        return frappe.call({
            method: "your_app_path.your_module.report.your_report_name.your_report_name.execute",
            args: {
                filters: filters
            },
            callback: function(response) {
                if (response.message) {
                    var result = response.message;
                    frappe.query_report.data = result;
                    frappe.query_report.render();
                }
            }
        });
    }
};
