// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Progress Entry", {
	refresh(frm) {
       if(!frm.is_new()){
        frm.add_custom_button(__("Create Proforma Invoice"),function(){

        },__("Action"))
       }
	},
});
