// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Period Closing Voucher", {
  onload: function(frm)
  {
    console.log("onload");
    assign_defaults(frm);
  },
	refresh(frm) {
    frm.set_query('account', 'period_closing_voucher_account', () => {
    return {
        filters: {
            is_group: 0,
            root_type: ['in',  ['Income', 'Expense']]
        }
    }
})
  frm.set_query('closing_account_head', () => {
  return {
      filters: {
          root_type: 'Liability'
      }
  }
  })
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
        console.log("default company")
        console.log(default_company)
      }
    });
  }

frappe.ui.form.on('Period Closing Voucher Account', {
  debit: function(frm, cdt, cdn) {
    calculate_totals(frm);
  },
  credit: function(frm, cdt, cdn) {
    calculate_totals(frm);
  },
  period_closing_voucher_account_add: function(frm, cdt, cdn) {
    calculate_totals(frm);
  },
  period_closing_voucher_account_remove: function(frm, cdt, cdn) {
    calculate_totals(frm);
  },
  account:function(frm, cdt, cdn) {
    var d = locals[cdt][cdn];
    if (d.account) {
        frappe.call({
            method: "digitz_erp.accounts.doctype.period_closing_voucher.period_closing_voucher.get_account_balance",
            args: {
                account: d.account
            },
            callback: function(r) {
                if (r.message) {
                    var account_balance = r.message;

                    if (account_balance < 0) {
                        frappe.model.set_value(cdt, cdn, "credit", 0);
                        frappe.model.set_value(cdt, cdn, "debit", Math.abs(account_balance));
                    } else {
                        frappe.model.set_value(cdt, cdn, "debit", 0);
                        frappe.model.set_value(cdt, cdn, "credit", Math.abs(account_balance));
                    }
                }
            }
        });
    }
}

});

let calculate_totals = function(frm){
  let total_debit = 0;
  let total_credit = 0;
  let amount = 0;
  frm.doc.period_closing_voucher_account.forEach(function(d) {
    if(d.debit){
      total_debit += d.debit;
    }
    if(d.credit){
      total_credit += d.credit;
    }
  });
  if (total_debit > total_credit) {
    amount = total_debit - total_credit;
    amount_dr_cr = "Cr";
  } else if (total_credit > total_debit) {
    amount = total_credit - total_debit;
    amount_dr_cr = "Dr";
  }
  frm.set_value('total_debit', total_debit);
  frm.set_value('total_credit', total_credit);
  frm.set_value('amount', amount);
  frm.set_value('amount_dr_cr', amount_dr_cr);
  frm.refresh_fields();
}
