// Copyright (c) 2024,   and contributors
// For license information, please see license.txt

frappe.ui.form.on("BOQ Execution", {
    show_a_message: function (frm,message) {
        frappe.call({
            method: 'digitz_erp.api.settings_api.show_a_message',
            args: {
                msg: message
            }
        });
    },
	refresh(frm) {
        
         if(frm.is_new())
         {
            frm.events.get_default_company_and_warehouse(frm);
            frm.events.show_a_message(frm,"Save and Submit the document to start execution.");

            if(frm.doc.boq !=undefined)
            {
                    frm.events.boq(frm)
            }
         }

         if (frm.doc.docstatus === 1 && frm.doc.status === "Not Started") {
            frm.add_custom_button(__('Start Execution'), function() {
                frappe.call({
                    method: "digitz_erp.api.boq_api.start_boq_execution",
                    args: {
                        boq_execution_name: frm.doc.name
                    },
                    callback: function(response) {
                        if (response.message === "success") {
                            frappe.show_alert({
                                message: __("Execution Started"),
                                indicator: "green"
                            });
                            frm.reload_doc();  // Refresh the document to show updated fields
                        } else {
                            frappe.show_alert({
                                message: __("Could not start execution"),
                                indicator: "red"
                            });
                        }
                    }
                });
            }, "Actions" );
        }
        
         // Show "Create Work Order" button if status is "In Process"
         if (frm.doc.docstatus === 1 && frm.doc.status === "In Process") {
            frm.add_custom_button(__('Create Work Order'), function() {
                frappe.call({
                    method: "digitz_erp.api.boq_api.create_work_order",
                    args: {
                        boq_execution_name: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            
                            console.log("r.message",r.message)

                            // Sync the received work order data to create a new unsaved document                            
                            frappe.model.sync([r.message]);                            

                            // Load the newly created Work Order in the form view
                            frappe.set_route("Form", "Work Order", r.message.name);
                        } 
                    }
                });
            },"Actions");

            frm.add_custom_button(__('Complete BOQ Execution'), function() {
                frappe.call({
                    method: "digitz_erp.api.boq_api.complete_boq_execution",
                    args: {
                        boq_execution_name: frm.doc.name
                    },
                    callback: function(r) {
                        if (response.message === "success") {
                            frappe.show_alert({
                                message: __("Execution Completed"),
                                indicator: "green"
                            });
                            frm.reload_doc();  // Refresh the document to show updated fields
                        } else {
                            frappe.show_alert({
                                message: __("Could not complete execution"),
                                indicator: "red"
                            });
                        }
                    }
                });
            },"Actions");
        }
        if (frm.doc.status == "In Process")
        {
            frm.add_custom_button(__('Sync BOQ Items'), () => {
                if (frm.doc.boq) {
                    syncBOQItems(frm.doc.boq, frm);
                } else {
                    frappe.msgprint(__('Please select a BOQ first.'));
                }
            });
            }
	},
    get_project_employees_and_tasks: function(frm,project) {
        console.log("get_project_employees")
        console.log("project",frm.doc.project)

        if (project) {

            console.log("project")
            console.log(project)
            // Call the server-side method to get filtered project employees
            frappe.call({
                method: "digitz_erp.api.boq_api.get_project_employees",
                args: {
                    project: project
                },
                callback: function(r) {
                    if (r.message) {
                        console.log("employees",r.message)
                        // Clear existing child table entries
                        frm.clear_table("project_employees");
                        
                        // Add the fetched employees to the project_employee table
                        r.message.forEach(employee => {
                            let row = frm.add_child("project_employees");
                            row.employee = employee.employee; 
                            row.employee_name = employee.employee_name;
                            row.per_hour_rate = employee.per_hour_rate;
                            row.department = employee.department;
                            row.designation = employee.designation;

                        });

                        frm.refresh_field("project_employees");
                    }
                }
            });

            frappe.call({
                method: "digitz_erp.api.boq_api.get_project_tasks",
                args: {
                    project: project
                },
                callback: function(r) {
                    if (r.message) {
                                               
                        // Add the fetched employees to the project_employee table
                        r.message.forEach(task => {
                            let row = frm.add_child("project_tasks");
                            row.task = task.task;
                            row.task_name = task.task_name;
                            row.task_description = task.task_description;
                            row.expected_end_date = task.expected_start_date;
                            row.expected_end_date = task.expected_end_date;
                            row.actual_start_date = task.actual_start_date;
                            row.actual_end_date = task.actual_end_date                            

                        });

                        frm.refresh_field("project_tasks");
                    }
                }
            });
        } else {
            frm.clear_table("project_employees");
            frm.refresh_field("project_employees");
            frm.clear_table("project_tasks");
            frm.refresh_field("project_tasks");
        }
    },
    boq(frm){

        if (frm.doc.boq)
        {
            console.log("frm.doc.boq",frm.doc.boq)
            frm.trigger("getProjectByBOQ");
            frm.trigger("getBOQItems")
            
        }
    },    
    getProjectByBOQ(frm) {

        boq = frm.doc.boq
        frappe.call({
            method: "digitz_erp.api.boq_api.get_project_for_boq",
            args: {
                boq_name: boq
            },
            callback: function(r) {
                if (r.message) {

                    let project = r.message;
                       
                    // Optionally, set the project information in specific fields on the form
                    frm.set_value('project', project.name);
                    frm.set_value('expected_start_date', project.expected_start_date)
                    frm.set_value('expected_end_date', project.expected_end_date)

                    console.log("get_project_employees",project.name)                    
                    frm.events.get_project_employees_and_tasks(frm, project.name);
                   
                } else {
                    frappe.msgprint(__('No project found for the specified BOQ.'));
                }
            }
        });
    },    
    getBOQItems(frm) {

        boq = frm.doc.boq

        console.log("boq",boq)
        frappe.call({
            method: "digitz_erp.api.boq_api.get_boq_items",
            args: {
                boq_name: boq
            },
            callback: function(r) {
                if (r.message) {
                    // Clear existing items in boq_execution_items table
                    frm.clear_table("boq_execution_items");
                    console.log("r.message",r.message)
                    
                    // Populate boq_execution_items with fetched data
                    r.message.forEach(item => {
                        let row = frm.add_child("boq_execution_items");
                        row.item = item.item;
                        row.description = item.description;
                        row.item_group = item.item_group;
                        row.item_group_description = item.item_group_description;
                        row.quantity = item.quantity;
                        row.balance_quantity = item.quantity
                        row.unit = item.unit
                    });
    
                    frm.refresh_field("boq_execution_items");
                    frm.events.show_a_message(frm,"BOQ items have been added to the table.");
                } else {
                    frm.events.show_a_message(frm,"No items found in the selected BOQ.");
                }
            }
        });
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
    edit_posting_date_and_time: function (frm) {
        const readOnly = frm.doc.edit_posting_date_and_time ? 0 : 1;
        frm.set_df_property("posting_date", "read_only", readOnly);
        frm.set_df_property("posting_time", "read_only", readOnly);
      },   
});


function syncBOQItems(boq_name, frm) {
    frappe.call({
        method: "digitz_erp.api.boq_api.get_boq_items",
        args: {
            boq_name: boq_name
        },
        callback: function(r) {
            if (r.message) {
                let boqItems = r.message;

                // Create a set of item names from the BOQ items for quick lookup
                let boqItemNames = new Set(boqItems.map(item => item.item));

                // Identify items in boq_execution_items that need to be removed
                let itemsToRemove = frm.doc.boq_execution_items.filter(execution_item => 
                    !boqItemNames.has(execution_item.item)
                );

                // Identify items in BOQ that need to be added to boq_execution_items
                let itemsToAdd = boqItems.filter(boqItem => 
                    !frm.doc.boq_execution_items.some(execution_item => execution_item.item === boqItem.item)
                );

                // Display relevant messages based on the actions taken
                if (itemsToRemove.length === 0 && itemsToAdd.length === 0) {
                    frappe.msgprint(__('No amendments available in the BOQ.'));
                    return;
                } else if (itemsToAdd.length > 0 && itemsToRemove.length === 0) {
                    frappe.msgprint(__('New items have been added to BOQ Execution Items.'));
                } else if (itemsToAdd.length === 0 && itemsToRemove.length > 0) {
                    frappe.msgprint(__('Some items have been removed from BOQ Execution Items as they no longer exist in the BOQ.'));
                } else if (itemsToAdd.length > 0 && itemsToRemove.length > 0) {
                    frappe.msgprint(__('BOQ Execution Items have been updated with new additions and removals based on the latest BOQ.'));
                }

                // Remove items that are no longer in the BOQ
                itemsToRemove.forEach(item => {
                    frm.get_field("boq_execution_items").grid.grid_rows
                        .filter(row => row.doc.item === item.item)[0]
                        .remove();
                });

                // Refresh the field after removal
                frm.refresh_field("boq_execution_items");

                // Add new BOQ items that are not already in `boq_execution_items`
                itemsToAdd.forEach(boqItem => {
                    let row = frm.add_child("boq_execution_items");
                    row.item = boqItem.item;
                    row.description = boqItem.description;
                    row.item_group = boqItem.item_group;
                    row.item_group_description = boqItem.item_group_description;
                    row.quantity = boqItem.quantity;
                    row.unit = boqItem.unit

                });

                // Refresh the field after addition
                frm.refresh_field("boq_execution_items");
            } else {
                frappe.msgprint(__('No items found in the selected BOQ.'));
            }
        }
    });
}