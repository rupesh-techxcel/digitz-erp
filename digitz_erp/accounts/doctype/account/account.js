// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Account', {


	refresh: function(frm) {
		frm.set_query('parent_account', () => {
			return {
				filters: {				
					is_group: 1
				}
			}
			});

	}
});

frappe.ui.form.on("Account", "onload", function(frm) {

	frm.trigger("get_default_warehouse");	

});
