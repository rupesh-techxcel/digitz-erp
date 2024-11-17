// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Expense Head', {
	refresh: function(frm) {
    frm.set_query('expense_account', function () {
      if (frm.doc.expense_type === 'Expense') {
          return {
              filters: {
                  root_type: 'Expense'
              }
          };
      } else if (frm.doc.expense_type === 'Work In Progress') {
          return {
              filters: {
                  account_type: 'Work In Progress'
              }
          };
      }
    });
	},
	tax_excluded: function(frm) {
			if (frm.doc.tax_excluded == 1) {
					frm.set_value('tax_rate', 0);
			}
	},
  expense_type: function (frm) {
    
}

});
