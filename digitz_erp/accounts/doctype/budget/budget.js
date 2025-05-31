// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Budget", {
	refresh(frm) {

        frm.fields_dict['budget_items'].grid.get_field('reference_type').get_query = function(doc, cdt, cdn) {
            var child = locals[cdt][cdn]; // Get the current child row
            return {
                filters: {
                    'budget_against': child.budget_against  // Filter based on budget_against in the current row
                }
            };
        };   
        
        
        // Set the query for reference_value dynamically
        frm.fields_dict['budget_items'].grid.get_field('reference_value').get_query = function(doc, cdt, cdn) {
            var child = locals[cdt][cdn];
            var filters = {};

            if (child.reference_type === 'Item' || child.reference_type == "Designation") {
                filters = {
                    'disabled': 0 // Show active items
                };            
            } else if (child.reference_type === 'Account') {
                filters = {
                    'is_group': 0 // Show only accounts
                };
            } else if (child.reference_type === 'Account Group') {
                filters = {
                    'is_group': 1 // Show only account groups
                };
            }

            return {
                filters: filters
            };
        };


        create_custom_buttons(frm)

	},
    setup(frm) {
        frm.trigger('get_default_company_and_warehouse');
    },
    validate: function(frm) {
        frm.doc.budget_items.forEach(item => {
            if (item.budget_against === 'Labour' && frm.doc.budget_against !== 'Project') {
                frappe.throw(__('Labour budget items are only allowed when Budget Against is set to Project.'));
            }
        });
    },

    get_default_company_and_warehouse(frm) {

		var default_company = ""

		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				'doctype': 'Global Settings',
				'fieldname': 'default_company'
			},
			callback: (r) => {

				default_company = r.message.default_company
				
                frm.set_value("company",default_company)
				
				
			}
		})

	},
    project: function(frm) {
        let project = frm.doc.project;
        console.log("Selected Project:", project);
    
        if (project) {

            frappe.call(
				{
				method: 'frappe.client.get_value',
				args: {
				  'doctype': 'Project',
				  'filters': { 'name': project },
				  'fieldname': ['project_maximum_allowable_budget', 'estimated_material_cost']
				},
				callback: (r) => {
				    const maximumAllowed = r.message.project_maximum_allowable_budget;
                    const estimatedMaterialCost = r.message.estimated_material_cost;

                    frm.set_value('project_estimated_material_cost', estimatedMaterialCost);

                    if (maximumAllowed > 0 && estimatedMaterialCost != undefined) {
                        const allowedBudget = estimatedMaterialCost * (maximumAllowed / 100);
                        frm.set_value('project_estimated_material_cost', allowedBudget);
                    } 
				}
				});
        } 
    },
    
});

frappe.ui.form.on("Budget Item", {

    budget_against: function(frm, cdt, cdn) {
        // Clear the reference_type when budget_against changes
        frappe.model.set_value(cdt, cdn, 'reference_type', "");
    
        let row = frappe.get_doc(cdt, cdn);
        
        if (row.budget_against === 'Labour' && frm.doc.budget_against !== 'Project') {
            frappe.msgprint({
                title: __('Not Allowed'),
                message: __('Labour can only be selected if Budget Against is set to Project in the parent.'),
                indicator: 'red'
            });
            frappe.model.set_value(cdt, cdn, 'budget_against', '');
        }    
    },

    reference_type: function(frm, cdt, cdn) {
        // Get the current row of the child table
        var child = locals[cdt][cdn];

        // Set the hidden field value based on reference_type
        if (child.reference_type === 'Account Group') {
            frappe.model.set_value(cdt, cdn, 'link_field_hidden', '');
            frappe.model.set_value(cdt, cdn, 'link_field_hidden', 'Account');
        } else {
            frappe.model.set_value(cdt, cdn, 'link_field_hidden', child.reference_type);
        }

        console.log("child.reference_type", child.reference_type)

        
    },
    budget_amount: function(frm, cdt, cdn) {
        // Get the specific row that triggered the event
        var child = locals[cdt][cdn];

        // Initialize total budget amount
        let total_budget_amount = 0;

        // Iterate through each row in the child table
        frm.doc.budget_items.forEach(row => {
            // Accumulate the total budget amount from each row
            total_budget_amount += row.budget_amount || 0; // Handle undefined/null values
        });

        // Update the total budget amount in the parent document
        frm.set_value('total_budget_amount', total_budget_amount);
    }
});

let create_custom_buttons = function(frm){
	
    if(!frm.doc.company){
        // Make sure default company is set
        frm.trigger('get_default_company_and_warehouse');

    }
    if(frm.doc.docstatus < 1){

        frappe.db.get_value('Company', frm.doc.company, 'allow_estimated_items_budgeting', function(r){

            if(r.allow_estimated_items_budgeting)
            {
                frm.add_custom_button('Get Items from Estimate',() =>{
                    get_items_from_estimate(frm)
                });	
            }
        });
    }
}

let get_items_from_estimate = function (frm) {
    if (!frm.doc.project) {
        frappe.msgprint('Please set the Project field in the document before fetching items.');
        return;
    }

    frappe.call({
        method: 'digitz_erp.api.budget_api.get_items_from_estimate',
        args: {
            project: frm.doc.project, // Use the project's field value from the document
        },
        callback: function (r) {
            if (r.message) {
                let data = r.message;
                let dialog = new frappe.ui.Dialog({
                    title: 'Select Estimation Items',
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'instruction',
                            options: `<p style="color: red; font-weight: bold;">Please select the items to add to the budget.</p>`,
                        },
                        {
                            fieldtype: 'Table',
                            fieldname: 'popup_table',
                            label: 'Estimation Items',
                            fields: [                                
                                {
                                    fieldtype: 'Data',
                                    fieldname: 'Item',
                                    label: 'Item',
                                    read_only: 1,
                                    in_list_view: 1,
                                },
                                {
                                    fieldtype: 'Float',
                                    fieldname: 'Quantity',
                                    label: 'Quantity',
                                    read_only: 1,
                                    in_list_view: 1,
                                },
                                {
                                    fieldtype: 'Currency',
                                    fieldname: 'Rate',
                                    label: 'Rate',
                                    read_only: 1,
                                    in_list_view: 1,
                                },
                                {
                                    fieldtype: 'Currency',
                                    fieldname: 'Amount',
                                    label: 'Amount',
                                    read_only: 1,
                                    in_list_view: 1,
                                },
                            ],
                            data: data,
                            get_data: () => data,
                        },
                    ],
                    primary_action_label: 'Save',
                    primary_action: function () {
                        let selected_items = dialog.fields_dict.popup_table.grid.get_selected_children();
                        if (selected_items.length > 0) {
                            selected_items.forEach(item => {
                                // Check if the item already exists in the child table
                                let exists = frm.doc.budget_items.some(existing_item => existing_item.reference_value === item.Item);
                                
                                if (!exists) {
                                    // Populate the child table in Budgeting only if the item doesn't exist
                                    let child = frm.add_child('budget_items');
                                    frappe.model.set_value(child.doctype, child.name, {
                                        budget_against: 'Purchase',
                                        reference_type: 'Item',
                                        reference_value: item.Item,
                                        budget_amount: item.Amount,
                                    });
                                }
                            });
                            frm.refresh_field('budget_items'); // Refresh the field to show updated values
                        } else {
                            frappe.msgprint('Please select at least one item.');
                        }
                        dialog.hide();
                    },
                });

                dialog.$wrapper.find('.modal-dialog').css("max-width", "90%").css("width", "65%");
                
                dialog.show();

            } else {
                frappe.msgprint('No items found for the selected project.');
            }
        },
    });
};
