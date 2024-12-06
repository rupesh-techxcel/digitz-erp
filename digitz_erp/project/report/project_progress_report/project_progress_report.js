// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Project Progress Report"] = {
	"filters": [
        {
            "fieldname": "project",
            "label": __("Project"),
            "fieldtype": "Link",
            "options": "Project",
            "reqd": 0, // Optional filter
            "get_query": () => {
                return {
                    filters: {
                        status: "Open",
                        cancelled: 0,
                    }
                };
            }
        }
    ]
};
