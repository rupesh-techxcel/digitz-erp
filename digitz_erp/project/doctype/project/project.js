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

    refresh(frm) {
        if(!frm.is_new())
            {
                frm.fields_dict['project_stage_table'].grid.add_custom_button('Create Progress Entry', function() {
                
                    frappe.new_doc("Progress Entry", {}, function(pe) {
                        pe.project = frm.doc.name;
                        pe.sales_order = frm.doc.sales_order
                    });
                
                });            
                  
                refresh_wip(frm)   
                refresh_so_value(frm)  
                refresh_billed_amount(frm)
            }

            refresh_progress_entries(frm); 
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

    retention_percentage(frm) {

        let percentage = parseFloat(frm.doc.retention_percentage);
        if (isNaN(percentage) || percentage < 0) {
            frm.set_value("retention_amt", 0);
            frm.set_value("amount_after_retention", 0);
            frappe.msgprint('Please enter a valid retention percentage.');
            return;
        }

        if (frm.doc.sales_order) {
            frappe.call({
                method: "digitz_erp.project.doctype.project.project.calculate_retention_amt",
                args: {
                    sales_order_id: frm.doc.sales_order,
                    retention_percentage: percentage
                },
                callback: function (response) {
                    if (response.message) {

                        console.log("response.message",response.message)

                        let data = response.message;

                        frm.doc.retention_amount = Math.round(data.retention_amt)
                        frm.refresh_field('retention_amount')

                        // frm.set_value("retention_amt", Math.round(data.retention_amt));
                        frm.set_value("amount_after_retention", Math.round(data.amount_after_retention));
                    }
                }
            });
        }
    },

    sales_order(frm) {
        frappe.db.get_value("Sales Order", frm.doc.sales_order, 'net_total').then(r => {
            if (r.message) {
                let net_total = r.message.net_total;
                let amt = (net_total * parseFloat(frm.doc.retention_percentage)) / 100;
                frm.set_value("project_amount", net_total);
                frm.set_value("retention_amt", amt);
                frm.set_value("amount_after_retention", net_total - amt);
            }
        });
    },
    project_team:function(frm)
    {
        if(frm.doc.project_team)
        {
            frm.clear_table('employees')
        }

        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Project Team',
                name: frm.doc.project_team
            },
            callback: function (r) {
                console.log("r")
                console.log(r)
                if (r.message && r.message.team_details) {
                    let team_employees = r.message.team_details;

                    
                    // Loop through each task in the template and add it to the project_tasks child table
                    team_employees.forEach(function (team_employee) {
                        let new_employee = frm.add_child('employees');
                        new_employee.employee = team_employee.employee; // Assuming Task Template has a 'task_name' field                        
                    });

                    // Refresh the child table to show populated tasks
                    frm.refresh_field('employees');
                }
            }
        })

    },
    task_template: function (frm) {
        if (frm.doc.task_template) {

            console.log("doc.task_template")
            console.log(frm.doc.task_template)

            // Clear existing project tasks
            frm.clear_table('tasks');
            
            // Fetch tasks from the selected Task Template
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Task Template',
                    name: frm.doc.task_template
                },
                callback: function (r) {
                    console.log("r")
                    console.log(r)
                    if (r.message && r.message.task_template_details) {
                        let template_tasks = r.message.task_template_details;

                        console.log("task_templates")
                        console.log(template_tasks)
                        
                        // Loop through each task in the template and add it to the project_tasks child table
                        template_tasks.forEach(function (template_task) {
                            let new_task = frm.add_child('tasks');
                            new_task.task = template_task.task; // Assuming Task Template has a 'task_name' field
                            // new_task.task_description = task.task_description; // Assuming Task Template has a 'task_description' field
                            // new_task.start_date = task.start_date; // Assuming Task Template has a 'start_date' field
                            // new_task.end_date = task.end_date; // Assuming Task Template has an 'end_date' field
                            // Add any additional fields from Task Template as needed
                        });

                        // Refresh the child table to show populated tasks
                        frm.refresh_field('tasks');
                    }
                }
            });
        }
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
                
                frm.refresh_field('project_stage_table');
                
            }
        }
    });
}

function refresh_wip(frm)
{
    frappe.call({
        method: 'digitz_erp.api.project_api.get_wip_closing_balance',
        args: {
            project_name: frm.doc.name
        },
        callback: function (r) {
            if (r.message) {
                frm.set_value('work_in_progress_value', r.message);
            }
        }
    });
}

function refresh_so_value(frm)
{
    frappe.call({
        method: 'digitz_erp.api.project_api.get_sales_order_value_for_project',
        args: {
            project_name: frm.doc.name
        },
        callback: function (r) {
            if (r.message) {
                frm.set_value('sales_order_value', r.message);
            }
        }
    });

}


function refresh_billed_amount(frm)
{
    frappe.call({
        method: 'digitz_erp.api.project_api.get_billed_amount_for_project',
        args: {
            project_name: frm.doc.name
        },
        callback: function (r) {
            if (r.message) {
                frm.set_value('total_billed_amount', r.message);
            }
        }
    });

}
