// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt
frappe.ui.form.on('Journal Entry', {
  refresh: function(frm) {
    frm.set_query('account', 'journal_entry_account', () => {
    return {
        filters: {
            is_group: 0
        }
    }
})
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
	}
});
frappe.ui.form.on('Journal Entry Account', {
  debit: function(frm, cdt, cdn) {
    calculate_totals(frm);
  },
  credit: function(frm, cdt, cdn) {
    calculate_totals(frm);
  },
  journal_entry_account_add: function(frm, cdt, cdn) {
    calculate_totals(frm);
  },
  journal_entry_account_remove: function(frm, cdt, cdn) {
    calculate_totals(frm);
  }
});

let calculate_totals = function(frm){
  let total_debit = 0;
  let total_credit = 0;
  frm.doc.journal_entry_account.forEach(function(d) {
    if(d.debit){
      total_debit += d.debit;
    }
    if(d.credit){
      total_credit += d.credit;
    }
  });
  frm.set_value('total_debit', total_debit);
  frm.set_value('total_credit', total_credit);
  frm.refresh_fields();
}
