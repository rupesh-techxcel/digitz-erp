// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Material Request", {

    show_a_message: function (frm,message) {
		frappe.call({
			method: 'digitz_erp.api.settings_api.show_a_message',
			args: {
				msg: message
			}
		});
	},

    setup(frm)
    {
        frm.fields_dict['items'].grid.get_field('item').get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    item_type: ['in', ['BOQ Product', 'Product','Material']]
                }
            };
          }

          frm.set_query("source_warehouse", function() {
			return {
				"filters": {
					"disabled": 0
				}
			};
		});
		frm.set_query("target_warehouse", function() {
			return {
				"filters": {
					"disabled": 0
				}
			};
		});

		frm.fields_dict['items'].grid.get_field('source_warehouse').get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    disabled: 0
                }
            };
		}
		frm.fields_dict['items'].grid.get_field('target_warehouse').get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    disabled: 0
                }
            };
		}
    },
	refresh(frm) {
        if (!frm.is_new() && frm.doc.docstatus == 1) {
    
            // For Stock Transfer type
            if (frm.doc.material_request_type == "Stock Transfer") {
                frm.add_custom_button(__("Stock Transfer"), () => {
                    console.log("Stock Transfer");
                }, __("Action"));
            }
    
            // For Purchase type, check if there are pending items
            if (frm.doc.material_request_type == "Purchase") {
    
                frappe.call({
                    method: "digitz_erp.api.purchase_order_api.check_pending_items_in_material_request",
                    args: {
                        mr_no: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message === true) {  // Check if server-side method returned True
                            frm.add_custom_button(__("Create Purchase Order"), () => {
    
                                frappe.call({
                                    method: "digitz_erp.api.purchase_order_api.create_purchase_order_from_material_request",
                                    args: {
                                        material_request: frm.doc.name
                                    },
                                    callback: function(r) {
                                        if (r.message) {
                                            // Open the Purchase Order in the UI without saving it
                                            let po_doc = frappe.model.sync([r.message])[0];
                                            frappe.set_route("Form", "Purchase Order", po_doc.name);
                                        }
                                    }
                                });
    
                            });
                        }
                    }
                });
    
            }
        }
    },    
    edit_posting_date_and_time(frm)
    {
        if (frm.doc.edit_posting_date_and_time == 1) {
			frm.set_df_property("posting_date", "read_only", 0);
			frm.set_df_property("posting_time", "read_only", 0);
		}
		else {
			frm.set_df_property("posting_date", "read_only", 1);
			frm.set_df_property("posting_time", "read_only", 1);
		}


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
				frm.doc.company = r.message.default_company
				frm.refresh_field("company");
				frappe.call(
					{
						method: 'frappe.client.get_value',
						args: {
							'doctype': 'Company',
							'filters': { 'company_name': default_company },
							'fieldname': ['default_warehouse', 'rate_includes_tax', 'delivery_note_integrated_with_sales_invoice','update_price_list_price_with_sales_invoice','use_customer_last_price','customer_terms','update_stock_in_sales_invoice']
						},
						callback: (r2) => {

							frm.doc.warehouse = r2.message.default_warehouse;
							
							frm.refresh_field("warehouse");							

						}
					}
				)
			}
		})

	},
    assign_defaults(frm)
	{
		if(frm.is_new())
		{
			frm.trigger("get_default_company_and_warehouse");

			frappe.db.get_value('Company', frm.doc.company, 'default_credit_sale', function(r) {
				if (r && r.default_credit_sale === 1) {
						// frm.set_value('credit_sale', 1);
				}
			});

		}


	},
    item(frm)
    {

    }
});

frappe.ui.form.on("Material Request", "onload", function (frm) {

	frm.trigger("assign_defaults")	

});


frappe.ui.form.on('Material Request Item', {
    
    // Triggered when the item field is changed
    item: function(frm, cdt, cdn) {
        
        let row = locals[cdt][cdn];
    
        // Ensure item is selected
        if (!row.item) {
            frappe.msgprint("Please select an item.");
            return;
        }
    
        check_budget_utilization(frm, cdt, cdn,"Item");

        // Set conversion factor to 1
        row.conversion_factor = 1;
        console.log("Item selected: ", row.item);
    
        // Ensure target warehouse is selected
        if (!frm.doc.target_warehouse) {
            row.item = ""; // Reset the item if target warehouse is not selected
            frappe.msgprint("Please select target warehouse.");
            frm.refresh_field("items"); // Refresh the items table to reflect changes
            return; // Exit if target warehouse is not selected
        }
    
        // If the purpose is "Stock Transfer", ensure source warehouse is selected
        if (frm.doc.purpose === "Stock Transfer") {
            if (!frm.doc.source_warehouse) {
                row.item = ""; // Reset the item if source warehouse is not selected
                frappe.msgprint("Please select source warehouse.");
                frm.refresh_field("items"); // Refresh the items table to reflect changes
                return; // Exit if source warehouse is not selected
            }
        }
    
        // Set source and target warehouses for the row
        row.source_warehouse = frm.doc.source_warehouse;
        row.target_warehouse = frm.doc.target_warehouse;
        row.project = frm.doc.project
        row.schedule_date = frm.doc.schedule_date
    
        // Refresh the items table to reflect the changes
        frm.refresh_field("items");
    },
    

    // Triggered when the unit field is changed
    unit: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        // Ensure the unit is selected
        if (!row.unit) {
            return;
        }

        console.log("Unit selected: ", row.unit);
        console.log("Corresponding item: ", row.item);

        // Check if the item is set before making the server call
        if (!row.item) {
            // frappe.msgprint("Please select an item before setting the unit.");
            return;
        }

        // Make the server call to validate unit for the selected item
        frappe.call({
            method: 'digitz_erp.api.items_api.get_item_uom',
            args: {
                item: row.item,   // Send the item code
                unit: row.unit    // Send the selected unit
            },
            callback: function(r) {
                // If no valid UOM is found, display an error and reset the unit and conversion factor
                if (r.message && r.message.length === 0) {
                    frappe.msgprint("Invalid unit, Unit does not exist for the selected item.");
                    frappe.model.set_value(cdt, cdn, 'unit', row.base_unit); // Reset to base unit
                    frappe.model.set_value(cdt, cdn, 'conversion_factor', 1); // Reset conversion factor
                } else {
                    // Set the conversion factor if the UOM exists
                    frappe.model.set_value(cdt, cdn, 'conversion_factor', r.message[0].conversion_factor);
                }

                // Refresh the 'items' field to reflect the changes
                frm.refresh_field("items");
            }
        });
    }
});

function check_budget_utilization(frm, cdt, cdn, reference_type) {
    const row = frappe.get_doc(cdt, cdn);

    if (!row.item) {
        
        return;
    }

    frappe.call({
        method: "digitz_erp.api.accounts_api.fetch_budget_utilization",  // Replace with the correct method path
        args: {
            reference_type: reference_type,
            reference_value: row.item,
            transaction_date: frm.doc.transaction_date || frappe.datetime.nowdate(),
            company: frm.doc.company,
            project: frm.doc.project || null,
            cost_center: frm.doc.cost_center || null,
        },
        callback: function(r) {
            if (r.message) {
                const { no_budget, utilized, budget } = r.message;

                if (no_budget) {
                    frappe.msgprint(__('No budget exists for the selected criteria.'));
                } else {
                    if (utilized > budget) {
                        frappe.throw(__('Budget exceeded! Utilized amount: {0}, Budget: {1}', [utilized, budget]));
                    } else {
						
						const message = `A budget was found for the item <b>${row.item}</b> or its associated item group. The utilized amount is <b>${utilized}</b>, while the allocated budget is <b>${budget}</b>.`;

                        frm.events.show_a_message(frm,message)
                    }
                }
            }
        }
    });
}