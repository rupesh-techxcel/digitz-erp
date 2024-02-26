// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt
frappe.ui.form.on('Contra Voucher', {
    refresh: function(frm) {
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
  