// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Additional Expense Voucher", {
	refresh(frm) {
  },
  onload: function(frm)
  {
    assign_defaults(frm);
  },
  is_sales: function(frm){
    if (cur_frm.doc.is_sales == 1) {
      cur_frm.set_df_property('additional_cost_purchase', 'hidden', 1);
    }
    else
    {
      cur_frm.set_df_property('additional_cost_purchase', 'hidden', 0);
    }

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
