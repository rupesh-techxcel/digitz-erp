// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt
frappe.ui.form.on("Progress Entry", {

  // Triggered after the form is loaded
//   onload(frm) {
//     // Set up custom handlers after the form is fully loaded
//     setup_custom_handlers(frm);
// },
validate(frm){
    if(frm.doc.previous_progress_entry == frm.doc.name){
        frappe.throw("Choose a valid Progress Entry !")
    }
},
setup(frm){
  // let project = localStorage.getItem("current_project");
  // let prev_progress_entry = localStorage.getItem("prev_progress_entry");

  // // localStorage.clear();
  //   if(project){
  //     frm.set_value("project", project);
  //   }

  //   if(prev_progress_entry){
  //     frm.set_value('is_prev_progress_exists',1);
  //     frm.set_value('previous_progress_entry', prev_progress_entry);

  //     localStorage.removeItem('prev_progress_entry')
  //     localStorage.removeItem('current_project')
    // }
  
  
},

// Triggered when the form is refreshed
refresh(frm) {
      frm.fields_dict['progress_entry_items'].grid.grid_rows.forEach(function(row) {
          update_total_completion_readonly(frm, row.doc);
      });

    if(frm.is_new()){
        get_default_company_and_warehouse(frm)
    }

    frm.set_query('previous_progress_entry', function() {
        return {
            filters: {
                name: ['!=', frm.doc.name],
                project: frm.doc.project,
                sales_order: frm.doc.sales_order
            }
        };
    });

    frappe.call(
      {
        method: 'frappe.client.get_value',
        args: {
          'doctype': 'Tax',
          'filters': { 'tax_name': r.message.tax },
          'fieldname': ['tax_name', 'tax_rate']
        },
        callback: (r2) => {
  
          for(row in frm.doc.progress_entry_items){
  
            row.tax = r2.message.tax_name;
            row.tax_rate = r2.message.tax_rate
          }
        }
  
      })
    // Optionally, add custom buttons or actions here if needed
  },
  project(frm){
    frm.set_value('progress_entry_items',[]);
    if (frm.doc.project && frm.doc.is_prev_progress_exists == 0) {
        // Fetch the Sales Order linked to this project
        // frappe.call({
        //   method: "frappe.client.get_value",
        //   args: {
        //     doctype: "Project",
        //     filters: { name: frm.doc.project },
        //     fieldname: "sales_order",
        //   },
        //   callback: function (r) {
        //     if (r.message && r.message.sales_order) {
        //       frm.set_value("sales_order", r.message.sales_order);
        //       fetch_sales_order_items(frm);
        //     } else {
        //       frappe.msgprint(
        //         __("No Sales Order found for the selected Project.")
        //       );
        //     }
        //   },
        // });
        frm.set_value("average_of_completion",0);
        if(frm.doc.sales_order){
          fetch_sales_order_items(frm);
        }
    }
    else{
        

        frm.set_value("average_of_completion",0);
        frm.set_value("gross_total","");
        frm.set_value("tax_total","");
        frm.set_value("net_total","");
        frm.set_value("total_discount_in_line_items","");
        frm.set_value("additional_discount","");
        frm.set_value("round_off","");
        frm.set_value("rounded_total","");
        frm.set_value("in_words","");
      // Refresh the field to show the updated items
      frm.refresh_field("progress_entry_items");
      frm.refresh_fields()

        if(frm.doc.previous_progress_entry && frm.doc.previous_progress_entry != frm.doc.name){
          
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Progress Entry",
                    name: frm.doc.previous_progress_entry,
                },
                callback: function (r) {
                  if (r.message && r.message.progress_entry_items) {
                    frm.set_value('progress_entry_items',[]);
                    update_table_and_total(frm,r);
                  } else {
                    frappe.msgprint(
                      __(`No Items Are In Previous Progress Entry, ${frm.doc.previous_progress_entry}.`)
                    );
                  }
                },
              });
        }else{
            if(frm.doc.previous_progress_entry == frm.doc.name){
                frappe.throw(`Choose a valid Progress Entry !`);
            }
        }
    }
  },
  is_prev_progress_exists(frm){
      if(frm.doc.is_prev_progress_exists == 0){
          frm.set_value("previous_progress_entry","");
        }
        frm.trigger('project');
  },
  previous_progress_entry(frm){
    frm.trigger('project');
  }
});

function setup_custom_handlers(frm) {
  // Set up handler for Project field
//   frm.set_query("project", function () {
//     return {
//       filters: {
//         // Add any necessary filters for the Project field
//       },
//     };
//   });

  // Set up handler for Sales Order field
//   frm.fields_dict["sales_order"].df.onchange = function () {
//     if (frm.doc.sales_order) {
//       fetch_sales_order_items(frm);
//     }
//   };
}

function fetch_sales_order_items(frm) {
  // Fetch the Sales Order details
  frappe.call({
    method: "frappe.client.get",
    args: {
      doctype: "Sales Order",
      name: frm.doc.sales_order,
    },
    callback: function (r) {
      if (r.message && r.message.items) {
        console.log(r.message.items);
        // Clear existing items
        frm.clear_table("progress_entry_items");

        // Add items from the Sales Order to Progress Entry Items
        r.message.items.forEach(function (item) {
          // Create a new row in Progress Entry Items table
          const row = frm.add_child("progress_entry_items");

          row.sales_order_amt = r.message.net_total;
          // Assigning values to the row fields

          // row.lumpsum_amount = item.lumpsum_0.000amount;
          // row.rate_includes_tax = item.rate_includes_tax;
          // row.tax_excluded = item.tax_excluded;
          // row.discount_percentage = item.discount_percentage;
          // row.discount_amount = item.discount_amount;
          // row.warehouse = item.warehouse;
          row.item = item.item;
          row.item_name = item.item_name;
          // row.display_name = item.display_name;
          // row.qty = item.qty;
          // row.unit = item.unit;
          // row.rate = item.rate;
          // row.base_unit = item.base_unit;
          // row.qty_in_base_unit = item.qty_in_base_unit;
          // row.rate_in_base_unit = item.rate_in_base_unit;
          // row.conversion_factor = item.conversion_factor;
          // row.rate_excluded_tax = item.rate_excluded_tax;
          row.item_gross_amount = item.gross_amount;
          // row.tax = item.tax;
          // row.tax_rate = item.tax_rate;
          row.item_tax_amount = item.tax_amount;
          row.item_net_amount = item.net_amount;
          // row.unit_conversion_details = item.unit_conversion_details;
          // row.cost_center = item.cost_center;
          // row.qty_sold_in_base_unit = item.qty_sold_in_base_unit;
          // row.quotation_item_reference_no = item.quotation_item_reference_no;

          // Refresh the field to update the table
          frm.refresh_field("progress_entry_items");

          // Optionally, adjust fields if necessary
          // row.custom_field = item.custom_field || default_value;
        });

        // frm.doc.gross_total = r.message.gross_total;
        // frm.doc.tax_total = r.message.tax_total;
        // frm.doc.net_total = r.message.net_total;
        // frm.doc.total_discount_in_line_items = r.message.total_discount_in_line_items;
        // frm.doc.additional_discount = r.message.additional_discount;
        // frm.doc.round_off = r.message.round_off;
        // frm.doc.rounded_total = r.message.rounded_total;
        // frm.doc.in_words = r.message.in_words;
        // Refresh the field to show the updated items
        frm.refresh_field("progress_entry_items");
        frm.refresh_fields()
      } else {
        frappe.msgprint(__("No items found for the selected Sales Order."));
      }
    },
    
  });
}


function update_table_and_total(frm,r){
    r.message.progress_entry_items.forEach(function (item) {
        // Create a new row in Progress Entry Items table
        const row = frm.add_child("progress_entry_items");

        row.sales_order_amt = frm.doc.sales_order_net_total;

        // Assigning values to the row fields
        row.prev_completion = item.total_completion || 0;
        row.total_completion = item.total_completion;
        row.total_amount = item.total_amount || 0;
        row.prev_amount = item.total_amount || 0;

        // row.lumpsum_amount = item.lumpsum_amount;
        // row.rate_includes_tax = item.rate_includes_tax;
        // row.tax_excluded = item.tax_excluded;
        // row.discount_percentage = item.discount_percentage;
        // row.discount_amount = item.discount_amount;
        // row.warehouse = item.warehouse;
        row.item = item.item;
        row.item_name = item.item_name;
        // row.display_name = item.display_name;
        // row.qty = item.qty;
        // row.unit = item.unit;
        row.rate = item.rate;
        // row.base_unit = item.base_unit;
        // row.qty_in_base_unit = item.qty_in_base_unit;
        // row.rate_in_base_unit = item.rate_in_base_unit;
        // row.conversion_factor = item.conversion_factor;
        // row.rate_excluded_tax = item.rate_excluded_tax;
        row.item_gross_amount = item.item_gross_amount;
        // row.gross_amount = item.gross_amount;
        // row.tax = item.tax;
        // row.tax_rate = item.tax_rate;
        row.item_tax_amount = item.item_tax_amount;
        // row.tax_amount = item.tax_amount;

        row.item_net_amount = item.item_net_amount;
        // row.net_amount = item.net_amount;
        // row.unit_conversion_details = item.unit_conversion_details;
        // row.cost_center = item.cost_center;
        // row.qty_sold_in_base_unit = item.qty_sold_in_base_unit;
        // row.quotation_item_reference_no = item.quotation_item_reference_no;

        // Refresh the field to update the table
        frm.refresh_field("progress_entry_items");

        // Optionally, adjust fields if necessary
        // row.custom_field = item.custom_field || default_value;
      });

      frm.doc.average_of_completion = r.message.average_of_completion;

      // frm.doc.gross_total = r.message.gross_total;
      // frm.doc.tax_total = r.message.tax_total;
      // frm.doc.net_total = r.message.net_total;
      // frm.doc.total_discount_in_line_items = r.message.total_discount_in_line_items;
      // frm.doc.additional_discount = r.message.additional_discount;
      // frm.doc.round_off = r.message.round_off;
      // frm.doc.rounded_total = r.message.rounded_total;
      // frm.doc.in_words = r.message.in_words;
      // Refresh the field to show the updated items
      frm.refresh_field("progress_entry_items");
      frm.refresh_fields()
}



frappe.ui.form.on("Progress Entry Items", {
  prev_completion: function(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    update_total_completion_readonly(frm, row);
  },

  progress_entry_items_add(frm,cdt,cdn){
    let row = frappe.get_doc(cdt,cdn);
    frappe.model.set_value(cdt,cdn,'sales_order_amt', frm.doc.sales_order_net_total);

    frappe.call(
      {
        method:'digitz_erp.api.settings_api.get_default_tax',
        async:false,
        callback(r){
            row.tax = r.message

        frappe.call({
          method: 'frappe.client.get_value',
          args: {
            'doctype': 'Tax',
            'filters': { 'tax_name': row.tax },
            'fieldname': ['tax_name', 'tax_rate']
          },
          callback: (r2) => {
            row.tax_rate = r2.message.tax_rate;
            frm.refresh_fields("progress_entry_items");
          }
        });

        }
      }
    );

  frm.refresh_fields("progress_entry_items");
  },
  prev_completion(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    console.log(row);

    if (row.prev_completion > 100) {
      row.prev_completion = 0;
      frappe.msgprint({
        title: __("Validation Error"),
        indicator: "red",
        message: __("Completion % can't be more than 100%"),
      });
    } else {
      update_progress(frm);
    }

    frappe.model.set_value(cdt,cdn, 'prev_amount', ((row.net_amount * row.prev_completion)/100));

    total_of_prev_and_curr_amount(frm);
  },
  total_completion(frm,cdt,cdn){
    let row = frappe.get_doc(cdt, cdn);
    console.log(row);

    if(!row.tax){
      frappe.call(
        {
          method:'digitz_erp.api.settings_api.get_default_tax',
          async:false,
          callback(r){
              row.tax = r.message
  
          frappe.call(
            {
            method: 'frappe.client.get_value',
            args: {
              'doctype': 'Tax',
              'filters': { 'tax_name': row.tax },
              'fieldname': ['tax_name', 'tax_rate']
            },
            callback: (r2) => {
              row.tax_rate = r2.message.tax_rate;
              frm.refresh_fields("progress_entry_items");
              update_all_amount_of_line_item(frm,cdt,cdn);
            }
            });
  
          }
        })
    }

    if (row.total_completion > 100) {
      row.total_completion = 0;
      frappe.msgprint({
        title: __("Validation Error"),
        indicator: "red",
        message: __("Completion % can't be more than 100%"),
      });
    } else {
      update_progress(frm);
    }

    // frappe.model.set_value(cdt,cdn, 'total_amount', ((row.net_amount * row.total_completion)/100));
    frappe.model.set_value(cdt,cdn, 'current_completion', (row.total_completion - row.prev_completion));

    update_all_amount_of_line_item(frm,cdt,cdn);

    // total_of_prev_and_curr_amount(frm);
  },
  progress_entry_items_delete(frm) {
    update_progress(frm);
    update_total_amounts(frm);
  },
  tax(frm,cdt,cdn){
    update_all_amount_of_line_item(frm,cdt,cdn);
  },
  tax_rate(frm,cdt,cdn){
    update_all_amount_of_line_item(frm,cdt,cdn);
  }

});

function update_progress(frm) {
  let total_percentage = 0;
  let total_items = frm.doc.progress_entry_items.length;
  for (item of frm.doc.progress_entry_items) {
    if(item.total_completion > 0){
      total_percentage += item.total_completion;
    }
    console.log( item.total_completion)
  }
  frm.set_value("average_of_completion", total_percentage / total_items);
}


function  get_default_company_and_warehouse(frm) {
    var default_company = ""
    console.log("From Get Default Warehouse Method in the parent form")

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
                        'fieldname': ['default_warehouse', 'rate_includes_tax']
                    },
                    callback: (r2) => {
                        console.log("Before assign default warehouse");
                        console.log(r2.message.default_warehouse);
                        frm.doc.warehouse = r2.message.default_warehouse;
                        console.log(frm.doc.warehouse);
                        frm.doc.rate_includes_tax = r2.message.rate_includes_tax;
                        frm.refresh_field("warehouse");
                        frm.refresh_field("rate_includes_tax");
                    }
                }

            )
        }
    })

}


function total_of_prev_and_curr_amount(frm){
  let net_prev_total = 0;
  let net_total_amount = 0;
  frm.doc.progress_entry_items.forEach(element => {
    net_prev_total += element.prev_amount || 0;
    net_total_amount += element.total_amount || 0;
  });

  frm.set_value('prev_total_amount', net_prev_total);
  frm.set_value('current_total_amount', net_total_amount);

  frm.refresh_fields('prev_total_amount','current_total_amount');
}


function update_all_amount_of_line_item(frm,cdt,cdn){
  let row = frappe.get_doc(cdt, cdn);
  if(row.current_completion > 0){
    let gross_amount = (row.item_net_amount * row.current_completion)/100;
    frappe.model.set_value(cdt,cdn,'gross_amount',gross_amount);

    let tax_amount = 0;
      if(row.tax && row.tax_rate){
          tax_amount = (row.gross_amount * row.tax_rate)/100;
      }
      frappe.model.set_value(cdt,cdn,'tax_amount',tax_amount);

      frappe.model.set_value(cdt,cdn, 'net_amount',(row.gross_amount + row.tax_amount));

      
  }else{
    frappe.model.set_value(cdt,cdn,'gross_amount',0);
    frappe.model.set_value(cdt,cdn,'tax_amount',0);
    frappe.model.set_value(cdt,cdn,'net_amount',0);
  }

  frappe.model.set_value(cdt,cdn, 'total_amount',(row.prev_amount + row.net_amount));


  update_total_amounts(frm);
}

function update_tax_amount(frm,cdt,cdn){
  let row = frappe.get_doc(cdt,cdn);
  let tax_amount = 0;
      if(row.tax_rate){
          tax_amount = (row.item_net_amount * row.tax_rate)/100;
      }
      frappe.model.set_value(cdt,cdn,'tax_amount',tax_amount);
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
}






function update_total_completion_readonly(frm, row) {
  if (row.prev_completion === 100) {
      frm.set_df_property('progress_entry_items', 'total_completion', 'read_only', 1, row.name);
      if (row.total_completion !== 100) {
          frappe.model.set_value(row.doctype, row.name, 'total_completion', 100);
      }
  } else {
      frm.set_df_property('progress_entry_items', 'total_completion', 'read_only', 0, row.name);
  }
}