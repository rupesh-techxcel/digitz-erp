// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Project", {
    project_name(frm) {
        frm.set_query("proforma_invoice", "project_stage_table", function (doc, cdt, cdn) {
            return {
                filters: { project: frm.doc.project_name }
            };
        });
    },

    onload_post_render(frm) {
        frm.fields_dict['project_stage_table'].grid.add_custom_button('Create Progress Entry', function() {
            if (frm.doc.project_stage_table.length < 1) {
                frappe.new_doc("Progress Entry", {}, function(pe) {
                    pe.project = frm.doc.name;
                });
            } else {
                frappe.call({
                    method: 'digitz_erp.api.project_api.get_last_progress_entry',
                    args: { project_name: frm.doc.name },
                    callback: function(r) {
                        if (r.message) {
                            frappe.new_doc("Progress Entry", {}, function(pe) {
                                pe.project = frm.doc.name;
                                pe.previous_progress_entry = r.message;
                                pe.is_prev_progress_exists = 1;
                            });
                        } else if (frm.doc.project_stage_table.length == 1) {
                            frappe.new_doc("Progress Entry", {}, function(pe) {
                                pe.project = frm.doc.name;
                            });
                        } else {
                            frappe.msgprint(__('No progress entries found, and conditions not met for auto-creation.'));
                        }
                    }
                });
            }
        });
    },

    refresh(frm) {
        refresh_progress_entries(frm);

        if (!frm.is_new()) {
            frm.add_custom_button(__('Create Advance Entry'), function() {
                frappe.new_doc('Advance Entry', {}, ae => {
                    ae.customer = frm.doc.customer;
                    ae.project = frm.doc.name;
                });
            }, __("Actions"));
        }
    },

    setup(frm) {
        let data = JSON.parse(localStorage.getItem('project_data'));
        if (data) {
            frm.set_value('customer', data.customer);
            frm.set_value('sales_order', data.sales_order);
            frm.set_value("project_amount", data.project_amount);
            frm.refresh_field();
            localStorage.removeItem('project_data');
        }
    },

    onload(frm) {
        let customer = localStorage.getItem('customer');
        if (customer) {
            frm.set_value('customer', customer);
            localStorage.removeItem('customer');
        }
    },

    retentation_percentage(frm) {
        let percentage = parseFloat(frm.doc.retentation_percentage);
        if (isNaN(percentage) || percentage < 0) {
            frm.set_value("retentation_amt", 0);
            frm.set_value("amount_after_retentation", 0);
            frappe.msgprint('Please enter a valid retention percentage.');
            return;
        }

        if (frm.doc.sales_order) {
            frappe.call({
                method: "digitz_erp.project.doctype.project.project.calculate_rest_amt",
                args: {
                    sales_order_id: frm.doc.sales_order,
                    retentation_percentage: percentage
                },
                callback: function (response) {
                    if (response.message) {
                        let data = response.message;
                        frm.set_value("retentation_amt", Math.round(data.retentation_amt));
                        frm.set_value("amount_after_retentation", Math.round(data.amount_after_retentation));
                    }
                }
            });
        }
    },

    sales_order(frm) {
        frappe.db.get_value("Sales Order", frm.doc.sales_order, 'net_total').then(r => {
            if (r.message) {
                let net_total = r.message.net_total;
                let amt = (net_total * parseFloat(frm.doc.retentation_percentage)) / 100;
                frm.set_value("project_amount", net_total);
                frm.set_value("retentation_amt", amt);
                frm.set_value("amount_after_retentation", net_total - amt);
            }
        });
    }
});

function refresh_progress_entries(frm) {
    frappe.call({
        method: 'digitz_erp.api.project_api.get_progress_entries_by_project',
        args: { project_name: frm.doc.name },
        callback: function(response) {
            if (response.message) {
                let total_completion_percentage = 0;
                let progress_count = 0;

                frm.clear_table('project_stage_table');
                response.message.forEach(entry => {
                    let row = frm.add_child('project_stage_table');
                    row.progress_entry = entry.name;
                    row.proforma_invoice = entry.proforma_invoice;
                    row.sales_invoice = entry.progressive_sales_invoice;
                    row.posting_date = entry.posting_date;
                    row.percentage_of_completion = entry.total_completion_percentage;
                    row.net_total = entry.net_total;

                    console.log("row.percentage_of_completion")
                    console.log(row.percentage_of_completion)

                    total_completion_percentage += row.percentage_of_completion;
                    progress_count++;
                });

                frm.doc.project_average_completion = total_completion_percentage / progress_count;
                frm.refresh_field('project_stage_table');
                frm.refresh_field('project_average_completion');
            }
        }
    });
}
