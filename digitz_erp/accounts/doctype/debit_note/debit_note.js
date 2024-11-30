// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Debit Note", {

	onload(frm) {
		frm.trigger("assign_defaults");
	},
	refresh(frm){
		create_custom_buttons(frm)

	},
	setup: function(frm)
	{

		frm.set_query('account', 'debit_note_details', () => {
			return {
				filters: {
				root_type: ['in',  ['Expense','Income','Liability','Asset']],
				is_group: 0
				}
			}
			});

			frm.set_query("warehouse", function() {
				return {
					"filters": {
						"disabled": 0
					}
				};
			});

			frm.set_query('payable_account', () => {
				return {
					filters: {
					root_type: ['in',  ['Liability','Asset']],
					is_group: 0
					}
				}
				});
	},
	assign_defaults: function(frm){

		if(frm.is_new())
		{

			default_company = "";

			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Global Settings'	,
					'fieldname': 'default_company'
				},
				callback: (r) => {

					default_company = r.message.default_company
					frm.set_value('company',default_company);

					frappe.db.get_value("Company", default_company, "default_payable_account").then((r) => {

						frm.set_value('payable_account',r.message.default_payable_account);
					});
				}
			});

			frappe.db.get_value('Company', frm.doc.company, 'default_credit_purchase', function(r) {
				if (r && r.default_credit_purchase === 1) {
						frm.set_value('on_credit', 1);
				}
			});

			set_default_payment_mode(frm);

			frm.clear_table("debit_note_details");
		}
	},
	rate_includes_tax: function(frm) {
		frappe.confirm("Updating this will modify the 'rate includes tax' information in the details section and related calculations. Are you sure you want to proceed?", () => {

			frm.doc.debit_note_details.forEach(function (entry) {
				entry.rate_includes_tax = frm.doc.rate_includes_tax
			})


			frm.trigger("make_taxes_and_totals");
		})
	},
	make_taxes_and_totals: function(frm) {
		var total_amount = 0;
		var tax_total = 0;
		var grand_total = 0;
		frm.doc.total_amount = 0;
		frm.doc.tax_total = 0;
		frm.doc.grand_total = 0;

		frm.doc.debit_note_details.forEach(function (entry) {

			var tax_in_rate = 0;
			var amount_excluded_tax = entry.amount;
			var tax_amount = 0;
			var total = 0;

			if(!entry.tax_excluded && entry.tax_rate>0)
			{
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
			}

			total = amount_excluded_tax + tax_amount;
			frappe.model.set_value(entry.doctype, entry.name, "amount_excluded_tax", amount_excluded_tax);
			frappe.model.set_value(entry.doctype, entry.name, "tax_amount", tax_amount);
			frappe.model.set_value(entry.doctype, entry.name, "total", total);
			total_amount  = grand_total+entry.amount;
			tax_total = tax_total + entry.tax_amount;
			grand_total  = grand_total+entry.total;
		});

		frm.set_value('total_amount', total_amount);
		frm.set_value('tax_total', tax_total);
		frm.set_value('grand_total', grand_total);
		fill_payment_schedule(frm);
		frm.refresh_fields();
	},
	setup(frm){
		frm.add_fetch('supplier', 'tax_id', 'tax_id')
		frm.add_fetch('supplier', 'full_address', 'supplier_address')
		frm.add_fetch('company', 'default_warehouse', 'warehouse')
		frm.add_fetch('payment_mode', 'account', 'payment_account')
	},
	supplier(frm){
			frappe.call(
			{
				method: 'digitz_erp.api.accounts_api.get_supplier_balance',
				args: {
					'supplier': frm.doc.supplier
				},
				callback: (r) => {
					frm.set_value('supplier_balance',r.message[0].supplier_balance)
					frm.refresh_field("supplier_balance");
				}
			});
	},

  edit_posting_date_and_time: function(frm) {
		if (frm.doc.edit_posting_date_and_time == 1) {
			frm.set_df_property("date", "read_only", 0);
			frm.set_df_property("posting_time", "read_only", 0);
		}
		else {
			frm.set_df_property("date", "read_only", 1);
			frm.set_df_property("posting_time", "read_only", 1);
		}
	},
	on_credit: function(frm) {
		set_default_payment_mode(frm);
		fill_payment_schedule(frm,refresh=true);

	},
	validate: function (frm) {

		if(!frm.doc.on_credit && !frm.doc.payment_mode)
		{
			frappe.throw("Select payment mode.")
		}

		if(!frm.doc.on_credit && !frm.doc.payment_account)
		{
			frm.refresh_field("payment_account");
			frappe.throw("Select payment account.")
		}
	},
});

function set_default_payment_mode(frm)
{
	console.log("hi")
	console.log(frm .doc.company)
	if(!frm.doc.on_credit)
	{
		frappe.db.get_value('Company', frm.doc.company,'default_payment_mode_for_purchase', function(r){
			console.log("default_payment_mode_for_purchase")
			console.log(r)
			if (r && r.default_payment_mode_for_purchase) {
							frm.set_value('payment_mode', r.default_payment_mode_for_purchase);
			} else {
							frappe.msgprint('Default payment mode for purchase not found.');
			}
		});
	}
	else
	{
		frm.set_value('payment_mode', "");
	}

	frm.set_df_property("credit_days", "hidden", !frm.doc.on_credit);
	frm.set_df_property("payment_mode", "hidden", frm.doc.on_credit);
	frm.set_df_property("payment_account", "hidden", frm.doc.on_credit);

}

function fill_payment_schedule(frm, refresh=false,refresh_credit_days=false)
{
	if(refresh)
	{
		frm.doc.payment_schedule = [];
		refresh_field("payment_schedule");
	}

	if (frm.doc.on_credit) {
		var postingDate = frm.doc.date;
		var creditDays = frm.doc.credit_days;
		var roundedTotal = frm.doc.grand_total;
		console.log("roundedTotal",roundedTotal);

		if (!frm.doc.payment_schedule) {
			frm.doc.payment_schedule = [];
		}

		var paymentRow = null;

		row_count = 0;
		// Check if a Payment Schedule row already exists
		frm.doc.payment_schedule.forEach(function(row) {
			if (row){
				paymentRow = row;
				if(refresh || refresh_credit_days)
				{
					paymentRow.date = creditDays ? frappe.datetime.add_days(postingDate, creditDays) : postingDate;
				}

				row_count++;
			}
		});
		console.log("row_count")
		console.log(row_count)
		console.log("paymentRow")
		console.log(paymentRow)
		console.log("refresh_credit_days")
		console.log(refresh_credit_days)

		//If there is no row exits create one with the relevant values
		if (!paymentRow) {
			// Calculate payment schedule and add a new row
			paymentRow = frappe.model.add_child(frm.doc, "Payment Schedule", "payment_schedule");
			paymentRow.date = creditDays ? frappe.datetime.add_days(postingDate, creditDays) : postingDate;
			paymentRow.payment_mode = "Cash"
			paymentRow.amount = frm.doc.grand_total;
			refresh_field("payment_schedule");
		}
		else if (row_count==1)
		{
			//If there is only one row update the amount. If there is more than one row that means there is manual
			//entry and	user need to manage it by themself
			paymentRow.amount = frm.doc.grand_total;
			refresh_field("payment_schedule");
		}

		//Update date based on credit_days if there is a credit days change or change in the credit_purchase checkbox
		if(refresh || refresh_credit_days)
			paymentRow.date = creditDays ? frappe.datetime.add_days(postingDate, creditDays) : postingDate;
			refresh_field("payment_schedule");
	}
	else
	{
		frm.doc.payment_schedule = [];
		refresh_field("payment_schedule");
	}
}


frappe.ui.form.on('Debit Note Detail',{
	account(frm,cdt, cdn){
		var child = locals[cdt][cdn];
		if (frm.doc.default_cost_center) {
			frappe.model.set_value(cdt, cdn, 'cost_center', frm.doc.default_cost_center);
		}
	},

	tax_excluded: function(frm, cdt, cdn) {
        frm.trigger("make_taxes_and_totals");
    },
	rate_includes_tax:function(frm,cdt,cdn){
		frm.trigger("make_taxes_and_totals");
	},
	amount: function(frm, cdt, cdn){
		frm.trigger("make_taxes_and_totals");
  	},
	tax_rate: function(frm,cdt,cdn){
		frm.trigger("make_taxes_and_totals");
		fill_payment_schedule(frm);
	},
	debit_note_details_add(frm,cdt,cdn){

		let row = frappe.get_doc(cdt, cdn);

		frappe.call(
			{
				method:'digitz_erp.api.settings_api.get_default_tax',
				async:false,
				callback(r){
					row.tax = r.message

					frappe.call(
						{
						  method: 'frappe.client.get_value',
						  args: {
							'doctype': 'Tax',
							'filters': { 'tax_name': row.tax },
							'fieldname': ['tax_name', 'tax_rate']
						  },
						  callback: (r2) => {
							row.tax_rate = r2.message.tax_rate;
							frm.trigger("make_taxes_and_totals");
						  }
						});

						frm.refresh_field("debit_note_details");

				}


			}
		);

	},
	debit_note_details_remove(frm,cdt,cdn){
		frm.trigger("make_taxes_and_totals");
	}
});

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
            let gl_postings = response.message.gl_postings;
            let totalDebit = parseFloat(response.message.total_debit).toFixed(2);
            let totalCredit = parseFloat(response.message.total_credit).toFixed(2);

            // Generate HTML content for the popup
            let htmlContent = '<div style="max-height: 680px; overflow-y: auto;">' +
                              '<table class="table table-bordered" style="width: 100%;">' +
                              '<thead>' +
                              '<tr>' +
                              '<th style="width: 15%;">Account</th>' +
							  '<th style="width: 25%;">Remarks</th>' +
                              '<th style="width: 10%;">Debit Amount</th>' +
                              '<th style="width: 10%;">Credit Amount</th>' +
							  '<th style="width: 10%;">Party</th>' +
                              '<th style="width: 10%;">Against Account</th>' +                              
                              '<th style="width: 10%;">Project</th>' +
                              '<th style="width: 10%;">Cost Center</th>' +                              
                              '</tr>' +
                              '</thead>' +
                              '<tbody>';

			console.log("gl_postings",gl_postings)

            gl_postings.forEach(function (gl_posting) {
                let remarksText = gl_posting.remarks || '';
                let debitAmount = parseFloat(gl_posting.debit_amount).toFixed(2);
                let creditAmount = parseFloat(gl_posting.credit_amount).toFixed(2);

                htmlContent += '<tr>' +
                               `<td>${gl_posting.account}</td>` +
							   `<td>${remarksText}</td>` +
                               `<td style="text-align: right;">${debitAmount}</td>` +
                               `<td style="text-align: right;">${creditAmount}</td>` +
							   `<td>${gl_posting.party}</td>` +
                               `<td>${gl_posting.against_account}</td>` +                               
                               `<td>${gl_posting.project}</td>` +
                               `<td>${gl_posting.cost_center}</td>` +
                               
                               '</tr>';
            });

            // Add totals row
            htmlContent += '<tr>' +
                           '<td style="font-weight: bold;">Total</td>' +
						   '<td></td>'+
                           `<td style="text-align: right; font-weight: bold;">${totalDebit}</td>` +
                           `<td style="text-align: right; font-weight: bold;">${totalCredit}</td>` +
                           '<td colspan="5"></td>' +
                           '</tr>';

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
            d.$wrapper.find('.modal-dialog').css('max-width', '90%'); 

            d.show();
        }
    });
};
