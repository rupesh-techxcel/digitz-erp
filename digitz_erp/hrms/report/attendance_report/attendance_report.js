// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Attendance Report"] = {
	"filters": [
        {
            "fieldname": "date",
            "label": __("Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        }
    ]
};
