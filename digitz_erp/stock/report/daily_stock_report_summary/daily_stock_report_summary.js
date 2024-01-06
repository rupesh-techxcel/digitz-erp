// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.query_reports["Daily Stock Report Summary"] = {
	"filters": [
		{
			"fieldname": "item",
			"fieldtype": "Link",
			"label": "Item",
			"options": "Item",
			"width": 150,
		},
		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": "From Date",
			"width": 150,
			"default":frappe.datetime.get_today(),
			"reqd":1
		},
		{
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": "To Date",
			"width": 150,
			"default":frappe.datetime.get_today(),
			"reqd":1
		},
		{
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"label": "Warehouse",
			"options": "Warehouse",
			"width": 150,
			"default": function () {
                var defaultWarehouse = "";
                frappe.call({
                    method: "digitz_erp.api.user_api.get_user_default_warehouse",
                    async: false,
                    callback: function (r) {
                        if (r && r.message) {
							console.log(r.message)
                            defaultWarehouse = r.message;
						}

						console.log(r)
                    },
                });

                return defaultWarehouse;
            },
			"reqd":1
		},
		{		
			"fieldname": "show_all",
			"fieldtype": "Check",
			"label": "Show All",
			"width": 150,
			"default":0			
		}
	]
};
