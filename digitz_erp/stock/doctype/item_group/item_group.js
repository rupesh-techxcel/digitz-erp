// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item Group', {
	// refresh: function(frm) {

	// }

	setup:function(frm)
	{
		frm.set_query("default_expense_account", function () {
			return {
				"filters": {
					"root_type":"Expense",
					"is_group":0
				}
			};
		});
	}
});
