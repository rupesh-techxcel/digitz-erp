// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item Price', {
	// refresh: function(frm) {

	// }

	is_selling(frm)
	{
		console.log("is_selling")
		frm.doc.is_buying = !frm.doc.is_selling
		frm.refresh_field("is_buying");  
	},
	is_buying(frm)
	{
		console.log("is buying")
		frm.doc.is_selling = !frm.doc.is_buying
		frm.refresh_field("is_selling"); 
	},

	validate: function (frm) {

		if ((frm.doc.from_date && !frm.doc.to_date) || (!frm.doc.from_date && frm.doc.to_date)) {
            frappe.msgprint(__('Both From Date and To Date must be selected together.'));
            frappe.validated = false;
        }
	},
	get_default_currency(frm)
	{

		var default_company = ""

		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				'doctype': 'Global Settings',
				'fieldname': 'default_company'
			},
			callback: (r) => {

				default_company = r.message.default_company
				frm.doc.company = r.message.default_company
				frm.refresh_field("company");
				frappe.call(
					{
						method: 'frappe.client.get_value',
						args: {
							'doctype': 'Company',
							'filters': { 'company_name': default_company },
							'fieldname': ['default_currency']
						},
						callback: (r2) => {
							
							
							frm.doc.currency = r2.message.default_currency;							
							frm.refresh_field("currency");
	}
	})}});
},


});

frappe.ui.form.on("Item Price", "onload", function (frm) {

	console.log("")

	if(frm.doc.__islocal)
	{
		frm.trigger("get_default_currency");
	}
});
