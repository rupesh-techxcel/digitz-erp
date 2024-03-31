// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt
frappe.ui.form.on('Journal Entry', {
  refresh: function(frm) {
    create_custom_buttons(frm)
    
	},
  setup: function(frm){

    frm.set_query('account', 'journal_entry_details', () => {
      return {
          filters: {
              is_group: 0
          }
      }
    });
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
  validate(frm){

    let total_debit = 0
    let total_credit = 0
    frm.doc.journal_entry_details.forEach(function(d) {
      if(d.debit){
        total_debit += d.debit;
      }
      if(d.credit){
        total_credit += d.credit;
      }
    });

    if(total_debit != total_credit)
      frappe.throw("Debit and credit amounts should be in equilibrium.")


  }

});

frappe.ui.form.on('Journal Entry Detail', {
  account(frm, cdt, cdn){
    var child = locals[cdt][cdn];
    if (frm.doc.default_cost_center) {
      frappe.model.set_value(cdt, cdn, 'cost_center', frm.doc.default_cost_center);
    }
  },

  debit: function(frm, cdt, cdn) {
    calculate_totals(frm);
  },
  credit: function(frm, cdt, cdn) {
    calculate_totals(frm);
  },
  journal_entry_details_add: function(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    calculate_totals(frm);
    if(frm.total_debit>frm.total_credit)
        row.credit = frm.total_debit - frm.total_credit
        frm.refresh_fields()

    if(frm.total_credit > frm.total_debit)
        row.debit = frm.total_credit - frm.total_debit
        frm.refresh_fields()

    calculate_totals(frm);


  },
  journal_entry_details_remove: function(frm, cdt, cdn) {
    calculate_totals(frm);
  }

});

let calculate_totals = function(frm){
  let total_debit = 0;
  let total_credit = 0;
  let total_balance = 0;
  let total_balance_with_sign = 0
  frm.doc.journal_entry_details.forEach(function(d) {
    if(d.debit){
      total_debit += d.debit;
    }
    if(d.credit){
      total_credit += d.credit;
    }
  });

  frm.total_debit = total_debit
  frm.total_credit = total_credit

  if(total_debit > total_credit)
    total_balance = total_debit - total_credit
    frm.set_value('balance', total_balance + ' Dr')
    console.log(total_balance)


  if (total_credit> total_debit)
    total_balance = total_credit - total_debit
    frm.set_value('balance', total_balance + ' Cr')
    console.log(total_balance)


  frm.set_value('total_debit', total_debit);
  frm.set_value('total_credit', total_credit);
  frm.refresh_fields();
}

