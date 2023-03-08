// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Entry', {
	// refresh: function(frm) {
		
	// },
});

frappe.ui.form.on('Payment Entry Detail', {
	sup_or_expense_:function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		console.log(row)
		if (row.sup_or_expense_ == "Supplier"){
			frappe.db.get_value("Company", "Dolphin Chemicals", "default_payable_account",(r) => {
						var d = r.default_payable_account;
						console.log(d,'------')
						frappe.model.set_value(d.doctype, d.name, "account", r.default_payable_account)
					});
		}
	},
	account:function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		console.log(row)
	}
});
