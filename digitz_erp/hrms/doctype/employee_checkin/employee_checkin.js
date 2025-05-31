// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Checkin", {
	refresh(frm) {

	},
    setup(frm)
    {
        frm.set_query("shift", function () {
			return {
				"filters": {
					"disabled": 0
				}
			};
		});
    },
    employee(frm)
    {
        

    }
});
