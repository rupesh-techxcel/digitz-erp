// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Additional Expense Entry", {
	refresh(frm) {
  },
  onload: function(frm)
  {
    assign_defaults(frm);
  },
  is_sales: function(frm){
    if (cur_frm.doc.is_sales == 1) {
      cur_frm.set_df_property('additional_cost_purchase', 'hidden', 1);
			cur_frm.set_df_property('get_purchase', 'hidden', 1);
			cur_frm.set_df_property('purchase_item', 'hidden', 1);
			cur_frm.set_df_property('get_purchase_items', 'hidden', 1);
    }
    else
    {
      cur_frm.set_df_property('additional_cost_purchase', 'hidden', 0);
			cur_frm.set_df_property('get_purchase', 'hidden', 0);
			cur_frm.set_df_property('purchase_item', 'hidden', 0);
			cur_frm.set_df_property('get_purchase_items', 'hidden', 0);
    }

  },
	make_taxes_and_totals: function(frm) {
    var total_taxes_and_charges = 0;
		frm.doc.grand_total = 0;
		frm.doc.expense_details.forEach(function (entry) {
			var tax_rate = 0;
      var amount = 0;
			var total_amount = 0;
			total_amount = entry.amount + entry.tax_rate;
			total_taxes_and_charges += total_amount
      frappe.model.set_value(entry.doctype, entry.name, "total_amount", total_amount);
		});
		frm.set_value('total_taxes_and_charges', total_taxes_and_charges);
		frm.refresh_fields('expense_details');
		frm.refresh_fields();
	},
	get_sales: function(frm){
		let d = new frappe.ui.Dialog({
    title: 'Get the Sales',
    fields: [
        {
            label: 'Sales Details',
            fieldname: 'sales_details',
            fieldtype: 'Table',
            fields: [
                {
                    label: 'Customer',
                    fieldtype: 'Link',
                    options: 'Customer',
                    fieldname: 'customer',
                    in_list_view: 1
                },
                {
                    label: 'Sales Invoice',
                    fieldtype: 'Link',
                    options: 'Sales Invoice',
                    fieldname: 'sales_invoice',
                    in_list_view: 1,
                    get_query: function(doc) {
                        return {
                            filters: {
                                "customer": doc.customer,
                            }
                        };
                    }
                },
                {
                    label: 'Grand Total',
                    fieldtype: 'Currency',
                    fieldname: 'grand_total',
                    in_list_view: 1
                }
            ],
        }
    ],
    size: 'large',
    primary_action_label: 'Submit',
    primary_action: function(values) {
        console.log(values);
				var salesDetails = values.sales_details;
				for (var i = 0; i < salesDetails.length; i++) {
						var child = frm.add_child('additional_cost_sales');
						child.customer = salesDetails[i].customer;
						child.sales_invoice = salesDetails[i].sales_invoice;
						child.grand_total = salesDetails[i].grand_total;
				}
				frm.refresh_field('additional_cost_sales');
        d.hide();
    }
});

d.show();

},
	get_purchase: function(frm){
		let d = new frappe.ui.Dialog({
    title: 'Get the Purchase',
    fields: [
        {
            label: 'Purchase Details',
            fieldname: 'purchase_details',
            fieldtype: 'Table',
            fields: [
                {
                    label: 'Supplier',
                    fieldtype: 'Link',
                    options: 'Supplier',
                    fieldname: 'supplier',
                    in_list_view: 1
                },
                {
                    label: 'Purchase Invoice',
                    fieldtype: 'Link',
                    options: 'Purchase Invoice',
                    fieldname: 'purchase_invoice',
                    in_list_view: 1,
                    get_query: function(doc) {
                        return {
                            filters: {
                                "supplier": doc.supplier,
                            }
                        };
                    }
                },
                {
                    label: 'Grand Total',
                    fieldtype: 'Currency',
                    fieldname: 'grand_total',
                    in_list_view: 1,
                }
            ],
        }
    ],
    size: 'large',
    primary_action_label: 'Submit',
    primary_action: function(values) {
        console.log(values);
				var purchaseDetails = values.purchase_details;
				for (var i = 0; i < purchaseDetails.length; i++) {
						var child = frm.add_child('additional_cost_purchase');
						child.supplier = purchaseDetails[i].supplier;
						child.purchase_invoice = purchaseDetails[i].purchase_invoice;
						child.grand_total = purchaseDetails[i].grand_total;
				}
				frm.refresh_field('additional_cost_purchase');
        d.hide();
    }
});

d.show();

},
	get_purchase_items: function(frm){
		var selectedInvoices = frm.doc.additional_cost_purchase.map(row => row.purchase_invoice);
		frappe.call({
        method: "digitz_erp.stock.doctype.additional_expense_entry.additional_expense_entry.get_purchase_invoice_items",
        args: {
            selected_invoices: selectedInvoices
        },
        callback: function(response) {
            if (response.message) {
                frm.clear_table('purchase_item');
                response.message.forEach(function(item) {
                    var row = frappe.model.add_child(frm.doc, 'purchase_item', 'purchase_item');
                    row.item_code = item.item;
                    row.qty = item.qty;
                    row.amount = item.net_amount;
                });

                frm.refresh_field('purchase_item');
            }
        }
    });
	},
	get_sales_items: function(frm){
		var selectedInvoices = frm.doc.additional_cost_sales.map(row => row.sales_invoice);
		frappe.call({
				method: "digitz_erp.stock.doctype.additional_expense_entry.additional_expense_entry.get_sales_invoice_items",
				args: {
						selected_invoices: selectedInvoices
				},
				callback: function(response) {
						if (response.message) {
								frm.clear_table('sales_item');
								response.message.forEach(function(item) {
										var row = frappe.model.add_child(frm.doc, 'sales_item', 'sales_item');
										row.item_code = item.item;
										row.qty = item.qty;
										row.amount = item.net_amount;
								});

								frm.refresh_field('sales_item');
						}
				}
		});
	}
});

function assign_defaults(frm)
{
    default_company = "";
    frappe.call({
      method: 'frappe.client.get_value',
      args: {
        'doctype': 'Global Settings',
        'fieldname': 'default_company'
      },
      callback: (r) => {
        default_company = r.message.default_company
        frm.set_value('company',default_company);
        frm.refresh_field("company")
      }
    });
  }

	frappe.ui.form.on('Expense Details', {
		amount: function(frm, cdt, cdn) {
			frm.trigger("make_taxes_and_totals");
		},
		tax_rate: function(frm, cdt, cdn) {
	    frm.trigger("make_taxes_and_totals");
	  },
		expense_details_add: function(frm, cdt, cdn) {
	    frm.trigger("make_taxes_and_totals");
	  },
	  expense_details_remove: function(frm, cdt, cdn) {
	    frm.trigger("make_taxes_and_totals");
	  },
		tax_excluded: function(frm, cdt, cdn){
			var child = locals[cdt][cdn];
			if (child.tax_excluded == 1) {
				frappe.model.set_value(cdt, cdn, 'tax_rate', 0);
				frappe.model.set_value(cdt, cdn, 'tax', '');
			}
			else{
				frappe.model.set_value(cdt, cdn, 'tax_rate', '');
			}
		},
		total_taxes_and_charges: function(frm, cdt, cdn){
			frm.trigger("make_taxes_and_totals");
		}
	});
