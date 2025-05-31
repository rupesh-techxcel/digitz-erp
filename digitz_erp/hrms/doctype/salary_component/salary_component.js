// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Component", {
	onload(frm) {
    assign_defaults(frm);
	},
	setup(frm){

		frm.set_query("account", function() {
			return {
				filters: {
					is_group: 0,
					root_type:"Expense"
				}
			};
		});
	}


});

function assign_defaults(frm)
{
	if(frm.is_new())
	{
	
	}
 }
