// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee", {
  onload(frm) {
    assign_defaults(frm);
  },
  });

  function assign_defaults(frm)
  {
  if(frm.is_new())
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
  }
