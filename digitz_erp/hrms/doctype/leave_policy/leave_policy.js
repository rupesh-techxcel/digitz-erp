// Copyright (c) 2024, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Policy", {

	setup:function(frm)
	{
		frm.fields_dict['leave_policy_details'].grid.get_field('leave_type').get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    disabled: 0,
					is_leave_without_pay:0,
					is_partially_paid_leave:0					
                }
            };
		}
	}

});

frappe.ui.form.on('Leave Policy Details',{
	leave_type: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if(child.leave_type){
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Leave Type",
					fieldname: "max_leaves_allowed",
					filters: { name: child.leave_type }
				},
				callback: function(r) {
					if (r.message) {
						child.annual_allocation = r.message.max_leaves_allowed;
						refresh_field("leave_policy_details");
					}
				}
			});
		}
		else{
			child.annual_allocation = "";
			refresh_field("leave_policy_details");
		}
	}
});
