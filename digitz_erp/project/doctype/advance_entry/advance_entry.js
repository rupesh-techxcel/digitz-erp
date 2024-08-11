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
            get_default_company_and_warehouse(frm);
            // Refresh the field to show the new row
            // frm.refresh_field('advance_item_table');
        }
    },
    onload(frm){
        console.log("onload")
    },
    
});


function get_default_company_and_warehouse(frm) {
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
            frm.doc.company = r.message.default_company
            frm.refresh_field("company");
            frappe.call(
                {
                    method: 'frappe.client.get_value',
                    args: {
                        'doctype': 'Company',
                        'filters': { 'company_name': default_company },
                        'fieldname': ['default_warehouse', 'rate_includes_tax']
                    },
                    callback: (r2) => {
                        console.log("Before assign default warehouse");
                        console.log(r2.message.default_warehouse);
                        frm.doc.warehouse = r2.message.default_warehouse;
                        console.log(frm.doc.warehouse);
                        frm.doc.rate_includes_tax = r2.message.rate_includes_tax;
                        frm.refresh_field("warehouse");
                        frm.refresh_field("rate_includes_tax");
                    }
                }

            )
        }
    })

}


frappe.ui.form.on("Advance Entry Item",{
    amount(frm,cdt,cdn){
        update_net_total(frm);
    },
    advance_item_table_remove(frm){
        update_net_total(frm);
    }
})


function update_net_total(frm){
    let net_total = 0;
    frm.doc.advance_item_table.forEach(item =>{
        net_total += item.amount;
    })

    frm.set_value("net_total",net_total);
}