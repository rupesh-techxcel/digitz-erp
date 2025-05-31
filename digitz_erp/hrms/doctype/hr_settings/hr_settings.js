// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("HR Settings", {
	refresh(frm) {

	},
    setup:function(frm){

        frm.set_query("default_shift", function () {
			return {
				"filters": {
					"disabled": 0
				}
			};
		});

    }
});
