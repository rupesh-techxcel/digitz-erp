// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Enquiry", {
	refresh(frm) {

	},
    edit_posting_date_and_time(frm){

        if (frm.doc.edit_posting_date_and_time == 1) {
			frm.set_df_property("posting_date", "read_only", 0);
			frm.set_df_property("posting_time", "read_only", 0);
		}
		else {
			frm.set_df_property("posting_date", "read_only", 1);
			frm.set_df_property("posting_time", "read_only", 1);
		}
    },
    get_default_company(frm) {
		var default_company = ""
		console.log("From Get Default Warehouse Method in the parent form")

		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				'doctype': 'Global Settings',
				'fieldname': 'default_company'
			},
			callback: (r) => {

				default_company = r.message.default_company
				frm.set_value('company', default_company)
			}
		})

	},

    assign_defaults(frm)
	{
		if(frm.is_new())
		{
			frm.trigger("get_default_company"); 
        }
    }
});


frappe.ui.form.on("Enquiry", "onload", function (frm) {

	frm.trigger("assign_defaults")

});
