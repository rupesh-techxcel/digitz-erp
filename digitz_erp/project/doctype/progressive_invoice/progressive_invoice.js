// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt


frappe.ui.form.on("Progressive Invoice", {
    setup(frm) {
        let project_id = localStorage.getItem("project_id");
        localStorage.removeItem("project_id");

        if (project_id) {
            frappe.call({
                method: "digitz_erp.project.doctype.project.project.get_project",
                args: {
                    project_id: project_id,
                },
                callback: function (response) {
                    if (response.message) {
                        frm.data = response.message;
                        frm.trigger("set_data_in_fields");
                    }
                }
            })
        }
    },
    refresh(frm) {
        frm.add_custom_button("Update", function () {
            console.log(frm)
            if (frm.doc.project) {
                frappe.call({
                    method: "digitz_erp.project.doctype.project.project.get_project",
                    args: {
                        project_id: frm.doc.project,
                    },
                    callback: function (response) {
                        if (response.message) {
                            frm.data = response.message;
                            frm.trigger('set_data_in_fields');
                            console.log("hdskfjsldf ")
                        }
                    }
                })
            }
        })
    },
    set_data_in_fields(frm) {
        console.log("Project Data", frm.data)
        let all_proforma_invoices = []
        let net_amounts = []
        frm.set_value("customer", frm.data.customer);
        frm.set_value("project", frm.data.name);
        frm.set_value("retentation_deducation", frm.data.retentation_amt);
        // frm.set_value()

        frm.data.project_stage_table.forEach(item => {
            net_amounts.push(item.net_total);
        })
        console.log(all_proforma_invoices);


                    let idx = 0;
                    let prev_amount = 0;

                    frm.doc.stage_details = []
                    let total_received = 0;
                    frm.data.project_stage_table.forEach(item => {
                        let current_amount = net_amounts[idx];

                        // Calculate amount as sum of prev_amount and current_amount
                        let amount = prev_amount + current_amount;
                        total_received = amount;
                        let row = frm.add_child("stage_details", {
                            "item": item.project_stage_defination,
                            "amount": amount,
                            "prev_amount": prev_amount,
                            "current_amount": current_amount,
                        })

                        prev_amount = amount;
                        idx += 1;
                    })
                    frm.refresh_field('stage_details');
                    console.log(total_received);
        // frm.data.project_stage_table.forEach(item => {
        //     all_proforma_invoices.push(item.proforma_invoice);
        // })
        // console.log(all_proforma_invoices);

        // frappe.call({
        //     method: "digitz_erp.project.doctype.proforma_invoice.proforma_invoice.get_net_amount_of_stages",
        //     args: {
        //         all_proforma_invoices: JSON.stringify(all_proforma_invoices)
        //     },
        //     callback: function (response) {
        //         if (response.message) {
        //             console.log("response.message",response.message)
        //             let net_total_amts = response.message;
        //             let idx = 0;
        //             let prev_amount = 0;

        //             frm.doc.stage_details = []
        //             frm.data.project_stage_table.forEach(item => {
        //                 let current_amount = net_total_amts[idx];

        //                 // Calculate amount as sum of prev_amount and current_amount
        //                 let amount = prev_amount + current_amount;
        //                 let row = frm.add_child("stage_details", {
        //                     "item": item.project_stage_defination,
        //                     "amount": amount,
        //                     "prev_amount": prev_amount,
        //                     "current_amount": current_amount,
        //                 })

        //                 prev_amount = current_amount;
        //                 idx += 1;
        //             })
        //             frm.refresh_field('stage_details');
        //         }
        //     }
        // })

        if (frm.data.advance_entry) {
            frappe.call({
                method: "digitz_erp.accounts.doctype.receipt_entry.receipt_entry.get_amount",
                args: {
                    receipt_entry_id: frm.data.advance_entry
                },
                callback: function (response) {
                    if (response.message) {
                        let amt = response.message;
                        frm.set_value("advance_deducation", amt);
                    }
                }
            })
        }

        // frm.data = null
    }
});
