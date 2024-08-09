// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Advance Entry", {
	refresh(frm) {
        // frm.add_custom_button(__("Create Pro"))
        console.log("refresh")
	},
    setup(frm){
        if(frm.is_new()){
            console.log("setup")
            let row = frm.add_child('advance_item_table');
            row.description = "Advance amount for the project "
            
            // Refresh the field to show the new row
            frm.refresh_field('advance_item_table');
            }
    },
    onload(frm){
        console.log("onload")
    }
});
