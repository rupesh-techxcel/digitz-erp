// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Price List', {
	// refresh: function(frm) {

	// }

	before_rename: function (frm, doc, dt, dn) {
        if (doc.name === "Standard Selling") {
            frappe.msgprint("You are not allowed to rename this record.");
            frappe.validated = false;
        }
		if (doc.name === "Standard Buying") {
            frappe.msgprint("You are not allowed to rename this record.");
            frappe.validated = false;
        }
    }
});
