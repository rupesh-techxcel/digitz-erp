// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Chart - Top Customer Sales"] = {
	"filters": [
		{
            "fieldname": "from_date",
            "fieldtype": "Date",
            "label": "From Date",
            "width": 150,
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -3)
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
