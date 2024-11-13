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
          });
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
          });
        }
      }
    });
  },
 
  project(frm) {

    frm.set_value('progress_entry_items', []);

    if (frm.doc.project) {

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
                            } else {
                                // If no BOQ exists, fall back to Sales Order items
                                fetch_sales_order_items(frm);
                            }
                        } else {
                            frappe.msgprint(__("No items found for the selected Sales Order."));
                        }
                    }
                });
            } else {
                
            }
        } else {
            frm.set_value("total_completion_percentage", 0);
            frm.set_value("gross_total", "");
            frm.set_value("tax_total", "");
            frm.set_value("net_total", "");
            frm.set_value("total_discount_in_line_items", "");
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
                                update_from_previous_progress_entry(frm, r);

                                // If previous progress entry exists, check for amendments
                                // if (frm.doc.sales_order) {
                                //     frappe.call({
                                //         method: "frappe.client.get",
                                //         args: {
                                //             doctype: "Sales Order",
                                //             name: frm.doc.sales_order
                                //         },
                                //         callback(r) {
                                //             if (r.message && r.message.boq) {
                                //                 // Check for BOQ Amendments after the progress entry date
                                //                 check_boq_amendments_after_progress(frm, r.message.boq);
                                //             }
                                //         }
                                //     });
                                // }
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
      callback(r) {
          if (r.message && r.message.boq_items) {

              frm.clear_table("progress_entry_items");
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
              });
              frm.refresh_field("progress_entry_items");
          } else {
              frappe.msgprint(__("No items found in the linked BOQ."));
          }
      }
  });
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

    let row = frappe.get_doc(cdt, cdn);
    
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
        row.current_completion = (row.total_completion - row.prev_completion);        
        
        update_progress(frm)
        make_taxes_and_totals(frm,cdt,cdn);      
    }
  },
});

function update_progress(frm) {
  let total_weighted_completion = 0;
  let total_item_net_amount = 0;
  
  // Iterate through progress_entry_items
  for (let item of frm.doc.progress_entry_items) {
    // Sum up item_net_amount for all items
    total_item_net_amount += item.item_net_amount;

    // Calculate weighted completion only if total_completion is greater than 0
    if (item.total_completion > 0) {
      total_weighted_completion += (item.total_completion / 100) * item.item_net_amount; // Convert percentage to actual amount
    }
  }

  // Calculate average completion percentage based on item_net_amount
  let average_completion = total_item_net_amount > 0 ? (total_weighted_completion / total_item_net_amount) * 100 : 0;

  let rounded_completion = Math.round(average_completion);

  // Set the average value in the form
  frm.set_value("total_completion_percentage", rounded_completion);
}

function make_taxes_and_totals(frm){

  // Tax configurations are using from the previous progress entry. So only consider taking the portion based on the current_completion
  frm.doc.progress_entry_items.forEach(row => {
  
      if(row.current_completion > 0){

        row.gross_amount = (row.item_gross_amount * row.current_completion)/100;
        row.net_amount = (row.item_net_amount * row.current_completion)/100;
        row.tax_amount = row.item_tax_amount>0? (row.item_tax_amount * row.current_completion)/100:0
          
      }else{
       
        row.gross_amount = 0
        row.tax_amount = 0
        row.net_amount = 0
      }

      row.total_amount = row.prev_amount + row.net_amount
      
    })
      
    
    frm.refresh_field("progress_entry_items")
    update_total_amounts(frm);    

  }

function update_total_amounts(frm){

  let gross_total = 0;
  let tax_total = 0;
  let net_total = 0;
  frm.doc.progress_entry_items.forEach(element => {
    gross_total += element.gross_amount;
    tax_total += element.tax_amount;
    net_total += element.net_amount;

  });

  frm.set_value('gross_total', gross_total);
  frm.set_value('tax_total', tax_total);
  frm.set_value('net_total', net_total);
  frm.set_value('rounded_total',0)

  frappe.db.get_value('Company', frm.doc.company, 'do_not_apply_round_off_in_si', function(data) {
    
    if (data && data.do_not_apply_round_off_in_si == 1) {
      frm.doc.rounded_total = frm.doc.net_total;
      frm.refresh_field('rounded_total');				
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

	let display_total = isNaN(frm.doc.rounded_total) ? 0 : parseFloat(frm.doc.rounded_total).toFixed(0);

    // Add 'AED' prefix and format net_total for display

	let displayHtml = `<div style="font-size: 25px; text-align: right; color: black;">AED ${display_total}</div>`;


    // Directly update the HTML content of the 'total_big' field
    frm.fields_dict['total_big'].$wrapper.html(displayHtml);

    frm.refresh_field('total_big');

}

function get_default_company_and_warehouse(frm) {
  frappe.call({
    method: 'frappe.client.get_value',
    args: { doctype: 'Global Settings', fieldname: 'default_company' },
    callback: r => frm.set_value('company', r.message.default_company)
  });
}
