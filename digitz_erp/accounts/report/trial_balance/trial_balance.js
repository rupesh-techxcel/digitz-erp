// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Trial Balance"] = {
	"filters": [
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
	
};
