// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt


frappe.query_reports["Project Summary"] = {
	filters: [
		// {
		// 	fieldname: "company",
		// 	label: __("Company"),
		// 	fieldtype: "Link",
		// 	options: "Company",
		// 	default: frappe.defaults.get_user_default("Company"),
		// 	reqd: 1,
		// },
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nOpen\nCompleted\nCancelled",
			// default: "Open",
		},
		// // {
		// // 	fieldname: "project_type",
		// // 	label: __("Project Type"),
		// // 	fieldtype: "Link",
		// // 	options: "Project Type",
		// // },
		// {
		// 	fieldname: "priority",
		// 	label: __("Priority"),
		// 	fieldtype: "Select",
		// 	options: "\nLow\nMedium\nHigh",
		// },
		// {"fieldname": "project_stage_defination", "label": "Project Stage Definition", "fieldtype": "Data", "width": 120},

	],
};


