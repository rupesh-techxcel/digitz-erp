// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt
frappe.ui.form.on('Contra Voucher', {
    refresh: function(frm) {
      create_custom_buttons(frm)
      frm.set_query('account', 'contra_voucher_details', () => {
      return {
          filters: {
              is_group: 0,
              account_type: ['in', ['Cash', 'Bank']]
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
      },
    validate(frm){

      let total_debit = 0
      let total_credit = 0
      frm.doc.contra_voucher_details.forEach(function(d) {
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

  frappe.ui.form.on('Contra Voucher Detail', {

    debit: function(frm, cdt, cdn) {
      calculate_totals(frm);
    },
    credit: function(frm, cdt, cdn) {
      calculate_totals(frm);
    },
    contra_voucher_details_add: function(frm, cdt, cdn) {
      var child = locals[cdt][cdn];
      if (frm.doc.default_cost_center) {
        frappe.model.set_value(cdt, cdn, 'cost_center', frm.doc.default_cost_center);
      }

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
    contra_voucher_details_remove: function(frm, cdt, cdn) {
      calculate_totals(frm);
    }

  });

  let calculate_totals = function(frm){
    let total_debit = 0;
    let total_credit = 0;
    let total_balance = 0;
    let total_balance_with_sign = 0
    frm.doc.contra_voucher_details.forEach(function(d) {
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
        voucher: frm.doc.doctype,
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
              d.$wrapper.find('.modal-dialog').css('max-width', '72%'); // or any specific width like 800px
  
              d.show();
          }
      });
  };
  
  