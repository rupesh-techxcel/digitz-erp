// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Project Profitability Report"] = {
	"filters":[
		{
			"fieldname": "project",
			"label": "Project",
			"fieldtype": "Link",
			"options": "Project",
			"reqd": 0,
			"get_query": () => {
                return {
                    filters: {
                        status: "Open",
                        docstatus: 1,
                    }
                };
            }
		}
	]
};
