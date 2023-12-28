// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Credit Note", {
	onload(frm) {
    frm.trigger("get_default_company_and_warehouse");
	},
	refresh(frm){
		frm.set_query('credit_account', 'credit_note_item', () => {
      return {
        filters: {
          root_type: ['in',  ['Income', 'Assets']],
          is_group: 0
        }
      }
    })
	},
  edit_posting_date_and_time(frm) {
    if (frm.doc.edit_posting_date_and_time == 1) {
      frm.set_df_property("date", "read_only", 0);
      frm.set_df_property("posting_time", "read_only", 0);
    }
    else {
      frm.set_df_property("date", "read_only", 1);
      frm.set_df_property("posting_time", "read_only", 1);
    }
  },
  setup(frm){
    frm.add_fetch('customer', 'full_address', 'address')
		frm.add_fetch('customer', 'tax_id', 'tax_id')
		frm.add_fetch('customer', 'credit_days', 'credit_days')
		frm.add_fetch('payment_mode', 'account', 'payment_account')
  },
  credit_sales(frm) {
		frm.set_df_property("credit_days", "hidden", !frm.doc.credit_sales);
		frm.set_df_property("payment_mode", "hidden", frm.doc.credit_sales);
		frm.set_df_property("payment_account", "hidden", frm.doc.credit_sales);

		if (frm.doc.credit_sales) {
			frm.doc.payment_mode = "";
			frm.doc.payment_account = "";
		}
	},
  customer(frm){

	frappe.call(
		{
			method: 'digitz_erp.accounts.doctype.gl_posting.gl_posting.get_party_balance',
			args: {
				'party_type': 'Customer',
				'party': frm.doc.customer
			},
			callback: (r) => {
				frm.set_value('customer_balance',r.message)
				frm.refresh_field("customer_balance");
			}
		});

  },
	// rate_includes_tax: function(frm) {
  //   frappe.confirm('Are you sure you want to change this setting which will change the tax calculation in the expense entry ?', () => {
  //     frm.trigger("make_taxes_and_totals");
  //   })
	// },
	// make_taxes_and_totals: function(frm) {
	// 	var total_amount = 0;
	// 	var tax_total = 0;
  //   var grand_total = 0;
	// 	frm.doc.total_amount = 0;
	// 	frm.doc.tax_total = 0;
	// 	frm.doc.grand_total = 0;
	// 	frm.doc.credit_note_item.forEach(function (entry) {
	// 		var tax_in_rate = 0;
  //     var amount_excluded_tax = 0;
  //     var tax_amount = 0;
  //     var total = 0;
	// 		entry.rate_included_tax = frm.doc.rate_includes_tax;
	// 		if (entry.rate_included_tax)
  //     {
	// 			tax_in_rate = entry.amount * (entry.tax_rate / (100 + entry.tax_rate));
	// 			amount_excluded_tax = entry.amount - tax_in_rate;
	// 			tax_amount = entry.amount * (entry.tax_rate / (100 + entry.tax_rate))
	// 		}
	// 		else {
	// 			amount_excluded_tax = entry.amount;
	// 			tax_amount = (entry.amount * (entry.tax_rate / 100))
	// 		}
  //     total = amount_excluded_tax + tax_amount;
  //     frappe.model.set_value(entry.doctype, entry.name, "amount_excluded_tax", amount_excluded_tax);
  //     frappe.model.set_value(entry.doctype, entry.name, "tax_amount", tax_amount);
  //     frappe.model.set_value(entry.doctype, entry.name, "total", total);
  //     total_amount  = grand_total+entry.amount;
	// 		tax_total = tax_total + entry.tax_amount;
  //     grand_total  = grand_total+entry.total;
	// 	});
  //   frm.set_value('total_amount', total_amount);
  //   frm.set_value('tax_total', tax_total);
  //   frm.set_value('grand_total', grand_total);
	// 	frm.refresh_fields();
	// },
  get_default_company_and_warehouse(frm) {
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
              //frm.doc.rate_includes_tax = r2.message.rate_includes_tax;
              frm.refresh_field("warehouse");
              frm.refresh_field("rate_includes_tax");
            }
          }

        )
      }
    })

  },

});
frappe.ui.form.on('Credit Note Item',{
	tax_excluded: function(frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        if (child.tax_excluded == 1) {
            frappe.model.set_value(cdt, cdn, 'tax_rate', 0);
						frappe.model.set_value(cdt, cdn, 'tax', '');
        }
				else{
					frappe.model.set_value(cdt, cdn, 'tax_rate', '');
				}
    },
		credit_note_item_add: function(frm,cdt,cdn){

	    let row = frappe.get_doc(cdt, cdn);
	    row.payable_account = frm.doc.default_payable_account
	    frm.refresh_field("credit_note_item");

	  },
		amount: function(frm, cdt, cdn){
    let d = locals[cdt][cdn];
    var total_amount = 0
    frm.doc.credit_note_item.forEach(function(d){
      total_amount += d.amount;
    })
    frm.set_value('total_amount',total_amount)
  },
	// tax_amount: function(frm, cdt, cdn) {
  //   var tax_total = 0;
  //   frm.doc.credit_note_item.forEach(function(d) {
  //     tax_total += d.tax_amount;
  //   })
  //   frm.set_value('tax_total', tax_total);
  // }
})
