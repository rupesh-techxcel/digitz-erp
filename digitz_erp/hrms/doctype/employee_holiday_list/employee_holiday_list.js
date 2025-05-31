// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Holiday List", {
	refresh(frm) {

	},
	leave_period:function(frm)
    {        
        frm.set_query("holiday_list", function () {
			return {
				"filters": {
					"leave_period": frm.doc.leave_period,
                    "default_for_the_leave_period":0,
					"docstatus":1
				}
			};
		});
    }    
});
