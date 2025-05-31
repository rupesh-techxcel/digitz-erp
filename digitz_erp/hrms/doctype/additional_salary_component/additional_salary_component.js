// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Additional Salary Component", {
	refresh(frm) {

	},
    setup(frm)
    {
        frm.set_query("salary_component", function () {
			return {
				"filters": {
					"use_for_additional_salary": 1                    
				}
			};
		});
    }
});
