// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Prospect", {
	refresh: function(frm) {

        frm.set_query("area", function() {
			return {
				"filters": {
					"emirate": frm.doc.emirate
				}
			};
		});


        // Check if the prospect already exists in any customer
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Customer',
                filters: {
                    prospect: frm.doc.name
                },
                fields: ['name']
            },
            callback: function(r) {
                // If no customer exists with this prospect, show the button
                if (r.message.length === 0) {
                    frm.add_custom_button(__('Convert to Customer'), function() {
                        frappe.call({
                            method: 'digitz_erp.api.customer_api.convert_prospect_to_customer',
                            args: {
                                prospect: frm.doc.name
                            },
                            callback: function(r) {
                                if (r.message) {

                                    let doc = frappe.model.sync(r.message)[0];
                                    frappe.set_route('Form', 'Customer', doc.name);
                                    // Redirect to the newly created customer document
                                    //frappe.set_route('Form', 'Customer', r.message.name);
                                }
                            }
                        });
                    });
                }
            }
        });
    },
    emirate: function (frm) 
    {
        frm.set_value("area","")
    },
});
