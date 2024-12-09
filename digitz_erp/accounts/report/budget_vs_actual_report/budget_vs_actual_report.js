// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Budget Vs Actual Report"] = {
	
		"filters": [
		  {
			"fieldname": "budget_against",
			"label": "Budget Against",
			"fieldtype": "Select",
			"options": "\nProject\nCost Center\nCompany",
			"reqd": 1
		  },		  
		  {
			"fieldname": "project",
			"label": "Project",
			"fieldtype": "Link",
			"options": "Project",
			"depends_on": "eval:doc.budget_against == 'Project'"
		  },
		  {
			"fieldname": "cost_center",
			"label": "Cost Center",
			"fieldtype": "Link",
			"options": "Cost Center",
			"depends_on": "eval:doc.budget_against == 'Cost Center'"
		  },
		  {
			"fieldname": "company",
			"label": "Company",
			"fieldtype": "Link",
			"options": "Company",
			"depends_on": "eval:doc.budget_against == 'Company'"
		  },
		  {
			"fieldname": "fiscal_year",
			"label": "Fiscal Year",
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"depends_on": "eval:doc.budget_against == 'Company'"
		  }
		]
	  }
	  