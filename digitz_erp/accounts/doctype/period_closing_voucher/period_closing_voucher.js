// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Period Closing Voucher", {
  onload: function(frm)
  {
    console.log("onload");
    assign_defaults(frm);
  },
	refresh(frm) {
    create_custom_buttons(frm)
    frm.set_query('account', 'closing_accounts', () => {
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
          is_group :0,
          root_type: 'Liability'
      }
  }
  })
	},
  get_accounts:function(frm){

    frm.clear_table('closing_accounts')

    frappe.call({
      method: "digitz_erp.api.gl_posting_api.get_account_balances_for_period_closing",
      args: {
          to_date: frm.doc.to_date
      },
      callback: function(response) {

        total_debit = 0
        total_credit = 0

        response.message.forEach(function(account_data)
        {
          var period_closing_account = frappe.model.get_new_doc('Period Closing Voucher Account');

          console.log("account_data")
          console.log(account_data)

          period_closing_account.account = account_data.name

          if(account_data.balance>0)
          {
            // For debit balance need to fill credit
            period_closing_account.credit_amount = account_data.balance
            total_credit = total_credit + account_data.balance

          }
          else
          {
            period_closing_account.debit_amount = account_data.balance * -1
            total_debit = total_debit + (account_data.balance * -1)
          }

          frm.add_child('closing_accounts', period_closing_account);

        })

        frm.doc.total_debit = total_debit
        frm.doc.total_credit = total_credit

        if(total_debit> total_credit)
        {
          frm.doc.amount = Math.round(total_debit,3) - Math.round(total_credit,3)
          frm.doc.amount_dr_cr = "Cr"
          frm.doc.total_credit = total_debit
        }
        else
        {
          frm.doc.amount = total_credit - total_debit
          frm.doc.amount_dr_cr = "Dr"
          frm.doc.total_debit = total_credit
        }

        frm.refresh_field('total_debit')
        frm.refresh_field('total_credit')
        frm.refresh_field('amount')
        frm.refresh_field('amount_dr_cr')
        frm.refresh_field('closing_accounts')

      }
  });
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

let create_custom_buttons = function(frm){
	if (frappe.user.has_role('Management')) {
		if(!frm.is_new() && (frm.doc.docstatus == 1)){
		frm.add_custom_button('General Ledgers',() =>{
				general_ledgers(frm)
		}, 'Postings');			
		}
	}
}

let general_ledgers = function (frm) {
    frappe.call({
        method: "digitz_erp.api.accounts_api.get_gl_postings",
        args: {
			voucher:frm.doc.doctype,
            voucher_no: frm.doc.name
        },
        callback: function (response) {
            let gl_postings = response.message;

            // Generate HTML content for the popup
            let htmlContent = '<div style="max-height: 400px; overflow-y: auto;">' +
                              '<table class="table table-bordered" style="width: 100%;">' +
                              '<thead>' +
                              '<tr>' +
                              '<th style="width: 20%;">Account</th>' +
                              '<th style="width: 15%;">Debit Amount</th>' +
                              '<th style="width: 15%;">Credit Amount</th>' +
                              '<th style="width: 25%;">Against Account</th>' +
                              '<th style="width: 25%;">Remarks</th>' +
                              '</tr>' +
                              '</thead>' +
                              '<tbody>';

							  gl_postings.forEach(function (gl_posting) {
								// Handling null values for remarks
								let remarksText = gl_posting.remarks || '';  // Replace '' with a default text if you want to show something other than an empty string
							
								// Ensure debit_amount and credit_amount are treated as floats and format them
								let debitAmount = parseFloat(gl_posting.debit_amount).toFixed(2);
								let creditAmount = parseFloat(gl_posting.credit_amount).toFixed(2);
							
								htmlContent += '<tr>' +
											   `<td>${gl_posting.account}</td>` +
											   `<td style="text-align: right;">${debitAmount}</td>` +
											   `<td style="text-align: right;">${creditAmount}</td>` +
											   `<td>${gl_posting.against_account}</td>` +
											   `<td>${remarksText}</td>` +
											   '</tr>';
							});

            htmlContent += '</tbody></table></div>';

            // Create and show the dialog
            let d = new frappe.ui.Dialog({
                title: 'General Ledgers',
                fields: [{
                    fieldtype: 'HTML',
                    fieldname: 'general_ledgers_html',
                    options: htmlContent
                }],
                primary_action_label: 'Close',
                primary_action: function () {
                    d.hide();
                }
            });

            // Set custom width for the dialog
            d.$wrapper.find('.modal-dialog').css('max-width', '90%'); // or any specific width like 800px

            d.show();
        }
    });
};

