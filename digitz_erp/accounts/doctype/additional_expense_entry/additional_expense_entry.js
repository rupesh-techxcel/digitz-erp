// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Additional Expense Entry", {
	refresh(frm) {

    frm.fields_dict['additional_expense_purchases'].grid.get_field('purchase_invoice').get_query = function(doc, cdt, cdn) {
      return {
          filters: {
              supplier: frm.supplier  // Set filters to only show accounts where is_group is false
          }
      };
  };
  },
  onload: function(frm)
  {
    assign_defaults(frm);
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
  validate: function (frm) {

		if(!frm.doc.credit_expense && !frm.doc.payment_mode)
		{
			frappe.throw("Select payment mode.")
		}

		if(!frm.doc.credit_expense && !frm.doc.payment_account)
		{			
			frappe.throw("Select payment account.")
		}

		if(frm.doc.expense_against == "Purchase" && !frm.doc.additional_expense_purchases)
		{
			frappe.throw("Select purchase against the expenses.")
		}

	},

	get_purchase_items: function(frm){

		console.log("from get_purchase_items")
		
		var selectedInvoices = frm.doc.additional_expense_purchases.map(row => row.purchase_invoice);

		let total_purchases = frm.doc.total_purchases
		let total_allocation_amount = 0

		frappe.call({
        method: "digitz_erp.api.additional_expense_entry_api.get_purchase_invoice_items",
        args: {
            selected_invoices: selectedInvoices
        },
        callback: function(response) {
            if (response.message) {
                frm.clear_table('purchase_items');
                response.message.forEach(function(item) {
                    var row = frappe.model.add_child(frm.doc, 'purchase_items', 'purchase_items');
                    row.item_code = item.item;
                    row.item_name = item.item_name,
                    row.qty = item.qty;
                    row.purchase_invoice = item.parent;
					row.net_amount = item.net_amount
                    row.gross_amount = item.gross_amount;
					row.reference_document_no = item.name
					
					item_share = (row.gross_amount / total_purchases) * 100

					console.log("item_share")
					console.log(item_share)
					
					allocation_amount = 0
					console.log("frm.doc.total_expense_amount")
					console.log(frm.doc.total_expense_amount)

					if(frm.doc.total_expense_amount && item_share > 0)
						allocation_amount  = (frm.doc.total_expense_amount * item_share) / 100
						console.log(allocation_amount)
						row.allocation_amount = allocation_amount
						total_allocation_amount = total_allocation_amount + allocation_amount

                });				

				frm.doc.total_allocation_amount = total_allocation_amount;
				frm.refresh_field("total_allocation_amount")
                frm.refresh_field('purchase_items');				
            }
        }
    });
	},	
	update_purchases_total_and_items:function(frm){

		console.log("frm.doc.additional_expense_purchases")
		console.log(frm.doc.additional_expense_purchases)
		total_purchases = 0
		frm.doc.additional_expense_purchases.forEach(function(purchaseRow)
		{
			total_purchases = total_purchases + purchaseRow.gross_total 
		});

		frm.doc.total_purchases = total_purchases
		refresh_field("total_purchases")
		frm.trigger("get_purchase_items")
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
			  total_expense_amount  = total_expense_amount + entry.amount;
			  total_tax_amount = total_tax_amount + entry.tax_amount;
			  grand_total  = grand_total+entry.total;
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
	total_expense_amount:function(frm){

		frm.trigger("update_purchases_total_and_items")
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

    frappe.call(
        {
          method:'digitz_erp.api.settings_api.get_default_payable_account',
          async:false,
          callback(r){								
            frm.set_value('default_payable_account',r.message);
          }
        }
      );
 }

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

		if (! row.payable_account)
		{
			row.payable_account = frm.doc.default_payable_account
		}
		
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
		
		if (! row.payable_account)
		{
			row.payable_account = frm.doc.default_payable_account
		}

		frm.refresh_field("expense_entry_details");
	},  
	expense_entry_details_add: function(frm,cdt,cdn){
		console.log("expense entry add")

		let row = frappe.get_doc(cdt, cdn); 
		row.payable_account = frm.doc.default_payable_account
		frm.refresh_field("expense_entry_details");		
	},
	expense_entry_details_remove:function(frm){
		frm.trigger("update_purchases_total_and_items")
		frm.trigger("make_taxes_and_totals");
	},
	tax_amount: function(frm, cdt, cdn) {

		frm.trigger("make_taxes_and_totals");    
	}
  
	});

  frappe.ui.form.on('Additional Expense Entry Purchase', {

    supplier:function(frm,cdt,cdn){

      let row = frappe.get_doc(cdt, cdn);
      frm.supplier = row.supplier

    },    
    purchase_invoice: function(frm,cdt,cdn)
    {
      
      let row = frappe.get_doc(cdt, cdn);
	  console.log(row)
	 
	  frappe.call({
		method: "digitz_erp.api.additional_expense_entry_api.get_purchase_invoice",
		args: {
				name: row.purchase_invoice
		},
		callback: function(response) {

			console.log("response")
			console.log(response)
			console.log(response.message.rounded_total)

			if (response.message) {					
				row.gross_total = response.message.gross_total
				row.grand = response.message.rounded_total
				
				frm.refresh_fields('additional_expense_purchases')
				frm.trigger("update_purchases_total_and_items")
			}
		}	
		
		
		});
      
    },	
	additional_expense_purchases_remove: function(frm,cdt,cdn){

		frm.trigger("update_purchases_total_and_items");
	}



  });

  frappe.ui.form.on('Additional Expense Entry Sales', {

    customer:function(frm,cdt,cdn){

      let row = frappe.get_doc(cdt, cdn);
      frm.customer = row.customer

    },    
    sales_invoice: function(frm,cdt,cdn)
    {
     
      let row = frappe.get_doc(cdt, cdn);
	  console.log(row)
	 
	  frappe.call({
		method: "digitz_erp.api.additional_expense_entry_api.get_sales_invoice",
		args: {
				name: row.sales_invoice
		},
		callback: function(response) {

			console.log("response")
			console.log(response)
			console.log(response.message.rounded_total)

			if (response.message) {
					
				row.grand_total = response.message.rounded_total
				console.log("row.grand_total")
				console.log(row.grand_total)
				frm.refresh_fields('additional_expense_sales')
			}
		}	
		
		
	});

	
      
    }


  });

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
