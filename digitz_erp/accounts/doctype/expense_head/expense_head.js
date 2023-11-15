// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Expense Head', {

  onload: function(frm)
  {
    frm.trigger("assign_default_tax");
  },
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
        frm.set_value('tax', '')
    }
    else
    {
      frm.trigger("assign_default_tax");
    }
  },
  assign_default_tax(frm)
  {
    frappe.call({
      method: 'frappe.client.get_value',
      args: {
        'doctype': 'Global Settings',
        'fieldname': 'default_company'
      },
      callback: (r) => {

        default_company = r.message.default_company          
        frappe.call(
          {
            method: 'frappe.client.get_value',
            args: {
              'doctype': 'Company',
              'filters': { 'company_name': default_company },
              'fieldname': ['tax','tax_excluded']
            },
            callback: (r) => {

              console.log(r)

              frm.set_value('tax', r.message.tax)
              frm.set_value('tax_excluded', r.message.tax_excluded)
            }
          });            

      }
    });
  }


});


