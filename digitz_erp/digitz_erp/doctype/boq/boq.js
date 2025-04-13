frappe.ui.form.on("BOQ", {
    show_a_message: function (frm,message) {
          frappe.call({
              method: 'digitz_erp.api.settings_api.show_a_message',
              args: {
                  msg: message
              }
          });
      },
    refresh: function (frm) {
      if (!frm.is_new() && frm.doc.docstatus === 1) {
  
        frappe.call({
          method: "digitz_services.api.boq_apis.check_estimate_for_boq",  // API to check if Estimate exists
          async: false,
          args: {
              boq_id: frm.doc.name,  // Current BOQ name
          },
          callback: function (r) {
              let estimate_exists = r.message;  // This tells if an Estimate exists for the BOQ
      
              if (!estimate_exists) {
                  // If no Estimate exists, show "Create Estimate" button
                  frm.add_custom_button(__("Create Estimate"), function () {
                      frappe.call({
                          method: "digitz_services.api.boq_apis.create_estimate_from_boq",  // API to create Estimate
                          args: {
                              boq_name: frm.doc.name,  // Pass BOQ ID
                          },
                          callback: function(r) {
                              if (r.message) {
                                  // Sync and load the newly created Estimate in the UI
                                  frappe.model.sync([r.message]);
                                  frappe.set_route("Form", "Estimate", r.message.name);
                              }
                          },
                      });
                  },"Actions");
  
                  frm.events.show_a_message(frm,"No estimate is linked to this BOQ. Please create an estimate to continue.");
                  
              } else {
  
                // When estimate exists, we can create a quotation, if it is not exists
                  frappe.call({
                    method: "digitz_services.api.boq_apis.check_quotation_for_boq",
                    async: false,
                    args: {
                      boq_id: frm.doc.name,
                    },
                    callback: function (r) {
                      let create_qot = !r.message;
  
                      if (create_qot) {
                        frm.add_custom_button(__("Create Quotation"), function () {
                          frappe.call({
                            method: "digitz_services.api.boq_apis.create_quotation",
                            args: {
                              boq_id: frm.doc.name,
                            },
                            callback: function(r) {
                              if (r.message) {
                                  // Sync the returned project document to load it in the UI
                                  frappe.model.sync([r.message]);
                                  console.log("r.message")
                                  console.log(r.message)
                                  
                                  // Set the route to the newly created Project
                                  frappe.set_route("Form", "Quotation", r.message.name);
                              }
                          },
                          });
                        }, "Actions");
  
                        // Option to create customer from prospect if it is not exists
                        // This option also needs to be showed only when there is no quotation exists
                        //In 'Create Quotation' option above, it shows the error to convert the prospect
                        //to customer. So user can just convert the prospect to customer with the below
                        //button and then create quotation.
                        if (frm.doc.lead_type === "Prospect") {
                          frappe.call({
                            method: "frappe.client.get_list",
                            args: {
                              doctype: "Customer",
                              filters: { prospect: frm.doc.prospect },
                              fields: ["name"],
                            },
                            callback: function (r) {
                              if (r.message.length === 0) {
                                frm.add_custom_button(__("Convert Prospect to Customer"), function () {
                                  frappe.call({
                                    method: "digitz_erp.api.customer_api.convert_prospect_to_customer",
                                    args: {
                                      prospect: frm.doc.name,
                                    },
                                    callback: function (r) {
                                      if (r.message) {
                                        let doc = frappe.model.sync(r.message)[0];
                                        frappe.set_route("Form", "Customer", doc.name);
                                      }
                                    },
                                  });
                                },"Actions");
                              }
                            },
                          });
                        }
                      }
                    },
                  });
  
  
              
  
                  frappe.call({
                    method: "digitz_services.api.boq_apis.check_sales_order_for_boq",
                    async: false,
                    args: {
                      boq_id: frm.doc.name,
                    },
                    callback: function (r) {
                      let allow_amend = r.message;
                      if(allow_amend)
                      {
                        frm.add_custom_button(__("Addition"), function () {
                          frappe.new_doc("BOQ Amendment", {}, (boq_amendment) => {
                            boq_amendment.boq = frm.doc.name;
                            boq_amendment.rate_includes_tax = frm.doc.rate_includes_tax
                            boq_amendment.option = "Addition";
                          });
                        }, __("BOQ Amendment"));
                  
                        frm.add_custom_button(__("Deduction"), function () {
                          frappe.new_doc("BOQ Amendment", {}, (boq_amendment) => {
                            boq_amendment.boq= frm.doc.name;
                            boq_amendment.option = "Deduction";
                  
                            frm.doc.boq_items.forEach((boq_item) => {
                              let new_row = frappe.model.add_child(boq_amendment, "boq_items");
                              Object.assign(new_row, {
                                item: boq_item.item,
                                item_name: boq_item.item_name,
                                description: boq_item.description,
                                quantity: boq_item.quantity,
                                rate: boq_item.rate,
                                amount: boq_item.amount,
                                unit: boq_item.unit,
                                net_amount: boq_item.net_amount,
                                gross_amount:boq_item.gross_amount
                              });
                            });
                            
                          });
                        }, __("BOQ Amendment"));
  
  
                        // Same condition to add BOQ Execution
  
                        // Add BOQ Execution button. Adding button only when estimate exists.
                        frappe.call({
                          method: "digitz_services.api.boq_apis.check_boq_execution_for_boq",
                          async: false,
                          args: {
                            boq_id: frm.doc.name,
                          },
                          callback: function (r) {
                            let create_boq_e = !r.message;
  
                            if (create_boq_e) {
                              frm.add_custom_button(__("Create BOQ Execution"), function () {
                                frappe.call({
                                  method: "digitz_services.api.boq_apis.create_boq_execution_for_boq",
                                  args: {
                                    boq_id: frm.doc.name,
                                  },
                                  callback: function(r) {
                                    if (r.message) {
                                        // Sync the returned project document to load it in the UI
                                        frappe.model.sync([r.message]);
                                        console.log("r.message")
                                        console.log(r.message)
                                        
                                        // Set the route to the newly created Project
                                        frappe.set_route("Form", "BOQ Execution", r.message.name);
                                    }
                                },
                                });
                              }, "Actions");
                            }}});
  
  
                      }
  
                    }});
  
                 
  
                }
              }});
  
  
       
      }
  
      if (frm.is_new()) {
        frm.trigger("make_taxes_and_totals");
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
          default_company = r.message.default_company
        },
      });
  
      frappe.call({
        method: "frappe.client.get_value",
        args: {
          doctype: "Company",
          filters: { company_name: frm.doc.default_company },
          fieldname: ["default_warehouse", "rate_includes_tax", "use_custom_item_group_description_in_estimation"],
        },
        callback: (r) => {
          frm.doc.rate_includes_tax = r.message.rate_includes_tax;
          frm.set_value("use_custom_item_group_description", r.message.use_custom_item_group_description_in_estimation);
        },
      });
    },
  
    assign_defaults: function (frm) {
      if (frm.is_new()) {
        frm.trigger("get_default_company_and_warehouse");
      }
    },
  
    edit_posting_date_and_time: function (frm) {
      const readOnly = frm.doc.edit_posting_date_and_time ? 0 : 1;
      frm.set_df_property("posting_date", "read_only", readOnly);
      frm.set_df_property("posting_time", "read_only", readOnly);
    },
  });
  
  frappe.ui.form.on("BOQ", "onload", function (frm) {
    frm.trigger("assign_defaults");
  });
  
  frappe.ui.form.on("BOQ Item", {
  
    item_group: function (frm, cdt, cdn) {
  
      let row = locals[cdt][cdn];
  
      if (row.item_group) {
  
        console.log("item_group2",row.item_group)
  
        
        let description= get_description_from_groups_table(frm, row.item_group);
  
        console.log("description",description)
  
        if (description!="")
        {
          row.item_group_description = description
        } //Else default description is already there
  
  
      }
    },
  
    item: function (frm, cdt, cdn) {
  
      
  
      console.log("item call")
  
      let row = locals[cdt][cdn];    
      let tax_excluded_for_company = false;
  
      frappe.call({
        method: "digitz_erp.api.settings_api.get_company_settings",
        async: false,
        callback: (r) => {
          tax_excluded_for_company = r.message[0].tax_excluded;
        },
      });
  
      frappe.call({
        method: "frappe.client.get_value",
        args: {
          doctype: "Item",
          filters: { item_code: row.item },
          fieldname: ["item_name", "description","base_unit", "tax", "tax_excluded"],
        },
        callback: (r) => {
  
          console.log("from get_value for item")
  
          Object.assign(row, {
            item_name: r.message.item_name,          
            description:  r.message.description?r.message.description: r.message.item_name,
            base_unit: r.message.base_unit,
            unit: r.message.base_unit,
            conversion_factor: 1,
            tax_excluded: tax_excluded_for_company ? true : r.message.tax_excluded,
          });
  
          console.log("r.message",r.message)
  
          if (!row.tax_excluded) {
            frappe.call({
              method: "frappe.client.get_value",
              args: {
                doctype: "Tax",
                filters: { tax_name: r.message.tax },
                fieldname: ["tax_name", "tax_rate"],
       
        
              },
              callback: (r2) => {
                row.tax = r2.message.tax_name;
                row.tax_rate = r2.message.tax_rate;
              },
            });
          } else {
            row.tax = "";
            row.tax_rate = 0;
          }
  
          row.rate_includes_tax = frm.doc.rate_includes_tax
          
          let description = get_description_from_groups_table(frm, row.item_group);
          console.log("description", description)
          if(description!="")
          {
            row.item_group_description = description
          } //else default description is already there
          
          frm.refresh_field("boq_items");
  
          let current_row = locals[cdt][cdn];
          let duplicate = frm.doc.boq_items.some(row => row.item === current_row.item && row.name !== current_row.name);
  
          if (duplicate) {
              frappe.msgprint(__('Item already exists in the table.'));
              frappe.model.set_value(cdt, cdn, 'item', null); // Reset the item field
          }
        },
      });
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
    boq_items_add(frm, cdt, cdn) {
      make_taxes_and_totals(frm);
    }
  });
  
  function make_taxes_and_totals(frm) {
    console.log("from make_taxes_and_totals");
    let total_amount = 0;
  
    frm.doc.boq_items.forEach((entry) => {
  
      if(entry.item != undefined)
        {
        
    
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
      }
    });
  
    frm.set_value("total_boq_amount", total_amount);
    frm.refresh_field("boq_items");
    console.log("Total BOQ Amount:", total_amount);
  }
  
  
  frappe.ui.form.on("Estimation Item Group", {
  
    item_group_name:function(frm,cdt,cdn)
    {
      console.log("item_group_name")
  
      let row = locals[cdt][cdn];
  
      item_group_name = row.item_group_name
  
      if(item_group_name != undefined)
        {
  
          console.log("here")
  
          frappe.call({
            method: "frappe.client.get_value",
            args: {
              doctype: "Item Group",
              filters: { item_group_name: item_group_name },
              fieldname: "description",
            },
            async: false, // Synchronous call to make sure description is fetched before proceeding
            callback: function (r) {
              if (r.message) {
  
                console.log(r)
  
                description = r.message.description;
                row.description = description
                frm.refresh_field("item_groups")
  
              } else {
                console.warn(`No description found for item group: ${item_group}`);
              }
            },
          });
        }
    },
    description: function (frm, cdt, cdn) {
      let row = locals[cdt][cdn];
      update_descriptions_in_items(frm, row.item_group_name,row.description);
    },
  });
  
  function update_descriptions_in_items(frm, item_group,description) {
    let item_table = frm.doc.boq_items;
    for (let row of item_table) {
      if (row.item_group === item_group) {
        row.item_group_description = description
      }
    }
    frm.refresh_field("boq_items");
  }
  
  function get_description_from_groups_table(frm, item_group) {
  
    console.log("from get_description_from_groups_table",item_group)
  
    let description = "";
    if (frm.doc.item_groups && frm.doc.item_groups.length > 0) {
      frm.doc.item_groups.forEach((row) => {
        if (row.item_group_name === item_group) {
          description = row.description;
          console.log("description for assignment", row.description)
        }
      });
    } else {
      // console.error("No item_groups data available in the form");
    }
  
    if (description == "") {
      frappe.call({
        method: "frappe.client.get_value",
        args: {
          doctype: "Item Group",
          filters: { item_group_name: item_group },
          fieldname: "description",
        },
        async: false, // Synchronous call to make sure description is fetched before proceeding
        callback: function (r) {
          if (r.message) {
            description = r.message.description;
          } else {
            console.warn(`No description found for item group: ${item_group}`);
          }
        },
      });
    }
    return description;
  }
  