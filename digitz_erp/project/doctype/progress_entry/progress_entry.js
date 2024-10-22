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
      get_default_company_and_warehouse(frm);
      frm.fields_dict['progress_entry_items'].grid.grid_rows.forEach(function(row) {
        update_total_completion_readonly(frm, row.doc);
      });
    }

    frm.set_query('previous_progress_entry', () => ({
      filters: {
        name: ['!=', frm.doc.name],
        project: frm.doc.project
        // sales_order: frm.doc.sales_order,
      }
    }));

    frappe.call({
      method: 'digitz_erp.api.project_api.check_proforma_invoice',
      args: { progress_entry: frm.doc.name },
      callback: function(response) {
        if (!response.message) {
          frm.add_custom_button(__('Create Proforma Invoice'), function() {
            frappe.model.with_doctype('Proforma Invoice', function() {
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
      callback: function(response) {
        if (!response.message) {
          frm.add_custom_button(__('Create Progressive Invoice'), function() {
            frappe.model.with_doctype('Progressive Sales Invoice', function() {
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
    if (frm.doc.project && frm.doc.is_prev_progress_exists === 0) {
      frm.set_value("total_completion_percentage", 0);
      if (frm.doc.sales_order) {
        fetch_boq_or_sales_order_items(frm);  // Updated function
      }
    } else {
      frm.set_value("total_completion_percentage", 0);
      reset_totals(frm);
      frm.refresh_field("progress_entry_items");
      frm.refresh_fields();

      if (frm.doc.previous_progress_entry && frm.doc.previous_progress_entry !== frm.doc.name) {
        fetch_previous_progress_entry(frm);
      }
    }
  },

  is_prev_progress_exists(frm) {
    if (frm.doc.is_prev_progress_exists === 0) {
      frm.set_value("previous_progress_entry", "");
    }
    frm.trigger('project');
  },

  previous_progress_entry(frm) {
    frm.trigger('project');
  }
});

function fetch_boq_or_sales_order_items(frm) {
  // Check if the BOQ is available for the project
  frappe.call({
    method: "frappe.client.get",
    args: { doctype: "Sales Order", name: frm.doc.sales_order },
    callback: function(r) {
      if (r.message && r.message.boq) {
        // Fetch items from the BOQ if it exists
        fetch_boq_items(frm, r.message.boq);
      } else {
        // Fallback to fetching items from Sales Order if no BOQ exists
        fetch_sales_order_items(frm);
      }
    }
  });
}

function fetch_boq_items(frm, boq) {
  frappe.call({
    method: "frappe.client.get",
    args: { doctype: "BOQ", name: boq },
    callback: function(r) {
      if (r.message && r.message.boq_items) {
        frm.clear_table("progress_entry_items");
        r.message.boq_items.forEach(item => {
          const row = frm.add_child("progress_entry_items");
          row.item = item.item;
          row.item_name = item.item_name;
          row.item_gross_amount = item.gross_amount;
          row.item_tax_amount = item.tax_amount;
          row.item_net_amount = item.net_amount;
        });
        frm.refresh_field("progress_entry_items");
        frm.refresh_fields();
      } else {
        frappe.msgprint(__("No items found in the selected BOQ."));
      }
    }
  });
}

function fetch_sales_order_items(frm) {
  frappe.call({
    method: "frappe.client.get",
    args: { doctype: "Sales Order", name: frm.doc.sales_order },
    callback: function(r) {
      if (r.message && r.message.items) {
        frm.clear_table("progress_entry_items");
        r.message.items.forEach(item => {
          const row = frm.add_child("progress_entry_items");
          row.sales_order_amt = r.message.net_total;
          row.item = item.item;
          row.item_name = item.item_name;
          row.item_gross_amount = item.gross_amount;
          row.item_tax_amount = item.tax_amount;
          row.item_net_amount = item.net_amount;
        });
        frm.refresh_field("progress_entry_items");
        frm.refresh_fields();
      } else {
        frappe.msgprint(__("No items found for the selected Sales Order."));
      }
    }
  });
}

function fetch_previous_progress_entry(frm) {
  frappe.call({
    method: "frappe.client.get",
    args: { doctype: "Progress Entry", name: frm.doc.previous_progress_entry },
    callback: function(r) {
      if (r.message && r.message.progress_entry_items) {
        update_items_from_previous_progress_entry(frm, r);
      } else {
        frappe.msgprint(__("No items found in the selected Progress Entry."));
      }
    }
  });
}

function update_items_from_previous_progress_entry(frm, r) {
  r.message.progress_entry_items.forEach(item => {
    if (item.total_completion !== 100) {
      const row = frm.add_child("progress_entry_items");
      row.sales_order_amt = frm.doc.sales_order_net_total;
      row.prev_completion = item.total_completion || 0;
      row.total_amount = item.total_amount || 0;
      row.prev_amount = item.total_amount || 0;
      row.item = item.item;
      row.item_name = item.item_name;
      row.rate = item.rate;
      row.item_gross_amount = item.item_gross_amount;
      row.item_tax_amount = item.item_tax_amount;
      row.item_net_amount = item.item_net_amount;
    }
  });

  frm.doc.total_completion_percentage = r.message.total_completion_percentage;
  if (frm.doc.total_completion_percentage === 100) {
    frappe.msgprint("The Completion Percentage is already 100%");
  }

  frm.refresh_field("progress_entry_items");
  frm.refresh_fields();
  update_total_amounts(frm);
}

frappe.ui.form.on("Progress Entry Items", {
  prev_completion: function(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    update_total_completion_readonly(frm, row);
  },

  progress_entry_items_add(frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);
    frappe.model.set_value(cdt, cdn, 'sales_order_amt', frm.doc.sales_order_net_total);

    frappe.call({
      method: 'digitz_erp.api.settings_api.get_default_tax',
      async: false,
      callback(r) {
        row.tax = r.message;
        frappe.call({
          method: 'frappe.client.get_value',
          args: { doctype: 'Tax', filters: { tax_name: row.tax }, fieldname: ['tax_name', 'tax_rate'] },
          callback(r2) {
            row.tax_rate = r2.message.tax_rate;
            frm.refresh_field("progress_entry_items");
          }
        });
      }
    });
  }
});

function reset_totals(frm) {
  frm.set_value("gross_total", "");
  frm.set_value("tax_total", "");
  frm.set_value("net_total", "");
  frm.set_value("total_discount_in_line_items", "");
  frm.set_value("additional_discount", "");
  frm.set_value("round_off", "");
  frm.set_value("rounded_total", "");
  frm.set_value("in_words", "");
}
