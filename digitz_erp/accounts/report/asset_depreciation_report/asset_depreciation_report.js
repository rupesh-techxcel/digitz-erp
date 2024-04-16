// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Asset Depreciation Report"] = {
	"filters": [
		{
			"fieldname": "asset",
			"fieldtype": "Link",
			"label": "Asset",
			"options":"Asset"						
		}
	]
};
