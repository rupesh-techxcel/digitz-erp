// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Expense Head', {
	refresh: function(frm) {
    frm.set_query('expense_account', () => {
      return {
        filters: {
          root_type: "Expense",
          is_group: 0
        }
      }
    });
	},
	tax_excluded: function(frm) {
			if (frm.doc.tax_excluded == 1) {
					frm.set_value('tax_rate', 0);
			}
	}

});
