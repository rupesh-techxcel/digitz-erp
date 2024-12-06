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




