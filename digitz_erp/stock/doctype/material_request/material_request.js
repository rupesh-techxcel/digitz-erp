// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Material Request", {

    show_a_message: function (frm, message) {
        frappe.call({
            method: 'digitz_erp.api.settings_api.show_a_message',
            args: {
                msg: message
            }
        });
    },
    use_dimensions(frm)
	{
		toggle_use_dimensions(frm)
	},
	use_dimensions_2(frm)
	{
		toggle_use_dimensions_2(frm)
	},

    // async setup(frm) {
    //     if(frm.is_new()){
    //         frm.set_value('company', await frappe.db.get_single_value("Global Settings","default_company"));
    //         let company = await frappe.db.get_doc("Company", cur_frm.doc.company);
    //         console.log("Hello", company.allow_purchase_with_dimensions)
    //         await frm.set_value("target_warehouse", company.default_warehouse)
    //         await frm.set_value("allow_against_budget", company.allow_budgeted_item_to_be_purchased)
    //         await frm.set_df_property("allow_against_budget", "hidden", company.allow_budgeted_item_to_be_purchased);
    //         await frm.set_df_property("use_dimensions", "hidden", company.allow_purchase_with_dimensions?0:1);    
    //     }       
    // },

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
                    callback: function (r) {

                        console.log("r.message")

                        console.log(r.message)

                        if (r.message === true) {  // Check if server-side method returned True
                            frm.add_custom_button(__("Create Purchase Order"), () => {

                                frappe.call({
                                    method: "digitz_erp.api.purchase_order_api.create_purchase_order_from_material_request",
                                    args: {
                                        material_request: frm.doc.name
                                    },
                                    callback: function (r) {
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
    calculate_qty: function (frm) {

        // frm.doc?.items.forEach(function (entry) {
        //     let width = entry.width || 0;
        //     let height = entry.height || 0;
        //     let area = entry.no_of_pieces || 0;
        //     entry.qty = width * height * area;
        // });      
        if (frm.doc.use_dimensions) {
            frm.doc?.items.forEach(function (entry) {
                let width = entry.width || 0;
                let height = entry.height || 0;
                let area = entry.no_of_pieces || 0;
                entry.qty = width * height * area;
            });

            frm.refresh_field("items");
        }
    },    
    approve_all_items: function (frm) {
        // Iterate through all rows in the 'items' child table
        $.each(frm.doc.items, function (index, row) {
            row.qty_approved = row.qty; // Set approved_quantity to match quantity
        });

        frm.set_value('approved', true)

        // Refresh the child table to reflect the changes in the UI
        frm.refresh_field('items');

        frappe.msgprint(__('All quantities have been approved successfully.'));
    },
    edit_posting_date_and_time(frm) {
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
        // var default_company = ""
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
                            'fieldname': ['default_warehouse', 'rate_includes_tax', 'delivery_note_integrated_with_sales_invoice', 'update_price_list_price_with_sales_invoice', 'use_customer_last_price', 'customer_terms', 'update_stock_in_sales_invoice','allow_purchase_with_dimensions', 'allow_purchase_with_dimensions_2']
                        },
                        callback: (r2) => {

                            console.log(r2, r2)

                            frm.set_value("target_warehouse", r2.message.default_warehouse)

                            frm.refresh_field("target_warehouse");

                           

                            console.log("allow_budgeted_item_to_be_purchased", r2.message.allow_budgeted_item_to_be_purchased)

                           // Update field properties for "use_dimensions" and "use_dimensions_2"
								frm.set_value("use_dimensions",r.allow_purchase_with_dimensions)
								frm.set_value("use_dimensions_2",r.allow_purchase_with_dimensions_2)
								toggle_dimension_fields(frm);
                        }
                    }
                )
            }
        })
    },
    assign_defaults(frm) {
        if (frm.is_new()) {
            frm.trigger("get_default_company_and_warehouse");
          
        }
    },
});

frappe.ui.form.on("Material Request", "onload", function (frm) {

    frm.trigger("assign_defaults")

});


frappe.ui.form.on('Material Request Item', {

    // Triggered when the item field is changed
    item: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        console.log("from item method")

        // Ensure item is selected
        if (!row.item) {
            frappe.msgprint("Please select an item.");
            return;
        }

        // check_budget_utilization(frm, cdt, cdn, row.item,row.item_group);

        frappe.db.get_value('Item', row.item, ['item_name', 'description','height','width','area','length'], (r) => {
            if (r) {
                
                // Update the row with fetched values
                frappe.model.set_value(cdt, cdn, 'item_name', r.item_name || '');
                frappe.model.set_value(cdt, cdn, 'display_name', r.description || '');

                frappe.model.set_value(cdt, cdn, 'height', r.height || 0);
                frappe.model.set_value(cdt, cdn, 'width', r.width || 0);
                frappe.model.set_value(cdt, cdn, 'area', r.area || 0);
                frappe.model.set_value(cdt, cdn, 'length', r.area || 0);
                
                // Refresh the field to ensure updates are visible in the child table
                frm.refresh_field('items');

                console.log("here")

            }
        });

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
    unit: function (frm, cdt, cdn) {
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
            callback: function (r) {
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
    },
    // qty: function (frm, cdt, cdn) {
    //     console.log("qty selected.")
    //     let row = locals[cdt][cdn];
    //     console.log("qty")
    //     frm.trigger("calculate_rows");
    // },
    height: function (frm, cdt, cdn) {
        console.log("height")
        let row = locals[cdt][cdn];
        frm.trigger("calculate_qty");
    },
    width: function (frm, cdt, cdn) {
        console.log("width")
        let row = locals[cdt][cdn];
        frm.trigger("calculate_qty");
    },
    no_of_pieces: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        console.log("no_of_pieces")
        frm.trigger("calculate_qty");
    }

});

function check_budget_utilization(frm, cdt, cdn, item, item_group) {
    const row = frappe.get_doc(cdt, cdn);

    console.log("from check_budget method");

    if (!row.item) {
        return;
    }

    // Call server method to get budget details
    frappe.call({
        method: "digitz_erp.api.accounts_api.get_balance_budget_value",
        args: {
            reference_type: "Item",
            reference_value: item,
            doc_type: "Material Request",
            doc_name: frm.doc.name,
            transaction_date: frm.doc.posting_date || frappe.datetime.nowdate(),
            company: frm.doc.company,
            project: frm.doc.project || null,
            cost_center: frm.doc.default_cost_center || null
        },
        callback: function (response) {
            if (response && response.message) {
                const result = response.message;
                console.log("Budget Result:", result);

                if (!result.no_budget) {
                    const details = result.details || {};
                    
                    const budget_amount = Number(details["Budget Amount"]) || 0;
                    let used_amount = Number(details["Used Amount"]) || 0;
                    const available_balance = Number(details["Available Balance"]) || 0;

                    const ref_type = details["Reference Type"];
                    let total_map = 0;

                    // Iterate through items dynamically based on reference type
                    frm.doc.items.forEach(row => {
                        let qty = Number(row.qty) || 0;
                        let valuation_rate = Number(row.valuation_rate) || 0;

                        if (ref_type === "Item" && row.item === item) {
                            total_map += qty * valuation_rate;
                        } else if (ref_type === "Item Group" && row.item_group === item_group) {
                            total_map += qty * valuation_rate;
                        }
                    });

                    used_amount += total_map;

                    if (budget_amount < used_amount) {
                        row.item = "";
                        frm.events.show_a_message("Over budget allocation!!!");
                    }

                    // Fetch item valuation rate
                    frappe.call({
                        method: 'digitz_erp.api.items_api.get_item_valuation_rate_default',
                        async: false,
                        args: {
                            'item': row.item,
                            'posting_date': frm.doc.posting_date,
                            'posting_time': frm.doc.posting_time
                        },
                        callback(r) {
                            console.log("Valuation rate in console", r.message);

                            if (r.message == 0) {
                                frappe.throw("No valuation rate has been specified for the item, " + row.item + ". Please update the Item Master with the appropriate valuation rate to proceed.");
                                row.item = "";
                                frm.refresh_field("items");
                            } else {
                                row.valuation_rate = r.message;

                                if (!frm.doc.project) {
                                    frm.events.show_a_message(frm, "Please select a project if required.");
                                }

                                const budgetMessage = `
                                    <strong>Budget Against:</strong> ${details["Budget Against"] || "N/A"}<br>
                                    <strong>Reference Type:</strong> ${details["Reference Type"] || "N/A"}<br>
                                    <strong>Budget Amount:</strong> ${budget_amount}<br>
                                    <strong>Utilized Amount:</strong> ${used_amount}<br>
                                    <strong>Remaining Balance:</strong> ${available_balance}
                                `;

                                row.available_amount_in_budget = available_balance
                            
                                frm.events.show_a_message(frm, budgetMessage);
                            }
                        }
                    });
                }
            } else {
                frappe.msgprint({
                    title: __("Error"),
                    indicator: "red",
                    message: __("No response received from the server.")
                });
            }
        }
    });
}

function toggle_use_dimensions(frm) {
    console.log("from toggle_use_dimensions");

    const hide = frm.doc.use_dimensions === 0;  // You want to show when it's TRUE, so hide when FALSE

	const fields_to_toggle = ['width', 'height', 'no_of_pieces'];

	console.log("hide")
	console.log(hide)

    fields_to_toggle.forEach(field => {
        frm.fields_dict.items.grid.update_docfield_property(field, "hidden", hide);
    });

    // Re-render the grid
    frm.fields_dict.items.grid.refresh();
}

function toggle_use_dimensions_2(frm) {
    console.log("from toggle_use_dimensions_2");

    const hide = frm.doc.use_dimensions_2 === 0;
    const fields_to_toggle = ['length', 'weight_per_meter', 'rate_per_kg'];

    fields_to_toggle.forEach(field => {
        frm.fields_dict.items.grid.update_docfield_property(field, 'hidden', hide);
    });
}

function toggle_dimension_fields(frm) {
    toggle_use_dimensions(frm);
    toggle_use_dimensions_2(frm);
    frm.refresh_fields("items");
}