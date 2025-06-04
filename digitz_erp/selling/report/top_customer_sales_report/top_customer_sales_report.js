// Copyright (c) 2025, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Top Customer Sales Report"] = {
	"filters": [
		{
            "fieldname": "from_date",
            "fieldtype": "Date",
            "label": "From Date",
            "width": 150,
            "default": frappe.datetime.year_start()
        },
        {
            "fieldname": "to_date",
            "fieldtype": "Date",
            "label": "To Date",
            "width": 150,
            "default": frappe.datetime.get_today()
        },
    ]
};

