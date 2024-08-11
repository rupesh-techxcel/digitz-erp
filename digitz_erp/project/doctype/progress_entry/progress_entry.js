// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Progress Entry", {
	refresh(frm) {
    //    if(!frm.is_new()){
    //     frm.add_custom_button(__("Create Proforma Invoice"),function(){

    //     },__("Action"))
    //    }
	},
});

frappe.ui.form.on("Progress Entry Items",{
    completion_percentage(frm,cdt,cdn) {
        let row = frappe.get_doc(cdt,cdn);
        console.log(row);

        if(row.completion_percentage > 100){
            row.completion_percentage = 0;
            frappe.msgprint({
                title: __('Validation Error'),
                indicator: 'red',
                message: __("Completion % can't be more than 100%")
            });
        }else{
            update_progress(frm);
        }
    },
    progress_entry_items_delete(frm){
        update_progress(frm)
    }
})

function update_progress(frm){
    let total_percentage = 0;
    let total_items = frm.doc.progress_entry_items.length;
    for(item of frm.doc.progress_entry_items){
        total_percentage += item.completion_percentage;
    }
    frm.set_value('average_of_completion', (total_percentage/total_items))
}