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
    calculate_qty_for_budgeted_items: function (frm) {

        console.log(1)

        // frm.doc?.budgeted_items.forEach(function (entry) {
        //     let width = entry.width || 0;
        //     let height = entry.height || 0;
        //     let area = entry.no_of_pieces || 0;
        //     entry.qty = width * height * area;
        // });      
        if (frm.doc.use_dimensions) {
            frm.doc?.budgeted_items.forEach(function (entry) {

                console.log("entry")
                console.log(entry)

                let width = entry.width || 0;
                let height = entry.height || 0;
                let area = entry.no_of_pieces || 0;
                entry.qty = width * height * area;
                console.log("entry.qty")
                console.log(entry.qty)
            });

            frm.refresh_field("budgeted_items");
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
                            'fieldname': ['default_warehouse', 'rate_includes_tax', 'delivery_note_integrated_with_sales_invoice', 'update_price_list_price_with_sales_invoice', 'use_customer_last_price', 'customer_terms', 'update_stock_in_sales_invoice', 'allow_budgeted_item_to_be_purchased', 'allow_purchase_with_dimensions', 'allow_purchase_with_dimensions_2']
                        },
                        callback: (r2) => {

                            console.log(r2, r2)

                            frm.set_value("target_warehouse", r2.message.default_warehouse)

                            frm.refresh_field("target_warehouse");

                            frm.set_value("allow_against_budget", r2.message.allow_budgeted_item_to_be_purchased)

                            console.log("allow_budgeted_item_to_be_purchased", r2.message.allow_budgeted_item_to_be_purchased)

                            frm.set_df_property("allow_against_budget", "hidden", r2.message.allow_budgeted_item_to_be_purchased ? 0 : 1);
                            frm.set_df_property("use_dimensions", "hidden", r2.message.allow_purchase_with_dimensions ? 0 : 1);
                            frm.set_df_property("use_dimensions_2", "hidden", r2.message.allow_purchase_with_dimensions_2 ? 0 : 1);

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

        // Ensure item is selected
        if (!row.item) {
            frappe.msgprint("Please select an item.");
            return;
        }

        frappe.db.get_value('Item', row.item, ['item_name', 'description','height','width','area','length'], (r) => {
            if (r) {
                
                // Update the row with fetched values
                frappe.model.set_value(cdt, cdn, 'item_name', r.item_name || '');
                frappe.model.set_value(cdt, cdn, 'description', r.description || '');

                frappe.model.set_value(cdt, cdn, 'height', r.height || 0);
                frappe.model.set_value(cdt, cdn, 'width', r.width || 0);
                frappe.model.set_value(cdt, cdn, 'area', r.area || 0);
                frappe.model.set_value(cdt, cdn, 'length', r.area || 0);
                
                // Refresh the field to ensure updates are visible in the child table
                frm.refresh_field('items');

                console.log("here")

            }
        });
        

        
        row.height = r.message.height
        row.width = r.message.width
        row.area = r.message.area
        row.length = r.message.length

        check_budget_utilization(frm, cdt, cdn, row.item);

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

function check_budget_utilization(frm, cdt, cdn, item) {
    const row = frappe.get_doc(cdt, cdn);

    // Ensure the item field is filled before proceeding
    if (!row.item) {
        return;
    }

    // Call server method to get budget details
    frappe.call({
        method: "digitz_erp.api.accounts_api.get_balance_budget_value",
        args: {
            reference_type: "Item",
            reference_value: item,
            transaction_date: frm.doc.transaction_date || frappe.datetime.nowdate(),
            company: frm.doc.company,
            project: frm.doc.project || null,
            cost_center: frm.doc.cost_center || null
        },
        callback: function (response) {
            if (response && response.message) {
                const result = response.message;

                // Log the response for debugging
                console.log("Budget Result:", result);

                if (!result.no_budget) {
                    // Display budget details if available
                    const details = result.details || {};
                    const budgetMessage = `
                        <strong>Budget Against:</strong> ${details["Budget Against"] || "N/A"}<br>
                        <strong>Reference Type:</strong> ${details["Reference Type"] || "N/A"}<br>
                        <strong>Budget Amount:</strong> ${details["Budget Amount"] || 0}<br>
                        <strong>Utilized Amount:</strong> ${details["Used Amount"] || 0}<br>
                        <strong>Remaining Balance:</strong> ${details["Available Balance"] || 0}
                    `;

                    // Custom method to display the message (replace with your own if needed)

                    frm.events.show_a_message(frm, budgetMessage);

                }
            } else {
                // Handle case where no response is received
                frappe.msgprint({
                    title: __("Error"),
                    indicator: "red",
                    message: __("No response received from the server.")
                });
            }
        }
    });
}


frappe.ui.form.on('Material Request Item Estimate', {

    item: function (frm, cdt, cdn) {

        let row = locals[cdt][cdn];

        console.log("row.item_code", row.item_code)
        check_budget_utilization(frm, cdt, cdn, row.item_code);

        // Ensure target warehouse is selected
        if (!frm.doc.target_warehouse) {
            row.item = ""; // Reset the item if target warehouse is not selected
            frappe.msgprint("Please select target warehouse.");
            frm.refresh_field("items"); // Refresh the items table to reflect changes
            return; // Exit if target warehouse is not selected
        }

        row.target_warehouse = frm.doc.target_warehouse;
        row.project = frm.doc.project
        row.schedule_date = frm.doc.schedule_date

        // Refresh the items table to reflect the changes
        frm.refresh_field("budgeted_items");

    },
    // qty: function (frm, cdt, cdn) {
    //     console.log("qty selected.")
    //     let row = locals[cdt][cdn];
    //     console.log("qty")
    //     frm.trigger("calculate_rows_for_budgeted_items");
    // },
    height: function (frm, cdt, cdn) {
        console.log("height")
        let row = locals[cdt][cdn];
        frm.trigger("calculate_qty_for_budgeted_items");
    },
    width: function (frm, cdt, cdn) {
        console.log("width")
        let row = locals[cdt][cdn];
        frm.trigger("calculate_qty_for_budgeted_items");
    },
    no_of_pieces: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        console.log("no_of_pieces")
        frm.trigger("calculate_qty_for_budgeted_items");
    }

})