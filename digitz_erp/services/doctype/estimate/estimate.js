// For license information, please see license.txt

frappe.ui.form.on("Estimate", {

    show_a_message: function (frm,message) {
        frappe.call({
            method: 'digitz_erp.api.settings_api.show_a_message',
            args: {
                msg: message
            }
        });
    },
    refresh: function (frm) {
           
        if(frm.is_new() && frm.doc.boq ==undefined)
        {
            frm.events.show_a_message(frm, "Select either the customer or prospect first, then click the 'Get Items from BOQ' button to generate an estimate based on the BOQ.");
        }
      var css = document.createElement("style");
      css.item_group = "text/css";
  
      var styles = ".row-index {display:none};";
  
      if (css.styleSheet) css.styleSheet.cssText = styles;
      else css.appendChild(document.createTextNode(styles));
      document.getElementsByTagName("head")[0].appendChild(css);
  
      // Ensure that the child table has a fieldname in camelCase
      if (frm.fields_dict.estimation_items) {
        frm.fields_dict["estimation_items"].grid.wrapper.off("click", ".grid-remove-rows");
        frm.fields_dict["estimation_items"].grid.wrapper.on("click", ".grid-remove-rows", function (e) {
            // Get the selected rows
            let selected_rows = frm.fields_dict["estimation_items"].grid.get_selected_children();
    
            if (selected_rows.length > 0) {
                selected_rows.forEach(function (removed_row) {
                    console.log("Delete Btn clicked", removed_row);
    
                    frm.doc.estimation_item_material_and_labour = frm.doc.estimation_item_material_and_labour.filter(row => row.item !== removed_row.item);
                  });
    
                // After processing all rows, refresh and reload the form
                frm.refresh_fields();
                frm.reload_doc();
            }
        });
  
      }

      if (!frm.doc.boq) {
        frm.add_custom_button(__('Get Items from BOQ'), function() {
            // Check if either customer or prospect is selected
            if (!frm.doc.customer && !frm.doc.prospect) {
                frappe.msgprint(__('Please select either a Customer or a Prospect before selecting a BOQ.'));
                return;
            }

            let d = new frappe.ui.Dialog({
                title: 'Get Items from BOQ',
                fields: [
                    {
                        label: 'BOQ',
                        fieldname: 'boq',
                        fieldtype: 'Select',
                        options: [],
                        reqd: 1
                    }
                ],
                primary_action_label: 'Get Items',
                primary_action(values) {
                    // Clear item_groups
                    frm.clear_table('item_groups');

                    // Clear estimation_items table
                    frm.clear_table('estimation_items');

                    // Set the selected BOQ to the Estimate Doctype
                    frm.set_value('boq', values.boq);
                    frm.refresh_field('boq');

                    // Fetch the selected BOQ details
                    frappe.call({
                        method: 'digitz_erp.api.boq_api.get_boq_details',
                        args: {
                            boq: values.boq
                        },
                        callback: function(r) {
                            if (r.message) {
                                let boq_data = r.message;

                                frm.set_value('use_custom_item_group_description',boq_data.use_custom_item_group_description)
                                frm.set_value('project_name', boq_data.project_name)
                                frm.set_value('project_short_name', boq_data.project_short_name)

                                // Populate item_groups in Estimate
                                boq_data.item_groups.forEach(function(group) {
                                    frm.add_child('item_groups', {
                                        item_group_name: group.item_group_name,
                                        description: group.description
                                    });
                                });
                                
                                // Populate estimation_items table in Estimate
                                boq_data.boq_items.forEach(function(item) {
                                    frm.add_child('estimation_items', {
                                        item: item.item,
                                        description: item.description,
                                        item_name: item.item_name,
                                        item_group: item.item_group,
                                        item_group_description: item.item_group_description,
                                        quantity: item.quantity
                                    });
                                });

                                // Refresh the fields to show the updated child tables
                                frm.refresh_field('item_groups');
                                frm.refresh_field('estimation_items');
                            } else {
                                frappe.msgprint(__('No details found for the selected BOQ.'));
                            }
                        }
                    });

                    d.hide();
                }
            });

            // Call the server-side method to get available BOQs
            frappe.call({
                method: 'digitz_erp.api.boq_api.get_available_boqs',
                args: {
                    lead_from: frm.doc.lead_from,
                    customer: frm.doc.customer,
                    prospect: frm.doc.prospect
                },
                callback: function(r) {
                    if (r.message) {
                        let options = r.message.map(boq => boq.name);
                        d.set_df_property('boq', 'options', options);
                        d.show();
                    } else {
                        frappe.msgprint(__('No available BOQs found for the selected prospect or customer.'));
                    }
                }
            });
        });
    }    
    },
    setup(frm)
    {
  
    },
    overhead_percentage(frm) {    
      update_estimation_totals(frm)
    },
    profit_and_margin(frm) {
      update_estimation_totals(frm)    
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
  
          var default_company = ""
  
          frappe.call({
              method: 'frappe.client.get_value',
              args: {
                  'doctype': 'Global Settings',
                  'fieldname': 'default_company'
              },
              callback: (r) => {
  
                  default_company = r.message.default_company
                  
                  frm.set_value("company", default_company);

                  frappe.db.get_value('Company', default_company, 
                    ['use_custom_item_group_description_in_estimation', 'overheads_based_on_percentage', 'width_height_applicable_in_estimate'], 
                    function (r) {
                        if (r) {
                            
                            // Set the fields on the form
                            frm.set_value('use_custom_item_group_description', r.use_custom_item_group_description_in_estimation);
                            frm.set_value('overheads_based_on_percentage',r.overheads_based_on_percentage);
                            console.log("console.log(r.overheads_based_on_percentage)")
                            console.log(r.overheads_based_on_percentage)
                            // Dynamically hide/show columns in the child table
                            // frm.fields_dict['estimation_items'].grid.set_column_disp('width_meter', !r.width_height_applicable_in_estimate);
                            // frm.fields_dict['estimation_items'].grid.set_column_disp('height_meter', !r.width_height_applicable_in_estimate);
                        }
                    }
                );

                }
          });  
      },
    assign_defaults(frm)
      {
          if(frm.is_new())
          {
              frm.trigger("get_default_company_and_warehouse");
      }
    },
  
  });
  frappe.ui.form.on('Estimation Item Group', {

    item_group_name: function(frm, cdt, cdn) {
        console.log("Processing item group");
        let row = locals[cdt][cdn];

        if (row.item_group_name) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Item Group',
                    filters: { name: row.item_group_name },
                    fieldname: 'description'
                },
                callback: function(response) {
                    console.log(response);
                    if (response.message && response.message.description) {
                        frappe.model.set_value(cdt, cdn, 'description', response.message.description);
                        frm.refresh_field('item_groups');
                    }
                },
                error: function(err) {
                    frappe.msgprint(__("Unable to fetch description. Please try again."));
                }
            });

            

        } else {
            frappe.model.set_value(cdt, cdn, 'description', '');
            frm.refresh_field('item_groups');
        }
    },
    description: function(frm, cdt, cdn) {
        console.log("descriptions")
        let row = locals[cdt][cdn];
        console.log(row)
        update_descriptions_in_items(frm,row.item_group_name, row.description)
    }
    
});


  frappe.ui.form.on("Estimate", "onload", function (frm) {
  
      frm.trigger("assign_defaults")
  
  });
  
  frappe.ui.form.on("Estimation Item", {
   
    item_group: function(frm, cdt, cdn) {
        
        console.log("item group")

        let row = locals[cdt][cdn];
        if (row.item_group) {
            updateDescription(frm, cdt, cdn, row.item_group);
        } else {
            
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Item Group',
                    filters: { name: row.item_group },
                    fieldname: 'description'
                },
                callback: function(response) {
                    if (response.message && response.message.description) {
                        frappe.model.set_value(cdt, cdn, 'item_group_description', response.message.description);
                        frm.refresh_field('estimation_items'); 
                    }
                },
                error: function(err) {
                    frappe.msgprint(__("Error fetching description. Please try again."));
                }
            });
            
        }
    },
  
    quantity(frm, cdt, cdn) {
      let row = frappe.get_doc(cdt, cdn);
      frappe.model.set_value(cdt, cdn, "rate", row.selling_sum / (row.quantity || 1));
      rateno = row.rateno
      let boq_rate = row.quantity ? Math.ceil(rateno/ 10) * 10 : 0;
      let boq_amount = row.quantity ? row.quantity * boq_rate:0;
      frappe.model.set_value(cdt, cdn, "boq_rate", boq_rate);
      frappe.model.set_value(cdt, cdn, "boq_amount", boq_amount);
      update_estimation_totals(frm)
    },
    width_meter(frm, cdt, cdn) {
      let row = frappe.get_doc(cdt, cdn);
      frappe.model.set_value(
        cdt,
        cdn,
        "area",
        row.width_meter * row.height_meter
      );
      frappe.model.set_value(
        cdt,
        cdn,
        "perimeter",
        2 * (row.width_meter + row.quantity)
      );
      frappe.model.set_value(cdt, cdn, "ratem2", row.selling_sum / (row.area || 1));
      update_estimation_totals(frm)
    },
    height_meter(frm, cdt, cdn) {
      let row = frappe.get_doc(cdt, cdn);
      frappe.model.set_value(
        cdt,
        cdn,
        "area",
        row.width_meter * row.height_meter
      );
      frappe.model.set_value(
        cdt,
        cdn,
        "perimeter",
        2 * (row.width_meter + row.quantity)
      );
      frappe.model.set_value(cdt, cdn, "ratem2", row.selling_sum / (row.area || 1));
      update_estimation_totals(frm)
    },
    click_btn: function (frm, cdt, cdn) {
        var row = locals[cdt][cdn];
    
        let data = {
            estimation_id: frm.doc.name,
            idx: row.idx,
            item: row.item,
            item_group: row.item_group,
        };
    
        // Fetch existing rows for the current item (both Material and Labour) in the child table
        let existing_items = frm.doc.estimation_item_material_and_labour.filter(function(item_row) {
            return item_row.item === row.item;
        });
    
        // Prepare data to populate the dialog's table if there are existing entries
        let pre_populated_data = existing_items.map(function(item_row) {
            return {
                type: item_row.type,
                item: item_row.sub_item,
                quantity: item_row.quantity,
                rate: item_row.rate,
                amount: item_row.amount
            };
        });
    
        // Fetch the Company settings
        frappe.db.get_value('Company', {name: frm.doc.company}, 'use_generic_items_for_material_and_labour')
        .then(r => {
            let use_generic_items = r.message.use_generic_items_for_material_and_labour;
    
            // Only proceed to fetch default items if the field is checked in Company document
            if (use_generic_items) {
                Promise.all([
                    frappe.db.get_list('Item', {
                        filters: {use_as_default_for_labour_in_estimate: 1},
                        fields: ['name']
                    }),
                    frappe.db.get_list('Item', {
                        filters: {use_as_default_for_material_in_estimate: 1},
                        fields: ['name']
                    })
                ]).then(([default_labour_items, default_material_items]) => {
                    if (pre_populated_data.length === 0) {
                        // Prepopulate labour and material defaults only if no data is filled by the user
                        default_labour_items.forEach(item => {
                            pre_populated_data.push({type: 'Labour', item: item.name, quantity:1});
                            
                        });
                        default_material_items.forEach(item => {
                            pre_populated_data.push({type: 'Material', item: item.name,quantity:1});
                        });
                    }
    
                    // Create the dialog window after checking for defaults
                    show_dialog(pre_populated_data);
                });
            } else {
                // If not using generic items, show the dialog without fetching defaults
                show_dialog(pre_populated_data);
            }
        });
    
        function show_dialog(pre_populated_data) {
            let dialog_window = new frappe.ui.Dialog({
                title: "Labour and Material Details",
                fields: [
                    {
                        fieldname: "item_group",
                        label: "Item Group",
                        fieldtype: "Link",
                        default: data.item_group,
                        read_only: 1,
                        column: 2,
                    },
                    {
                        fieldtype: "Column Break",
                    },
                    {
                        fieldname: "item",
                        label: "Item",
                        fieldtype: "Link",
                        default: data.item,
                        read_only: 1,
                        column: 2,
                    },
                    {
                        fieldtype: "Section Break",
                    },
                    {
                        label: "Items",
                        fieldname: "items",
                        fieldtype: "Table",
                        fields: [
                            {
                                fieldname: "type",
                                label: "Type",
                                fieldtype: "Select",
                                options: "\nMaterial\nLabour",
                                in_list_view: 1,
                                change: function () {
                                    const item_group = this.value;
                                    const item_field = dialog_window.fields_dict.items.grid.fields_map.item;
    
                                    // Set the query to filter items based on the selected item group
                                    item_field.get_query = function () {
                                        return {
                                            filters: {
                                                item_type: item_group,
                                            },
                                        };
                                    };
                                },
                            },
                            {
                                fieldname: "item",
                                label: "Item",
                                fieldtype: "Link",
                                options: "Item",
                                in_list_view: 1,
                            },
                            {
                                fieldname: "quantity",
                                label: "Quantity",
                                fieldtype: "Float",
                                in_list_view: 1,
                                change: function () {
                                    calculate_amount(dialog_window);
                                },
                            },
                            {
                                fieldname: "rate",
                                label: "Rate",
                                fieldtype: "Float",
                                in_list_view: 1,
                                change: function () {
                                    calculate_amount(dialog_window);
                                },
                            },
                            {
                                fieldname: "amount",
                                label: "Amount",
                                fieldtype: "Float",
                                in_list_view: 1,
                            },
                        ],
                        data: pre_populated_data,  // Pre-populate with existing values if any
                    },
                    {
                        fieldname: "idx",
                        label: "Idx",
                        fieldtype: "Data",
                        default: data.idx,
                        read_only: 1,
                        hidden: 1,
                    },
                ],
                primary_action_label: "Save",
                primary_action(values) {
                    if (!frm.doc.items) {
                        frm.doc.items = [];
                    }
                    values.items.forEach((item) => {
                        frm.doc.items.push(item);
                    });
    
                    // Remove existing rows with the same item
                    frm.doc.estimation_item_material_and_labour = frm.doc.estimation_item_material_and_labour.filter(row => row.item !== values.item);
    
                    values.items.forEach(element => {
                        var row_material_and_labour = frappe.model.get_new_doc("Estimation Item Material And Labour");
                        row_material_and_labour.item_group = values.item_group;
                        row_material_and_labour.item = values.item;
                        row_material_and_labour.sub_item = element.item;
                        row_material_and_labour.type = element.type;
                        row_material_and_labour.quantity = element.quantity;
                        row_material_and_labour.rate = element.rate;
                        row_material_and_labour.amount = element.amount;
                        frm.add_child('estimation_item_material_and_labour', row_material_and_labour);
                    });
    
                    frm.refresh_field('estimation_item_material_and_labour');
                    calculate_material_labour_table_amount(dialog_window, frm);
                    update_estimation_totals(frm);
                    dialog_window.hide();
                },
            });
    
            dialog_window.$wrapper.find(".modal-dialog").css("max-width", "90%");
            dialog_window.$wrapper.find(".modal-dialog").css("width", "90%");
            dialog_window.show();
    
            dialog_window.fields_dict.items.grid.wrapper.on("change", 'input[data-fieldname="quantity"], input[data-fieldname="rate"]', function () {
                calculate_material_labour_table_amount(dialog_window, frm);
            });
        }
    },
    
  });
  
  function calculate_material_labour_table_amount(dialog,frm) {
    let child_table_data = dialog.fields_dict.items.grid.get_data();
    child_table_data.forEach((row, idx) => {
      let quantity = row.quantity || 0;
      let rate = row.rate || 0;
      let amount = quantity * rate;
      dialog.fields_dict.items.grid.get_row(idx).doc.amount = amount;
    });
    
    dialog.fields_dict.items.grid.refresh(); // Refresh the table to show updated values
    
  }
  
  function calculate_amount(d) {
    
    let qty = d.get_value("quantity") || 0;
    let rate = d.get_value("rate") || 0;
    let amount = qty * rate;
  
    d.set_value("amount", amount);
    d.refresh_fields(["amount"]); // Refresh the field to show the updated value
  }
  
  function update_estimation_totals(frm) {
      // Initialize dictionaries to hold sum of amounts for each item and type
      console.log("from update_estimation_toals")
  
      let material_totals = {};
      let labour_totals = {};
  
      // Loop through the rows of the child table (estimation_item_material_and_labour)
      frm.doc.estimation_item_material_and_labour.forEach(row => {
          // Ensure item and amount are defined before proceeding
          if (row.item && row.amount !== undefined) {
              if (row.type === "Material") {
                  // Add the amount to the material totals
                  if (!material_totals[row.item]) {
                      material_totals[row.item] = 0;
                  }
                  material_totals[row.item] += row.amount;
              } else if (row.type === "Labour") {
                  // Add the amount to the labour totals
                  if (!labour_totals[row.item]) {
                      labour_totals[row.item] = 0;
                  }
                  labour_totals[row.item] += row.amount;
              }
          }
      });
  
      let total_material_cost = 0
      let total_labour_cost = 0
      let total_estimate = 0
      let total_profit = 0
      let total_overheads = 0
  
      // Now update the corresponding raw_cost and labour_cost in the main estimation table
      frm.doc.estimation_items.forEach(item_row => {
          // Check if item is defined in the main table and in the totals
          if (item_row.item) {
              if (material_totals[item_row.item] !== undefined) {
                  item_row.raw_cost = material_totals[item_row.item]; // Update raw_cost for Material
              } else {
                  item_row.raw_cost = 0; // Set to 0 if no materials found
              }
  
              total_material_cost += item_row.raw_cost
  
              if (labour_totals[item_row.item] !== undefined) {
                  item_row.labour_cost = labour_totals[item_row.item]; // Update labour_cost for Labour
              } else {
                  item_row.labour_cost = 0; // Set to 0 if no labour found
              }
  
              total_labour_cost += item_row.labour_cost
  
              item_row.fixed_amount = item_row.raw_cost + item_row.labour_cost
              
              item_row.overhead_amount = frm.doc.overhead_percentage>0? (item_row.fixed_amount * frm.doc.overhead_percentage) /100:0

              total_overheads += item_row.overhead_amount

              item_row.profit_amount =  frm.doc.profit_and_margin>0? ((item_row.fixed_amount + item_row.overhead_amount) * frm.doc.profit_and_margin) /100 : 0

              total_profit += item_row.profit_amount

              console.log("total profit")
              console.log(total_profit)
              console.log(total_overheads)
              

              item_row.selling_sum = item_row.fixed_amount + item_row.overhead_amount + item_row.profit_amount           
              item_row.rate = item_row.quantity>0 ? (item_row.selling_sum / item_row.quantity):0
              item_row.boq_rate = item_row.quantity>0? Math.ceil(item_row.rate/ 10) * 10 : 0;
              item_row.boq_amount = item_row.quantity * item_row.boq_rate
              total_estimate += item_row.boq_amount
  
              item_row.ratem2 = item_row.area>0 ? item_row.selling_sum / item_row.area : 0           
  
          }
  
          frm.doc.total_material_cost = total_material_cost
          frm.doc.total_labour_cost = total_labour_cost
          frm.doc.total_overheads = total_overheads
          total_cost = total_material_cost + total_labour_cost + total_overheads
          frm.doc.total_cost = total_cost
          frm.doc.total_profit = total_profit
          frm.doc.estimate_total =  total_estimate
          
      });
  
      frm.refresh_fields()
  }
  
  // fetched the description from item group. 
  
  
  
  
  frappe.ui.form.on("Estimate", {
    refresh: function(frm) {
        frm.fields_dict['estimation_items'].grid.get_field('item').get_query = function(doc, cdt, cdn) {
            var child = locals[cdt][cdn];
            return {
                filters: {
                    'item_group': child.group_item,
                    'item_type': 'BOQ Product'
                }
            };
        };
    }
  });
  
    
  function updateDescription(frm, cdt, cdn, groupItem) {
    
    console.log("from update description")
    console.log(groupItem)
    
    let icsqDescription = getDescriptionFromICSQ(frm, groupItem);
    console.log(icsqDescription)
    if (icsqDescription) {
        
        frappe.model.set_value(cdt, cdn, 'item_group_description', icsqDescription);
        frm.refresh_field('estimation_items');        
    } 
    else
    {
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Item Group',
                filters: { name: groupItem},
                fieldname: 'description'
            },
            callback: function(response) {
                console.log(response);
                if (response.message && response.message.description) {
                    frappe.model.set_value(cdt, cdn, 'item_group_description', response.message.description);
                    frm.refresh_field('estimation_items');
                }
            },
            error: function(err) {
                frappe.msgprint(__("Unable to fetch description. Please try again."));
            }
        });

        
    }
  }
  
  function getDescriptionFromICSQ(frm, groupItem) {

    console.log("getDescriptionFromICSQ")
    console.log(groupItem)
    let item_groups = frm.doc.item_groups || [];
    for (let row of item_groups) {
        if (row.item_group_name === groupItem && row.description) {
            return row.description;
        }
    }
    return null;
  }

  function update_descriptions_in_items(frm,item_group,description)
  {
    console.log("from update_item_descriptions")

    console.log("item_group")
    console.log(item_group)
    
    let item_table = frm.doc.estimation_items
    for (let row of item_table) {
        if (row.item_group === item_group) {
            console.log("found")
            row.item_group_description = description
        }
    }

    frm.refresh_field("estimation_items")
  }
    
  // Created a dialog box upon clicking show_details button that has all the fields of item estimation table
  frappe.ui.form.on('Estimate', {
    refresh: function(frm) {
        // Remove any existing click handlers
        frm.fields_dict.show_details.$input.off('click');
        
        // Add a single click handler
        frm.fields_dict.show_details.$input.on('click', function() {
            showDetailsTable(frm);
        });
    }
  });
  
  let detailsDialog = null; // Global variable to hold the dialog instance
  
  function showDetailsTable(frm) {
    // If a dialog is already open, close it
    if (detailsDialog) {
        detailsDialog.hide();
        detailsDialog = null;
    }
  
    let groupedItems = {};
    frm.doc.estimation_items.forEach(row => {
  
      if (row.quantity && row.item) {
        const key = `${row.item_group || 'Others'}_${row.item}_${row.width_meter}_${row.height_meter}`;
        if (!groupedItems[key]) {
            groupedItems[key] = { ...row, total_quantity: 0 };
        }
        groupedItems[key].total_quantity += row.quantity || 0;
      }
    });
  
    const sortedKeys = Object.keys(groupedItems).sort((a, b) => {
        const groupA = groupedItems[a].item_group || 'Others';
        const groupB = groupedItems[b].item_group || 'Others';
        return groupA.localeCompare(groupB);
    });
  
    let tableHtml = `
    <div style="overflow-x: auto;">
    <table class="table table-bordered" style="width: 100%;">
    <thead>
    <tr>
        <th>Group Item</th>
        <th>Group Description</th>
        <th>Item</th>
        <th>Description</th>     
        <th style="text-align: right;">Width</th>
        <th style="text-align: right;">Height</th>
        <th style="text-align: right;">Quantity</th>
        <th style="text-align: right;">Area</th>
        <th style="text-align: right;">Perimeter</th>
        <th style="text-align: right;">Raw Cost</th>
        <th style="text-align: right;">Labour Cost</th>
        <th style="text-align: right;">Fixed Amount</th>
        <th style="text-align: right;">Selling Sum</th>
        <th style="text-align: right;">Rate/No</th>
        <th style="text-align: right;">Rate/M²</th>     
        <th style="text-align: right;">Overhead Amount</th>
        <th style="text-align: right;">Profit Amount</th>
        <th style="text-align: right;">BOQ Rate</th>
        <th style="text-align: right;">BOQ Amount</th>
    </tr>
    </thead>
    <tbody>
    `;
  
    let currentGroup = '';
    sortedKeys.forEach(key => {
        const row = groupedItems[key];
        if (row.item_group !== currentGroup) {
            currentGroup = row.item_group || 'Others';
            tableHtml += `
            <tr class="group-header">
                <td colspan="17"><strong>${currentGroup}</strong></td>
            </tr>
            `;
        }
        tableHtml += `
        <tr>
            <td>${row.item_group || 'Others'}</td>
            <td>${row.item_group_description || ''}</td>
            <td>${row.item || ''}</td>
            <td>${row.description || ''}</td>
            <td>${row.width_meter || ''}</td>
            <td>${row.height_meter || ''}</td>
            <td>${row.total_quantity || ''}</td>
            <td>${row.area || ''}</td>
            <td>${row.perimeter || ''}</td>
            <td>${(row.raw_cost !== undefined ? row.raw_cost.toFixed(2) : '0.00')}</td>
            <td>${(row.labour_cost !== undefined ? row.labour_cost.toFixed(2) : '0.00')}</td>
            <td>${(row.fixed_amount !== undefined ? row.fixed_amount.toFixed(2) : '0.00')}</td>
            <td>${(row.selling_sum !== undefined ? row.selling_sum.toFixed(2) : '0.00')}</td>
            <td>${(row.rate !== undefined ? row.rate.toFixed(2) : '0.00')}</td>
            <td>${(row.ratem2 !== undefined ? row.ratem2.toFixed(2) : '0.00')}</td>
            <td>${(row.overhead_amount !== undefined ? row.overhead_amount.toFixed(2) : '0.00')}</td>
            <td>${(row.profit_amount !== undefined ? row.profit_amount.toFixed(2) : '0.00')}</td>
            <td>${(row.boq_rate !== undefined ? row.boq_rate.toFixed(2) : '0.00')}</td>
            <td>${(row.boq_amount !== undefined ? row.boq_amount.toFixed(2) : '0.00')}</td>          
        </tr>
        `;
    });
  
    tableHtml += `
    </tbody>
    </table>
    </div>
    `;
  
    detailsDialog = new frappe.ui.Dialog({
        title: 'Estimation Details',
        fields: [{
            fieldtype: 'HTML',
            fieldname: 'details_table',
            options: tableHtml
        }]
    });
  
    detailsDialog.show();
  
    detailsDialog.$wrapper.find('.modal-dialog').css({
        'width': '95%',
        'max-width': '95%',
        'margin': '30px auto'
    });
    detailsDialog.$wrapper.find('.modal-content').css({
        'height': 'auto',
        'max-height': '90vh'
    });
    detailsDialog.$wrapper.find('.modal-body').css({
        'max-height': 'calc(90vh - 120px)',
        'overflow-y': 'auto',
        'overflow-x': 'auto',
        'white-space': 'nowrap'
    });
    detailsDialog.$wrapper.find('.group-header').css('background-color', '#f0f0f0');
  
    detailsDialog.set_primary_action(__('Close'), function() {
        detailsDialog.hide();
        detailsDialog = null;
    });
  }