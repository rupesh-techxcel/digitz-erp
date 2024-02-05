// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.
frappe.ui.form.on('Expense Entry', {

  onload: function(frm)
  {
    assign_defaults(frm);
    fill_payment_schedule(frm);
  },

  refresh: function(frm) {
    frm.set_query('expense_account', 'expense_entry_details', () => {
      return {
        filters: {
          root_type: "Expense",
          is_group: 0
        }
      }
    })

    frm.set_query('payable_account', 'expense_entry_details', () => {
      return {
        filters: {
          root_type: "Liability",
          is_group: 0
        }
      }
    })
	},
  rate_includes_tax: function(frm) {
      frappe.confirm('Are you sure you want to change this setting which will change the tax calculation in the expense entry ?', () => {
      frm.trigger("make_taxes_and_totals");
    })
	},
  validate: function (frm) {

		if(!frm.doc.credit_expense && !frm.doc.payment_mode)
		{
			frappe.throw("Select payment mode.")
		}

		if(!frm.doc.credit_expense && !frm.doc.payment_account)
		{			
			frappe.throw("Select payment account.")
		}
	},
  make_taxes_and_totals: function(frm) {

    console.log("from make_tax_and_totals")
		var total_expense_amount = 0;
		var total_tax_amount = 0;
    var grand_total = 0;
		frm.doc.total_expense_amount = 0;
		frm.doc.total_tax_amount = 0;
		frm.doc.grand_total = 0;
		frm.doc.expense_entry_details.forEach(function (entry) {

        if(entry.expense_head && entry.supplier && entry.expense_account)
        {
          var tax_in_rate = 0;
          var amount_excluded_tax = 0;
          var tax_amount = 0;
          var total = 0;
          entry.rate_includes_tax = frm.doc.rate_includes_tax;
          if (entry.rate_includes_tax)
          {
            tax_in_rate = entry.amount * (entry.tax_rate / (100 + entry.tax_rate));
            amount_excluded_tax = entry.amount - tax_in_rate;
            tax_amount = entry.amount * (entry.tax_rate / (100 + entry.tax_rate))
          }
          else {
            amount_excluded_tax = entry.amount;
            tax_amount = (entry.amount * (entry.tax_rate / 100))
          }

          total = amount_excluded_tax + tax_amount;

          frappe.model.set_value(entry.doctype, entry.name, "amount_excluded_tax", amount_excluded_tax);
          frappe.model.set_value(entry.doctype, entry.name, "tax_amount", tax_amount);
          frappe.model.set_value(entry.doctype, entry.name, "total", total);
          
          total_expense_amount  = total_expense_amount+ entry.amount;
          
          console.log("entry.amount")
          console.log(entry.amount)
          console.log("total_expense_amount")
          console.log(total_expense_amount)

          total_tax_amount = total_tax_amount + entry.tax_amount;
          grand_total  = grand_total+ entry.total;
        }       
		});

    frm.refresh_field("expense_entry_details");

    frm.set_value('total_expense_amount', total_expense_amount);
    frm.set_value('total_tax_amount', total_tax_amount);
    frm.set_value('grand_total', grand_total);
		frm.refresh_field("total_expense_amount");
    frm.refresh_field("total_tax_amount");
    frm.refresh_field("grand_total");

    fill_payment_schedule(frm);

	},
  edit_posting_date_and_time: function(frm) {
		if (frm.doc.edit_posting_date_and_time == 1) {
			frm.set_df_property("posting_date", "read_only", 0);
			frm.set_df_property("posting_time", "read_only", 0);
		}
		else {
			frm.set_df_property("posting_date", "read_only", 1);
			frm.set_df_property("posting_time", "read_only", 1);
		}
	},
  credit_expense: function(frm){

    fill_payment_schedule(frm)
  },
  credit_days(frm)
  {
    fill_payment_schedule(frm)
  },  

});

frappe.ui.form.on('Expense Entry Details',{

  amount: function(frm, cdt, cdn){

    console.log("amount")
    frm.trigger("make_taxes_and_totals");

  },
  tax: function(frm,cdt,cdn)
  {

    // frm.trigger("make_taxes_and_totals");

  },
  tax_excluded:function(frm,cdt,cdn)
  {
    let row = frappe.get_doc(cdt, cdn);

    if(row.tax_excluded)
    {
      console.log("tax excluded = true")
      row.tax = "";
      row.tax_rate = 0;

      frm.trigger("make_taxes_and_totals");

      frm.refresh_field("expense_entry_details");
    }
    else
    {

      console.log("tax excluded = false")

      let row = frappe.get_doc(cdt, cdn);    
      
      frappe.call(
          {
            method: 'frappe.client.get_value',
            args: {
              'doctype': 'Expense Head',
              'filters': { 'name': row.expense_head },
              'fieldname': ['tax', 'tax_rate']
            },
            callback: (r) => {
              
              console.log("r.message.tax")
              console.log(r.message.tax)

              row.tax = r.message.tax;
              row.tax_rate = r.message.tax_rate;

              frm.trigger("make_taxes_and_totals");
              frm.refresh_field("expense_entry_details");

            }
          }
        );
    }
    
  },
  expense_head(frm,cdt,cdn)
  {
    console.log("expense_head")

    let row = frappe.get_doc(cdt, cdn);
    frm.expense_head = row.expense_head
    
    frappe.call(
			{
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Expense Head',
					'filters': { 'name': row.expense_head },
					'fieldname': ['tax', 'tax_excluded','expense_account']
				},
        callback: (r) => {
          row.expense_account = r.message.expense_account
          row.tax = r.message.tax,
          row.tax_excluded = r.message.tax_excluded          
        }
      }
      );

      frm.refresh_field("expense_entry_details");
  },
  supplier(frm,cdt,cdn)
  {
    let row = frappe.get_doc(cdt, cdn);    
    frappe.call(
			{
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Supplier',
					'filters': { 'name': row.supplier },
					'fieldname': ['credit_days']
				},
				callback: (r) => {

          console.log(r)

          row.credit_days = r.message.credit_days
          console.log(r.message.credit_days)
          frm.refresh_field("expense_entry_details");
        }
      });
  },  
  expense_entry_details_add: function(frm,cdt,cdn){

    let row = frappe.get_doc(cdt, cdn); 
    row.payable_account = frm.doc.default_payable_account
    frm.refresh_field("expense_entry_details");
    
  },
  expense_entry_details_remove:function(frm){
     
    frm.trigger("make_taxes_and_totals");
  },
  tax_amount: function(frm, cdt, cdn) {

    frm.trigger("make_taxes_and_totals");    
  }

});

function update_grand_total(frm) {
  
  var grand_total = 0;
  if(frm.doc.rate_includes_tax){
    grand_total = frm.doc.total_expense_amount;
  }
  else {
    grand_total = frm.doc.total_expense_amount + frm.doc.total_tax_amount;
  }
  frm.set_value('grand_total', grand_total);
}

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
      }
    });

    frappe.call(
      {
        method:'digitz_erp.api.settings_api.get_default_payable_account',
        async:false,
        callback(r){								
          frm.set_value('default_payable_account',r.message);
        }
      }
    );

    // frm.set_value('credit_expense', true);

  frm.refresh_fields();

  }

  function fill_payment_schedule(frm)
  {
    
    frm.doc.payment_schedule = [];

    refresh_field("payment_schedule");    
  
    if(frm.doc.credit_expense && frm.doc.expense_entry_details)
    {
        frm.doc.expense_entry_details.forEach(function(expenseRow)
        { 
            if(expenseRow)
            {        
              console.log("expenseRow")
              console.log(expenseRow)
              
              var date = expenseRow.credit_days ? frappe.datetime.add_days(expenseRow.expense_date, expenseRow.credit_days) : expenseRow.expense_date;	

              var rowFound = false
              frm.doc.payment_schedule.forEach(function(row) {
                if (row){
                  if(row.supplier == expenseRow.supplier && row.date == date)
                  {
                    rowFound = true
                    row.amount = row.amount + expenseRow.total
                  }
                }        
              });
              
              if(!rowFound)
              {          
                paymentRow = frappe.model.add_child(frm.doc, "Payment Schedule", "payment_schedule");
                paymentRow.supplier = expenseRow.supplier
                paymentRow.date = date
                paymentRow.payment_mode = "Cash"
                paymentRow.amount = expenseRow.total
              }
          }       
        });

        refresh_field("payment_schedule");
    }      
    else
    {
      frm.doc.payment_schedule = [];
      refresh_field("payment_schedule");
    }
  }

