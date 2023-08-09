// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.
frappe.ui.form.on('Expense Entry', {
  refresh: function(frm) {
    frm.set_query('account', 'expense_entry_details', () => {
      return {
        filters: {
          root_type: "Expense",
          is_group: 0
        }
      }
    })
	},
  rate_includes_tax: function(frm) {
    frappe.confirm('Are you sure you want to change this setting which will change the tax calculation in the expense entry ?', () => {
      frm.trigger("make_taxes_and_totals");
    })
	},
  make_taxes_and_totals: function(frm) {
		var total_expense_amount = 0;
		var total_tax_amount = 0;
    var grand_total = 0;
		frm.doc.total_expense_amount = 0;
		frm.doc.total_tax_amount = 0;
		frm.doc.grand_total = 0;
		frm.doc.expense_entry_details.forEach(function (entry) {
			var tax_in_rate = 0;
      var amount_excluded_tax = 0;
      var tax_amount = 0;
      var total = 0;
			entry.rate_included_tax = frm.doc.rate_includes_tax;
			if (entry.rate_included_tax)
      {
				tax_in_rate = entry.expense_amount * (entry.tax_rate / (100 + entry.tax_rate));
				amount_excluded_tax = entry.expense_amount - tax_in_rate;
				tax_amount = entry.expense_amount * (entry.tax_rate / (100 + entry.tax_rate))
			}
			else {
				amount_excluded_tax = entry.expense_amount;
				tax_amount = (entry.expense_amount * (entry.tax_rate / 100))
			}
      total = amount_excluded_tax + tax_amount;
      frappe.model.set_value(entry.doctype, entry.name, "amount_excluded_tax", amount_excluded_tax);
      frappe.model.set_value(entry.doctype, entry.name, "tax_amount", tax_amount);
      frappe.model.set_value(entry.doctype, entry.name, "total", total);
      total_expense_amount  = grand_total+entry.expense_amount;
			total_tax_amount = total_tax_amount + entry.tax_amount;
      grand_total  = grand_total+entry.total;
		});
    frm.set_value('total_expense_amount', total_expense_amount);
    frm.set_value('total_tax_amount', total_tax_amount);
    frm.set_value('grand_total', grand_total);
		frm.refresh_fields();
	},
  edit_posting_date_and_time: function(frm) {
		if (frm.doc.edit_posting_date_and_time == 1) {
			frm.set_df_property("posting_date", "read_only", 0);
			frm.set_df_property("posting_time", "read_only", 0);
		}
		else {
			frm.set_df_property("posting_date", "read_only", 1);
			frm.set_df_property("posting_time", "read_only", 1);
		}
	},
  credit_expense: function(frm){
    console.log("credit_expense");
    frm.doc.expense_entry_details.forEach((child) =>{
      frappe.model.set_value(child.doctype, child.name, 'credit_expense', frm.doc.credit_expense );
    });
    frm.refresh_field('expense_entry_details');
  }
});

frappe.ui.form.on('Expense Entry Details',{
  expense_amount: function(frm, cdt, cdn){
    let d = locals[cdt][cdn];
    var total_expense_amount = 0
    frm.doc.expense_entry_details.forEach(function(d){
      total_expense_amount += d.expense_amount;
    })
    frm.set_value('total_expense_amount',total_expense_amount)
    update_grand_total(frm);
  },
  expense_entry_details_add: function(frm,cdt,cdn){
    let child = locals[cdt][cdn];
    frappe.model.set_value(child.doctype, child.name, 'credit_expense', frm.doc.credit_expense);
    frm.refresh_field('expense_entry_details');
  },
  expense_entry_details_remove:function(frm){
      var total_expense_amount = 0
      frm.doc.expense_entry_details.forEach(function(d){
        total_expense_amount += d.expense_amount;
      })
      frm.set_value('total_expense_amount',total_expense_amount);
      update_grand_total(frm);
    },
  tax_amount: function(frm, cdt, cdn) {
    var total_tax_amount = 0;
    frm.doc.expense_entry_details.forEach(function(d) {
      total_tax_amount += d.tax_amount;
    })
    frm.set_value('total_tax_amount', total_tax_amount);
  }
});

function update_grand_total(frm) {
  frm.trigger("make_taxes_and_totals");
  var grand_total = 0;
  if(frm.doc.rate_includes_tax){
    grand_total = frm.doc.total_expense_amount;
  }
  else {
    grand_total = frm.doc.total_expense_amount + frm.doc.total_tax_amount;
  }
  frm.set_value('grand_total', grand_total);
}
