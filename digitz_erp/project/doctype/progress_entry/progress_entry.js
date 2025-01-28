// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Progress Entry", {

  validate(frm) {
    if (frm.doc.previous_progress_entry === frm.doc.name) {
      frappe.throw("Choose a valid Progress Entry!");
    }
  },
  refresh(frm) {
    if (frm.is_new()) {
      get_default_company_and_warehouse(frm)
    }
    else
    {
      update_total_big_display(frm)
    }

    frm.set_query('previous_progress_entry', function () {
      return {
        filters: {
          name: ['!=', frm.doc.name],
          project: frm.doc.project          
        }
      };
    });

    frappe.call({
      method: 'digitz_erp.api.project_api.check_proforma_invoice',
      args: { progress_entry: frm.doc.name },
      callback(response) {
        if (!response.message) {
          frm.add_custom_button(__('Create Proforma Invoice'), function () {
            frappe.model.with_doctype('Proforma Invoice', function () {
              let doc = frappe.model.get_new_doc('Proforma Invoice');
              doc.progress_entry = frm.doc.name;
              doc.customer = frm.doc.customer;
              doc.company = frm.doc.company;
              frappe.set_route('Form', 'Proforma Invoice', doc.name);
            });
          },"Actions");
        }
      }
    });

    frappe.call({
      method: 'digitz_erp.api.project_api.check_progressive_invoice',
      args: { progress_entry: frm.doc.name },
      callback(response) {
        if (!response.message) {
          frm.add_custom_button(__('Create Progressive Invoice'), function () {
            frappe.model.with_doctype('Progressive Sales Invoice', function () {
              let doc = frappe.model.get_new_doc('Progressive Sales Invoice');
              doc.progress_entry = frm.doc.name;
              doc.customer = frm.doc.customer;
              doc.company = frm.doc.company;
              frappe.set_route('Form', 'Progressive Sales Invoice', doc.name);
            });
          },"Actions");
        }
      }
    });

    
  },
  onload_post_render: function(frm) {
    // Ensure styling is applied when the form is loaded
    highlight_amended_rows(frm);
  }, 
  project(frm) {

    frm.set_value('progress_entry_items', []);

    if (frm.doc.project) {

        // Steps
        // 1. Set sales order when project selected
        // 2. Check for previous progress entry already exists
        // 3. If No
        //       And if BOQ exists , load the items from boq Else load from Sales Order
        //    If Yes
        //       Fetch BOQ items and update progress from the previous PE

        // Set Sales Order
        if(frm.doc.sales_order == undefined)
        {

          frappe.call({
            method: 'digitz_erp.api.project_api.get_sales_order_for_project',
            args: { project_name: frm.doc.project }, 
            async:false,
            callback: function(response) {
              if (response.message.status === "success") {
                  frm.set_value('sales_order', response.message.sales_order);
              }}});
        }

        // Get Last Progress Entry
        frappe.call({
            method: 'digitz_erp.api.project_api.get_last_progress_entry',
            args: { project_name: frm.doc.project },   
            async:false,         
            callback: function(r) {
                if (r.message) {
                  frm.set_value('previous_progress_entry', r.message);
                  frm.set_value('is_prev_progress_exists', 1);
                 
                }
            }
        });

        if (frm.doc.is_prev_progress_exists === 0) {
            frm.set_value("total_completion_percentage", 0);
     
            if (frm.doc.sales_order) {

                // Fetch sales order and check if BOQ exists
                frappe.call({
                    method: "frappe.client.get",
                    args: {
                        doctype: "Sales Order",
                        name: frm.doc.sales_order
                    },
                    callback(r) {
                        if (r.message) {
                            // Check if there is a BOQ linked in the Sales Order
                            if (r.message.boq) {
                                fetch_boq_items(frm, r.message.boq);
                                update_boq_deleted_items(frm,r.message.boq)
                            } else {
                                // If no BOQ exists, fall back to Sales Order items
                                fetch_sales_order_items(frm);
                            }
                            highlight_amended_rows(frm);
                        } else {
                            frappe.msgprint(__("No items found for the selected Sales Order."));
                        }
                    }
                });
            } else {

              frappe.throw("Sales Order not found!!!")
                
            }
        } else {
            frm.set_value("total_completion_percentage", 0);
            frm.set_value("gross_total", "");
            frm.set_value("tax_total", "");
            frm.set_value("net_total", "");
            // frm.set_value("total_discount_in_line_items", "");
            frm.set_value("additional_discount", "");
            frm.set_value("round_off", "");
            frm.set_value("rounded_total", "");
            frm.set_value("in_words", "");
            frm.refresh_field("progress_entry_items");

            if (frm.doc.previous_progress_entry && frm.doc.previous_progress_entry !== frm.doc.name) {
                frappe.call({
                    method: "frappe.client.get",
                    args: {
                        doctype: "Progress Entry",
                        name: frm.doc.previous_progress_entry
                    },
                    callback(r) {
                        if (r.message && r.message.progress_entry_items) {
                            // Check if the total completion percentage is below 100
                            if (r.message.total_completion_percentage < 100) {

                                if(frm.doc.boq)
                                {
                                  // Fetch the latest BOQ items (may be amended) and then update the previous progress for each line item.
                                  fetch_boq_items(frm,frm.doc.boq)                                  
                                  update_from_previous_progress_entry_for_boq(frm,r)
                                  update_boq_deleted_items(frm,r.message.boq)
                                }
                                else //If there is no BOQ exists and progress entry is creating with out BOQ
                                {
                                  update_from_previous_progress_entry(frm, r);
                                }

                                highlight_amended_rows(frm);
                               
                            } else {
                                frappe.msgprint(__("The previous progress entry is already 100% completed."));
                            }
                        } else {
                            frappe.msgprint(__("No Items Are In Previous Progress Entry, " + frm.doc.previous_progress_entry + "."));
                        }
                    }
                });
            }
        }

        update_total_big_display(frm);
    }
},

  // is_prev_progress_exists(frm) {
  //   if (frm.doc.is_prev_progress_exists === 0) {
  //     frm.set_value("previous_progress_entry", "");
  //   }
  //   frm.trigger('project');
  // },

  // previous_progress_entry(frm) {
  //   // frm.trigger('project');
  // }
});

function fetch_sales_order_items(frm) {
  frappe.call({
    method: "frappe.client.get",
    args: {
      doctype: "Sales Order",
      name: frm.doc.sales_order
    },
    callback(r) {
      if (r.message && r.message.items) {
        frm.clear_table("progress_entry_items");
        r.message.items.forEach(function (item) {
          let row = frm.add_child("progress_entry_items");
          row.sales_order_amt = r.message.net_total;
          row.item = item.item;
          row.item_name = item.item_name;
          //Just copying the tax related configurations from the sales order, for reference
          row.rate_includes_tax = item.rate_includes_tax
          row.tax_excluded = item.tax_excluded
          row.tax = item.tax
          row.tax_rate = item.tax_rate       

          row.item_tax_amount = item.tax_amount;
          row.item_gross_amount = item.gross_amount;
          row.item_net_amount = item.net_amount         
          
        });

        frm.refresh_field("progress_entry_items");

      } else {

        frappe.msgprint(__("No items found for the selected Sales Order."));
      }
    }
  });
}

function check_boq_amendments_after_progress(frm, boq_name) {
  frappe.call({
      method: "frappe.client.get_list",
      args: {
          doctype: "BOQ Amendment",
          filters: {
              boq: boq_name,
              posting_date: [">", frm.doc.last_progress_entry_date]  // Assuming `last_progress_entry_date` is available
          },
          order_by: "posting_date asc",
          limit_page_length: 1
      },
      callback(r) {
          if (r.message && r.message.length > 0) {
              // Fetch items from the latest BOQ Amendment after the last progress entry
              fetch_boq_amendment_items(frm, r.message[0].name);
          } else {
              // No relevant BOQ Amendment found; continue with previous Progress Entry data
              frappe.msgprint(__("No BOQ Amendments found after the last Progress Entry."));
          }
      }
  });
}

function fetch_boq_amendment_items(frm, amendment_name) {
  frappe.call({
      method: "frappe.client.get",
      args: {
          doctype: "BOQ Amendment",
          name: amendment_name
      },
      callback(r) {
          if (r.message && r.message.items) {
              frm.clear_table("progress_entry_items");
              r.message.items.forEach(function (item) {
                  let row = frm.add_child("progress_entry_items");
                  row.item = item.item;
                  row.item_name = item.item_name;
                  row.quantity = item.quantity;
                  row.rate = item.rate;
                  row.amount = item.amount;
                  row.tax_rate = item.tax_rate;
                  row.tax_amount = item.tax_amount;
                  row.gross_amount = item.gross_amount;
                  row.net_amount = item.net_amount;
              });
              frm.refresh_field("progress_entry_items");
          } else {
              frappe.msgprint(__("No items found in the linked BOQ Amendment."));
          }
      }
  });
}

function fetch_boq_items(frm, boq_name) {

  frappe.call({
      method: "frappe.client.get",
      args: {
          doctype: "BOQ",
          name: boq_name
      },
      async:false,
      callback(r) {
          if (r.message && r.message.boq_items) {

              frm.clear_table("progress_entry_items");
              let gross_before_addition = 0
              let gross_for_addition = 0
              r.message.boq_items.forEach(function (item) {
                  let row = frm.add_child("progress_entry_items");
                  row.item = item.item;
                  row.item_name = item.item_name;
                  row.quantity = item.quantity;
                  row.rate = item.rate;
                  row.amount = item.amount;
                  row.tax_rate = item.tax_rate;
                  row.item_tax_amount = item.tax_amount;
                  row.item_gross_amount = item.gross_amount;
                  row.item_net_amount = item.net_amount;                 

                  if(item.addition)
                  {
                    row.amendment_mode = "Addition"
                    gross_for_addition += item.gross_amount
                  }
                  else
                  {
                    gross_before_addition += item.gross_amount
                  }

                    
              });

              frm.set_value('gross_total_before_addition', gross_before_addition)
              frm.set_value('gross_for_addition', gross_for_addition)

              frm.refresh_field("progress_entry_items");
          } else {
              frappe.msgprint(__("No items found in the linked BOQ."));
          }
      }
  });
}

function update_boq_deleted_items(frm, boq_name) {

  frappe.call({
      method: "frappe.client.get",
      args: {
          doctype: "BOQ",
          name: boq_name
      },
      async:false,
      callback(r) {

          console.log(r.message.items_deleted)

          if (r.message && r.message.items_deleted) {
            
              
              let gross_total_for_removed = 0
              let net_total_for_removed = 0

              r.message.items_deleted.forEach(function (item) {
                
                gross_total_for_removed += item.gross_amount;
                net_total_for_removed += item.net_amount
                    
              });

              frm.set_value("gross_total_for_removed_items", gross_total_for_removed)
              frm.set_value("net_total_for_removed_items", net_total_for_removed)


              frm.refresh_field("progress_entry_items");
          } else {
              frappe.msgprint(__("No items found in the linked BOQ."));
          }
      }
  });
}


function update_from_previous_progress_entry_for_boq(frm, r) {

  // Ensure progress entry and its items exist
  if (!r.message || !r.message.progress_entry_items) {
    frappe.msgprint(__("No valid data found for the previous progress entry."));
    return;
  }
  
  // Set previous completion percentage from the previous progress entry
  frm.set_value("previous_completion_percentage", r.message.total_completion_percentage);

  // Loop through each row in the current child table.
  // This loop also identifies any 'Addition' happened after the previous progress entry
  frm.doc.progress_entry_items.forEach(function (row) {
    // Find matching item in progress_entry_items from the previous progress entry
    const matching_item = r.message.progress_entry_items.find(item => item.item === row.item);

    if (matching_item) {
      // Update values if a match is found
      row.sales_order_amt = frm.doc.sales_order_net_total;
      row.prev_completion = matching_item.total_completion || 0;
      row.total_completion = matching_item.total_completion || 0;
      row.total_amount = matching_item.total_amount || 0;
      row.prev_amount = matching_item.total_amount || 0;
      row.item_name = matching_item.item_name;
      
      // Copy tax configurations from the previous progress entry
      row.rate_includes_tax = matching_item.rate_includes_tax;
      row.tax_excluded = matching_item.tax_excluded;
      row.tax = matching_item.tax;
      row.tax_rate = matching_item.tax_rate;
      row.item_net_amount = matching_item.item_net_amount;
      row.item_gross_amount = matching_item.item_gross_amount;
      row.item_tax_amount = matching_item.item_tax_amount;
    }      
  });

  // Check each previous progress entry items is still in the BOQ items which is loaded already.
  // If Not mark it's 'Amendment Mode' as 'Deletion'
  // This scenario is not likely to occur since we dont allow to delete the item in the 'BOQ Amendment'
  // if its already using in the progress entry
  r.message.progress_entry_items.forEach(function (item) {
    const existing_row = frm.doc.progress_entry_items.find(row => row.item === item.item);

    // This condition is not likely to occur since in the current implementation, we dont allow
    // to delete item when there is a progress entry already exists with the item
    if (existing_row == undefined) {

      // Add a new row for unmatched items
      const new_row = frm.add_child("progress_entry_items");
      new_row.sales_order_amt = frm.doc.sales_order_net_total;
      new_row.prev_completion = item.total_completion || 0;

      new_row.total_completion = 100 || 0;

      new_row.total_amount = item.total_amount || 0;
      new_row.prev_amount = item.total_amount || 0;
      new_row.item = item.item;
      new_row.item_name = item.item_name;

      // Copy tax configurations from the previous progress entry
      new_row.rate_includes_tax = item.rate_includes_tax;
      new_row.tax_excluded = item.tax_excluded;
      new_row.tax = item.tax;
      new_row.tax_rate = item.tax_rate;

      //Change the item net_amount to previous entry's net_amount likewie, gross_amount and tax_amount
      new_row.item_net_amount = item.net_amount;
      new_row.item_gross_amount = item.gross_amount;
      new_row.item_tax_amount = item.tax_amount;

      // Set Amendment Mode to "Deletion" for new rows
      new_row.amendment_mode = "Deletion";

       // Make `total_completion` read-only for "Deletion" rows
       frappe.run_serially([
        () => {
          frm.fields_dict["progress_entry_items"].grid.grid_rows_by_docname[new_row.name].toggle_editable("total_completion", false);
        }
      ]);
    }
  });

  // Reset totals
  frm.set_value('gross_total', 0);
  frm.set_value('tax_total', 0);
  frm.set_value('net_total', 0);
  frm.set_value('rounded_total', 0);

  // Refresh the field after setting new rows
  frm.refresh_field("progress_entry_items");

  // Alert if total completion percentage is already 100%
  if (frm.doc.total_completion_percentage === 100) {
    frappe.msgprint(__("The Completion Percentage is already 100%."));
  }

  highlight_amended_rows(frm);
}

function update_from_previous_progress_entry(frm, r) {

  // Ensure progress entry and its items exist
  if (!r.message || !r.message || !r.message.progress_entry_items) {
    frappe.msgprint(__("No valid data found for the previous progress entry."));
    return;
  }
  
  // Set previous completion percentage from the previous progress entry
  frm.set_value("previous_completion_percentage", r.message.total_completion_percentage);

  // Loop through each progress entry item and copy data to the current form
  r.message.progress_entry_items.forEach(function (item) {

    if (item.total_completion !== 100) {
      let row = frm.add_child("progress_entry_items");      
      row.sales_order_amt = frm.doc.sales_order_net_total;
      row.prev_completion = item.total_completion || 0;
      row.total_completion = item.total_completion || 0; //Default to previous completion
      row.total_amount = item.total_amount || 0;
      row.prev_amount = item.total_amount || 0;
      row.item = item.item;
      row.item_name = item.item_name;
      
      // Copy tax configurations from the previous progress entry
      row.rate_includes_tax = item.rate_includes_tax;
      row.tax_excluded = item.tax_excluded;
      row.tax = item.tax;
      row.tax_rate = item.tax_rate;
      row.item_net_amount = item.item_net_amount;
      row.item_gross_amount = item.item_gross_amount;
      row.item_tax_amount = item.item_tax_amount;
    }
  });

  frm.set_value('gross_total',0)
  frm.set_value('tax_total',0)
  frm.set_value('net_total',0)
  frm.set_value('rounded_total',0)

  // Refresh the field after setting new rows
  frm.refresh_field("progress_entry_items");

  // Set total completion percentage and alert if it's already 100%
  // frm.set_value("total_completion_percentage", r.message.total_completion_percentage);
  
  if (frm.doc.total_completion_percentage === 100) {
    frappe.msgprint(__("The Completion Percentage is already 100%."));
  }
}


frappe.ui.form.on("Progress Entry Item", {
 
  total_completion(frm,cdt,cdn){

    console.log("total_completion")

    let row = frappe.get_doc(cdt, cdn);
    
    if (row.amendment_mode == "Deletion")
    {
      frappe.msgprint({
        title: __("Validation Error"),
        indicator: "red",
        message: __("Deleted row % can't be edited."),
      });

      row.total_completion = 100;
      return;
    }
    
    if(row.total_completion< row.prev_completion)
    {
      frappe.msgprint({
        title: __("Validation Error"),
        indicator: "red",
        message: __("Completion % can't be less than previous completion %."),
      });

      row.total_completion = 0
      
      frm.refresh_field("progress_entry_items")

    }
    else if (row.total_completion > 100) {
      row.total_completion = 0;
      frappe.msgprint({
        title: __("Validation Error"),
        indicator: "red",
        message: __("Completion % can't be more than 100%"),
      });
    } else {      

        if (row.amendment_mode == "Deletion")
        {
          row.current_completion = 0
          // If the total_completion is edited by the user, put it back to 100
          row.total_completion = 100 
        }
        else
        {
          row.current_completion = (row.total_completion - row.prev_completion);   
        }

        update_total_progress(frm)
        console.log("eof update_total_progress")

        make_taxes_and_totals(frm,cdt,cdn);      
    }
  },
});

function update_total_progress(frm) {

  console.log("from update_total_progress")

  let total_weighted_completion = 0;
  let total_item_net_amount = 0;
  let total_gross_amount = 0;
  let total_weighted_current_completion = 0;
  
  // Iterate through progress_entry_items
  for (let item of frm.doc.progress_entry_items) {

    // Sum up item_net_amount for all items
      total_item_net_amount += item.item_net_amount;
      total_gross_amount += item.gross_amount

    // Calculate weighted completion only if total_completion is greater than 0
    if (item.total_completion > 0) {
        
        total_weighted_completion += item.item_net_amount * (item.total_completion / 100); // Convert percentage to actual amount
    }

    if (item.current_completion >0)
    {      
      total_weighted_current_completion += item.item_net_amount * (item.current_completion / 100); // Convert percentage to actual amount
    }
  }

  console.log("total_weighted_current_completion",total_weighted_current_completion)
  console.log("total_weighted_completion",total_weighted_completion)

  frm.set_value('gross_total', total_gross_amount)

  // Calculate average completion percentage based on item_net_amount
  let average_completion = total_item_net_amount > 0 ? (total_weighted_completion / total_item_net_amount) * 100 : 0;
  // Set the average value in the form
  frm.set_value("total_completion_percentage", average_completion);

  // Current completion
  let current_completion = total_item_net_amount > 0 ? (total_weighted_current_completion / total_item_net_amount) * 100 : 0
  frm.set_value("current_completion_percentage", current_completion)

}

function make_taxes_and_totals(frm){

  console.log("from make_taxes_and_totals")

  total_gross_amount = 0

  // Tax configurations are using from the previous progress entry. So only consider taking the portion based on the current_completion
  frm.doc.progress_entry_items.forEach(row => {

      console.log("current_completion", row.current_completion)
  
      if(row.current_completion > 0){

        console.log("row in current completion:",row)

        row.gross_amount = (row.item_gross_amount * row.current_completion)/100;
        // Note that retention is not considering in the line item
        row.net_amount = (row.item_net_amount * row.current_completion)/100;
        row.tax_amount = row.item_tax_amount>0? (row.item_tax_amount * row.current_completion)/100:0

        total_gross_amount += row.gross_amount
          
      }else{
       
        row.gross_amount = 0
        row.tax_amount = 0
        row.net_amount = 0
      }

      row.total_amount = row.prev_amount + row.net_amount
      
    })

    frm.set_value('gross_total', total_gross_amount)
      
    frm.refresh_field("progress_entry_items")
    update_total_amounts(frm);    

  }

function update_total_amounts(frm){

  console.log("from update_total_amounts")

  let gross_total = 0;
  let tax_total = 0;

  let advance_amount = 0
  let retention_amount  = 0

  current_completion = frm.doc.current_completion_percentage

  if(frm.doc.project_advance_amount > 0)
  {
    advance_amount = (frm.doc.project_advance_amount * current_completion) / 100    
  }

  gross_total = frm.doc.gross_total

  if(frm.doc.retention_percentage > 0)
  {
    retention_amount = (gross_total  * frm.doc.retention_percentage) /100
    console.log(retention_amount)
  }

  let taxable_amount  = gross_total - advance_amount - retention_amount

  frm.set_value("deduction_against_advance", advance_amount)
  frm.set_value("deduction_for_retention", retention_amount)
  frm.set_value('taxable_amount',taxable_amount)  

  if(!frm.doc.tax_excluded && frm.doc.tax_rate>0)
  {
    console.log("taxable_amount",taxable_amount)
    tax_total = taxable_amount * frm.doc.tax_rate / 100
  }

  net_total = taxable_amount + tax_total

  frm.set_value('tax_total', tax_total);
  frm.set_value('net_total', net_total);
  frm.set_value('rounded_total',0)
  
  console.log("gross_total",gross_total)
  console.log("taxable_amount",taxable_amount)
  console.log("tax_total",tax_total)
  console.log("net_total",net_total)

  frappe.db.get_value('Company', frm.doc.company, 'do_not_apply_round_off_in_si', function(data) {
    
    if (data && data.do_not_apply_round_off_in_si == 1) {
     	
      frm.set_value('rounded_total',net_total)
    }
    else {
     if (frm.doc.net_total != Math.round(frm.doc.net_total)) {
       
       frm.set_value('round_off',Math.round(frm.doc.net_total) - frm.doc.net_total)	
       frm.set_value('rounded_total',Math.round(frm.doc.net_total))		 
     }
     else{

      frm.set_value('rounded_total',frm.doc.net_total)
     }
   }

   console.log("frm.doc.rounded_total")
   console.log(frm.doc.rounded_total)

   update_total_big_display(frm)  

  });
  
}

function update_total_big_display(frm) {
  // Ensure `rounded_total` has a valid value; fallback to 0 if undefined or NaN
  let roundedTotal = frm.doc.rounded_total || 0;

  // Safely parse the value to a number and round it off
  let display_total = isNaN(parseFloat(roundedTotal)) ? 0 : parseFloat(roundedTotal).toFixed(0);

  // Add 'AED' prefix and format for display
  let displayHtml = `<div style="font-size: 25px; text-align: right; color: black;">AED ${display_total}</div>`;

  // Update the HTML content of the 'total_big' field
  frm.fields_dict['total_big'].$wrapper.html(displayHtml);

  // No need to refresh `total_big` as it’s directly modified
}

function get_default_company_and_warehouse(frm) {
  frappe.call({
      method: 'frappe.client.get_value',
      args: { 
          doctype: 'Global Settings', 
          fieldname: 'default_company' 
      },
      callback: (r) => {
          if (r && r.message) {
              frm.set_value('company', r.message.default_company);

              // Ensure frm.company is set before fetching tax details
              if (frm.doc.company) {
                  frappe.db.get_value(
                      "Company", 
                      frm.doc.company, 
                      ["tax_excluded", "tax","boq_with_manual_item_selection"]
                  ).then((res) => {
                      if (res && res.message) {
                          frm.set_value('tax_excluded', res.message.tax_excluded);
                          frm.set_value('tax', res.message.tax);
                          frm.set_value('boq_with_manual_item_selection',res.message.boq_with_manual_item_selection)



                          // Check if tax_excluded is false, then fetch tax_rate from Tax doctype
                          if (!res.message.tax_excluded) {
                              frappe.db.get_value(
                                  "Tax", 
                                  res.message.tax, 
                                  "tax_rate"
                              ).then((taxRes) => {
                                  if (taxRes && taxRes.message) {
                                      frm.set_value('tax_rate', taxRes.message.tax_rate);
                                  }
                              });
                          }
                      }
                  });
              }
          }
      }
  });
}

function highlight_amended_rows(frm) {
  // Loop through each child row
  frm.doc.progress_entry_items.forEach(function(row) {
    // Get the grid row
    const grid_row = frm.fields_dict["progress_entry_items"].grid.grid_rows_by_docname[row.name];

    if (row.amendment_mode === "Deletion") {
      // Apply background color to the row for "Deletion"
      $(grid_row.row).css({
        "background-color": "#ffcccc", // Light red
        "color": "#000000"            // Optional: black text for better readability
      });
    }
    else if(row.amendment_mode =="Addition")
    {
      $(grid_row.row).css({
        "background-color": "lightblue", // Light red
        "color": "#000000"            // Optional: black text for better readability
      });
    }
    else {
      // Reset the background color for other rows
      $(grid_row.row).css({
        "background-color": "",
        "color": ""
      });
    }
  });
}
