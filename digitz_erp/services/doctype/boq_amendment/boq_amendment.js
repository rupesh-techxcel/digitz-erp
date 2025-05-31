// Copyright (c) 2024,   and contributors
// For license information, please see license.txt

frappe.ui.form.on("BOQ Amendment", {
	show_a_message: function (frm,message) {
		frappe.call({
			method: 'digitz_erp.api.settings_api.show_a_message',
			args: {
				msg: message
			}
		});
	},
    refresh: function(frm) {
        // Check if the option field is set to "Delete"
        if (frm.is_new())
        {
            // frm.trigger("fill_boq_items")
            make_taxes_and_totals(frm);
             
            if(frm.doc.option =="Deduction")
            {
                frm.events.show_a_message(frm,"The BOQ Amendment with the 'Deduction' option requires that the item to be deleted is kept in the document, rather than keeping the other items.")
            }
        }
    },
    setup: function (frm) {
      frm.fields_dict["boq_items"].grid.get_field("item").get_query = function () {
          return {
              filters: {
                  item_type: ["in", ["BOQ Product", "Product"]]
              }
          };
      };
    },   
    before_cancel:function(frm)
    {
        return new Promise((resolve, reject) => {
            frappe.confirm(
                'The original BOQ changes needs to fixed manually. Are you sure you want to cancel the document?',
                function () {
                    // User confirmed, proceed with submission
                    resolve();
                },
                function () {
                    // User canceled, stop submission
                    // frappe.msgprint('Submission canceled.');
                    reject();
                }
            );
        });

    },
    before_submit: function (frm) {
        // Show confirmation dialog
        return new Promise((resolve, reject) => {

            if (frm.doc.option === "Deduction") {
                
                // Show a confirmation dialog with the redrafted message
                
                frappe.confirm(
                    "The BOQ Amendment with the 'Deduction' option requires that the item to be deleted is kept in the document, rather than keeping the other items. Are you sure you want to proceed?",
                    function () {
                        // User confirmed, proceed with submission
                        resolve();
                    },
                    function () {
                        // User canceled, stop submission
                        frappe.msgprint('Submission canceled.');
                        reject();
                    }
                );
            }
            else
            {
                frappe.confirm(
                    'The BOQ Amendments cannot be undone. Are you sure you want to submit the document?',
                    function () {
                        // User confirmed, proceed with submission
                        resolve();
                    },
                    function () {
                        // User canceled, stop submission
                        frappe.msgprint('Submission canceled.');
                        reject();
                    }
                );
            }
          
        });
    },
    edit_posting_date_and_time: function (frm) {
        const readOnly = frm.doc.edit_posting_date_and_time ? 0 : 1;
        frm.set_df_property("posting_date", "read_only", readOnly);
        frm.set_df_property("posting_time", "read_only", readOnly);
    },
    fill_boq_items(frm)
    {
        
        console.log("frm.doc.option_field",frm.doc.option_field)
       
        if (frm.doc.option_field === "Delete" && frm.doc.boq_reference) {

            frm.clear_table('boq_items');
            
            // Call the server-side method to fetch items from BOQ
            frappe.call({
                method: "digitz_erp.api.boq_api.fetch_items_from_boq",
                args: {
                    boq_reference: frm.doc.boq_reference
                },
                callback: function(r) {
                    if (r.message) {
                        
                        // Iterate over the fetched items and add them to boq_items child table
                        $.each(r.message, function(i, item) {
                            let new_row = frm.add_child('boq_items');

                            console.log("item",item)

                            new_row.item_code = item.item_code;
                            new_row.item_name = item.item_name;
                            new_row.description = item.description;
                            new_row.item_group = item.item_group;
                            new_row.item_group_description = item.item_group_description;
                            new_row.quantity = item.quantity;
                            new_row.unit = item.unit
                            new_row.rate = item.rate;
                            new_row.rate_includes_tax = item.rate_includes_tax
                            new_row.tax_excluded = item.tax_excluded                            
                            new_row.tax = item.tax
                            new_row.tax_rate = item.tax_rate
                            new_row.rate_excluded_tax = item.rate_excluded_tax
                            new_row.gross_amount = item.gross_amount;
                            new_row.tax_amount = item.tax_amount;
                            new_row.net_amount = item.net_amount;
                            
                        });

                        frappe.msgprint(__('Items fetched from BOQ and added to the BOQ Amendment.'));
                    }
                }
            });
        }
    },
    });
    
    function make_taxes_and_totals(frm) {
        console.log("from make_taxes_and_totals");
        let total_amount = 0;

        frm.doc.boq_items.forEach((entry) => {
        if (entry.rate_includes_tax) {
        // Disclaimer: Since tax is calculated after discounted amount, this implementation
        // has a mismatch with it. But still, it is straightforward than the other way.
            if (entry.tax_rate > 0) {
                const tax_in_rate = entry.rate * (entry.tax_rate / (100 + entry.tax_rate));
                entry.rate_excluded_tax = entry.rate - tax_in_rate;
                entry.tax_amount = (entry.quantity * entry.rate) * (entry.tax_rate / (100 + entry.tax_rate));
            } else {
                entry.rate_excluded_tax = entry.rate;
                entry.tax_amount = 0;
            }
        entry.net_amount = (entry.quantity * entry.rate);
        entry.gross_amount = entry.net_amount - entry.tax_amount;
        } else {
        console.log("rate not includes tax");
        entry.rate_excluded_tax = entry.rate;

        if (entry.tax_rate > 0) {
            console.log("tax_rate", entry.tax_rate);
            console.log("entry.rate", entry.rate);
            entry.tax_amount = (entry.quantity * entry.rate) * (entry.tax_rate / 100);
            console.log("tax_amount", entry.tax_amount);
            entry.net_amount = entry.quantity * entry.rate + entry.tax_amount;
        } else {
            entry.tax_amount = 0;
            entry.net_amount = entry.quantity * entry.rate;
        }

            console.log("entry.tax_amount", entry.tax_amount);
            console.log("Net amount:", entry.net_amount);
            entry.gross_amount = entry.quantity * entry.rate_excluded_tax;
        }

        total_amount += entry.net_amount;
        });

        if(frm.doc.option == "Addition")
        {
            frm.set_value("total_addition", total_amount);
        }
        else
        {
         frm.set_value("total_deduction", total_amount);
        }

        frm.refresh_field("boq_items");
        
    }

    frappe.ui.form.on('BOQ Item In Amendment', {

        item: function (frm, cdt, cdn) {
            let row = locals[cdt][cdn];
            let tax_excluded_for_company = false;
        
            // Backup item value to ensure it persists
            const currentItem = row.item;
        
            if (!currentItem) {
                frappe.msgprint("Please select a valid item.");
                return;
            }
        
            // Get company settings (synchronous call)
            frappe.call({
                method: "digitz_erp.api.settings_api.get_company_settings",
                async: false,
                callback: (r) => {
                    if (r.message && r.message.length > 0) {
                        tax_excluded_for_company = r.message[0].tax_excluded;
                    }
                },
            });
        
            // Fetch item details
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Item",
                    filters: { item_code: currentItem },
                    fieldname: ["item_name", "description", "base_unit", "tax", "tax_excluded"],
                },
                callback: (r) => {
                    if (r.message) {
                        // Update row fields
                        Object.assign(row, {
                            item_name: r.message.item_name,
                            description: r.message.description || r.message.item_name,
                            base_unit: r.message.base_unit,
                            unit: r.message.base_unit,
                            conversion_factor: 1,
                            tax_excluded: tax_excluded_for_company ? true : r.message.tax_excluded,
                        });
        
                        // Handle tax details if tax is not excluded
                        if (!row.tax_excluded) {
                            frappe.call({
                                method: "frappe.client.get_value",
                                args: {
                                    doctype: "Tax",
                                    filters: { tax_name: r.message.tax },
                                    fieldname: ["tax_name", "tax_rate"],
                                },
                                callback: (r2) => {
                                    if (r2.message) {
                                        row.tax = r2.message.tax_name;
                                        row.tax_rate = r2.message.tax_rate;
                                        frm.refresh_field("boq_items");
                                    }
                                },
                            });
                        } else {
                            row.tax = "";
                            row.tax_rate = 0;
                        }
        
                        row.rate_includes_tax = frm.doc.rate_includes_tax;
        
                        // Refresh the child table
                        frm.refresh_field("boq_items");
        
                        // Check for duplicate items in the table
                        let duplicate = frm.doc.boq_items.some(
                            (existing_row) => existing_row.item === currentItem && existing_row.name !== row.name
                        );
        
                        if (duplicate) {
                            frappe.msgprint(__("Item already exists in the table."));
                            frappe.model.set_value(cdt, cdn, "item", null); // Reset the item field
                            return;
                        }
        
                        // Check if the item exists in the BOQ
                        frappe.call({
                            method: "digitz_erp.api.boq_api.check_item_in_boq",
                            args: {
                                boq_name: frm.doc.boq,
                                item_code: currentItem, // Use the backed-up item value
                            },
                            async: false,
                            callback: function (response) {
                                if (response.message) {
                                    frappe.msgprint(`Item ${currentItem} exists in BOQ ${frm.doc.boq}.`);
                                    frappe.model.set_value(cdt, cdn, "item", null); // Reset the item field
                                    frappe.model.set_value(cdt, cdn, "description", null); // Reset the item field
                                    frappe.model.set_value(cdt, cdn, "base_unit", null); // Reset the item field
                                    frappe.model.set_value(cdt, cdn, "unit", null); // Reset the item field
                                    frappe.model.set_value(cdt, cdn, "conversion_factor", null); // Reset the item field
                                    frappe.model.set_value(cdt, cdn, "tax_excluded", null); // Reset the item field
                                }
                            },
                        });
                    }
                },
            });
        
            console.log("Check item in BOQ complete");
            console.log("Row data:", row);
            console.log("BOQ:", frm.doc.boq);
            console.log("Item:", currentItem);
      },        
      quantity: function (frm) {
        make_taxes_and_totals(frm);
      },
    
      rate: function (frm) {
        make_taxes_and_totals(frm);
      },
    
      tax_rate: function (frm) {
        make_taxes_and_totals(frm);
      },
    
      tax_excluded: function (frm) {
        make_taxes_and_totals(frm);
      },
    
      rate_includes_tax: function (frm) {
        make_taxes_and_totals(frm);
      },
      boq_items_remove:function(frm)
      {
            make_taxes_and_totals(frm);
      }

    });