// Copyright (c) 2024,   and contributors
// For license information, please see license.txt

frappe.ui.form.on("Work Order", {
    show_a_message: function (frm,message) {
        frappe.call({
            method: 'digitz_erp.api.settings_api.show_a_message',
            args: {
                msg: message
            }
        });
    },
	refresh(frm) {

        if (frm.doc.boq_execution) {

            frm.set_df_property('boq_execution', 'read_only', 1);

            if(frm.is_new())
            {
                frm.events.get_boq_execution_employees(frm,frm.doc.boq_execution)
                frm.events.get_boq_execution_tasks(frm,frm.doc.boq_execution)
            }            
        }

        if(frm.is_new())
            {
               frm.events.get_default_company_and_warehouse(frm);
               frm.events.show_a_message(frm,"Save and submit the document to start the work order.");
            }

            if (frm.doc.docstatus === 1 && frm.doc.status == "In Process") {
                frm.add_custom_button(__('Complete Work Order'), function() {
                    frappe.call({
                        method: 'digitz_erp.api.boq_api.complete_work_order',
                        args: {
                            work_order_name: frm.doc.name
                        },
                        callback: function(response) {
                            if (!response.exc) {                                
                                frm.events.show_a_message(frm,"Work Order Completed and BOQ updated successfully..");
                                frm.reload_doc();
                            }
                        }
                    });
                });
            }
            if (frm.doc.docstatus === 1 && frm.doc.status === "Not Started") {
                frm.add_custom_button(__('Start Work Order'), function() {
                    frappe.call({
                        method: 'digitz_erp.api.boq_api.start_work_order',
                        args: {
                            work_order_name: frm.doc.name
                        },
                        callback: function(response) {
                            if (!response.exc) {                                
                                frm.events.show_a_message(frm,"Work Order Started successfully.");
                                frm.reload_doc();
                            }
                        }
                    });
                });
            }

            if (frm.doc.docstatus === 1 && frm.doc.status === "In Process") {
                frm.add_custom_button(__('Create Timesheet Entry'), function() {
                    frappe.call({
                        method: "digitz_erp.api.boq_api.create_timesheet_entry",
                        args: {
                            work_order: frm.doc.name
                        },
                        callback: function(r) {
                            if (r.message) {
                                console.log("r.message",r.message)
    
                                // Sync the received work order data to create a new unsaved document                            
                                frappe.model.sync([r.message]);                            
    
                                // Load the newly created Work Order in the form view
                                frappe.set_route("Form", "Timesheet Entry", r.message.name);
                            } 
                        }
                    });
                },"Actions");
            }
            if (frm.doc.docstatus === 1 && frm.doc.status === "In Process") {
                frm.add_custom_button(__('Create Material Issue'), function() {
                    frappe.call({
                        method: "digitz_erp.api.boq_api.create_material_issue",
                        args: {
                            work_order: frm.doc.name
                        },
                        callback: function(r) {
                            if (r.message) {
                                console.log("r.message",r.message)
    
                                // Sync the received work order data to create a new unsaved document                            
                                frappe.model.sync([r.message]);                            
    
                                // Load the newly created Work Order in the form view
                                frappe.set_route("Form", "Material Issue", r.message.name);
                            } 
                        }
                    });
                },"Actions");
            }
	},
    get_default_company_and_warehouse: function (frm) {
        let default_company = ""
        frappe.call({
          method: "frappe.client.get_value",
          args: {
            doctype: "Global Settings",
            fieldname: "default_company",
          },
          callback: (r) => {
            frm.set_value("company", r.message.default_company);
          }})
    },    
    get_boq_execution_employees: function(frm,boq_execution) {
       
        if (boq_execution) {

            // Call the server-side method to get filtered project employees
            frappe.call({
                method: "digitz_erp.api.boq_api.get_boq_execution_employees",
                args: {
                    boq_execution_name: boq_execution
                },
                callback: function(r) {
                    if (r.message) {
                        
                        // Clear existing child table entries
                        frm.clear_table("work_order_employees");
                        
                        // Add the fetched employees to the project_employee table
                        r.message.forEach(employee => {
                            let row = frm.add_child("work_order_employees");
                            row.employee = employee.employee; 
                            row.employee_name = employee.employee_name;
                            row.per_hour_rate = employee.per_hour_rate;
                            row.department = employee.department;
                            row.designation = employee.designation;

                        });

                        frm.refresh_field("work_order_employees");
                    }
                }
            });
        } else {
            frm.clear_table("work_order_employees");
            frm.refresh_field("work_order_employees");
        }
    },
    get_boq_execution_tasks: function(frm,boq_execution) { 
        
        console.log("get_boq_execution_tasks")

        if (boq_execution) {

            // Call the server-side method to get filtered project employees
            frappe.call({
                method: "digitz_erp.api.boq_api.get_boq_execution_tasks",
                args: {
                    boq_execution_name: boq_execution
                },
                callback: function(r) {
                    if (r.message) {
                        
                        console.log("boq_execution_tasks")
                        console.log(r.message)

                        // Clear existing child table entries
                        frm.clear_table("work_order_tasks");
                        
                        // Add the fetched employees to the project_employee table
                        r.message.forEach(task => {
                            let row = frm.add_child("work_order_tasks");
                            row.task = task.task;
                            row.task_name = task.task_name;
                            row.task_description = task.task_description
                            row.expected_start_date = task.expected_start_date;
                            row.expected_end_date = task.expected_end_date
                            row.actual_start_date = task.actual_start_date;
                            row.actual_end_date =  task.actual_end_date
                        });

                        frm.refresh_field("work_order_tasks");
                    }
                }
            });
        } else {
            frm.clear_table("work_order_tasks");
            frm.refresh_field("work_order_tasks");
        }
    },
});
