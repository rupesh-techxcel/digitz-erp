// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shift Allocation", {

	show_a_message: function (frm,message) {
		frappe.call({
			method: 'digitz_erp.api.settings_api.show_a_message',
			args: {
				msg: message
			}
		});
	},
	refresh(frm) {
		if(frm.is_new())
		{
			// frm.events.show_a_message(frm,"Select the employee, shift and enter the 'expected end hour'. All other fields are read-only and are copied from the shift document.")
		}
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

		frm.add_fetch('shift', 'end_time', 'expected_end_time')
		frm.add_fetch('shift', 'no_of_units_per_day', 'expected_no_of_units')

	},
    onload(frm)
	{
		if(frm.is_new())
		{
			get_ot_applicable(frm);
		}
		
	},    
});

function get_ot_applicable(frm) {

    frappe.call({
        method: 'digitz_erp.api.employee_api.get_ot_applicable',
        callback: (r) => {

            if (!r.message) {
				frm.set_df_property('ot_applicable', 'hidden', true);                
            } else {
				frm.set_df_property('ot_applicable', 'hidden', false);
            }
        }
    });
}



