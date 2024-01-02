// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Debit Note", {
	onload(frm) {
		assign_defaults(frm);
	},
	refresh(frm){
		frm.set_query('debit_account', 'debit_note_items', () => {
      return {
        filters: {
          root_type: ['in',  ['Expense', 'Liability']],
          is_group: 0
        }
      }
    })
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
	// 	frm.doc.debit_note_items.forEach(function (entry) {
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
	setup(frm){
		frm.add_fetch('supplier', 'tax_id', 'tax_id')
		frm.add_fetch('supplier', 'full_address', 'supplier_address')
		frm.add_fetch('company', 'default_warehouse', 'warehouse')
	},
	supplier(frm){
			frappe.call(
			{
				method: 'digitz_erp.api.accounts_api.get_supplier_balance',
				args: {
					'supplier': frm.doc.supplier
				},
				callback: (r) => {
					frm.set_value('supplier_balance',r.message[0].supplier_balance)
					frm.refresh_field("supplier_balance");
				}
			});
	},

  edit_posting_date_and_time: function(frm) {
		if (frm.doc.edit_posting_date_and_time == 1) {
			frm.set_df_property("date", "read_only", 0);
			frm.set_df_property("posting_time", "read_only", 0);
		}
		else {
			frm.set_df_property("date", "read_only", 1);
			frm.set_df_property("posting_time", "read_only", 1);
		}
	},
	credit_expense: function(frm) {
		frm.set_df_property("credit_days", "hidden", !frm.doc.credit_expense);
		frm.set_df_property("payment_mode", "hidden", frm.doc.credit_expense);
		frm.set_df_property("payment_account", "hidden", frm.doc.credit_expense);

		if (frm.doc.credit_expense) {
			frm.doc.payment_mode = "";
			frm.doc.payment_account = "";
		}
	},
});
function assign_defaults(frm){
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
		}
	});
	frappe.call(
		{
			method:'digitz_erp.api.settings_api.get_default_payable_account',
			async:false,
			callback(r){
				frm.set_value('default_payable_account',r.message);
			}
		}
	);
}

frappe.ui.form.on('Debit Note Item',{
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
		debit_note_items_add: function(frm,cdt,cdn){

	    let row = frappe.get_doc(cdt, cdn);
	    row.payable_account = frm.doc.default_payable_account
	    frm.refresh_field("debit_note_items");

	  },
		amount: function(frm, cdt, cdn){
    let d = locals[cdt][cdn];
    var total_amount = 0
    frm.doc.debit_note_items.forEach(function(d){
      total_amount += d.amount;
    })
    frm.set_value('total_amount',total_amount)
  },
	// tax_amount: function(frm, cdt, cdn) {
  //   var tax_total = 0;
  //   frm.doc.debit_note_items.forEach(function(d) {
  //     tax_total += d.tax_amount;
  //   })
  //   frm.set_value('tax_total', tax_total);
  // }
})
