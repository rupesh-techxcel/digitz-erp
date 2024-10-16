// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Budget", {
	refresh(frm) {

	},
    setup(frm) {
        frm.trigger('get_default_company_and_warehouse');
    },

    get_default_company_and_warehouse(frm) {

		var default_company = ""

		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				'doctype': 'Global Settings',
				'fieldname': 'default_company'
			},
			callback: (r) => {

				default_company = r.message.default_company
				
                frm.set_value("company",default_company)
				
				
			}
		})

	},
});

