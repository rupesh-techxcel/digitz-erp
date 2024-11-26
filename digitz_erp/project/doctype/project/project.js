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
        if(!frm.is_new() && frm.doc.docstatus==1)
        {
            frm.fields_dict['project_stage_table'].grid.add_custom_button('Create Progress Entry', function() {
            
                frappe.new_doc("Progress Entry", {}, function(pe) {
                    pe.project = frm.doc.name;
                    pe.sales_order = frm.doc.sales_order
                });
            
            });
        }
    },
    setup(frm) {
       
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
            frm.set_value("retention_amount", 0);
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
        frappe.db.get_value("Sales Order", frm.doc.sales_order, 'rounded_total','gross_total').then(r => {
            if (r.message) {
                let project_value = r.message.rounded_total; 
                let project_gross_value = r.message.gross_total
                frm.set_value("project_value", project_value);
                frm.set_value("project_gross_value", project_gross_value);

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


