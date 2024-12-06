// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Budget Vs Actual Report"] = {
	"filters": [
		{
			"fieldname": "budget_against",
			"label": "Budget Against",
			"fieldtype": "Select",
			"options": "Company\nProject\nCost Center",
			"reqd": 1
		},
		{
			"fieldname": "company",
			"label": "Company",
			"fieldtype": "Link",
			"options": "Company",
			"depends_on": "eval:doc.budget_against == 'Company'",
			"reqd": 0
		},
		{
			"fieldname": "project",
			"label": "Project",
			"fieldtype": "Link",
			"options": "Project",
			"depends_on": "eval:doc.budget_against == 'Project'",
			"reqd": 0
		},
		{
			"fieldname": "cost_center",
			"label": "Cost Center",
			"fieldtype": "Link",
			"options": "Cost Center",
			"depends_on": "eval:doc.budget_against == 'Cost Center'",
			"reqd": 0
		}
	]
	
};
