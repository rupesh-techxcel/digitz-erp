// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Account', {


	// refresh: function(frm) {

	// }
});

frappe.ui.form.on("Account Invoice", "onload", function(frm) {

	//Since the default selectionis cash
	//frm.set_df_property("date","read_only",1);	
	frm.set_query("warehouse", function() {
		return {
			"filters": {
				"is_group": 0
			}
		};
	});	

	frm.trigger("get_default_warehouse");	

});
