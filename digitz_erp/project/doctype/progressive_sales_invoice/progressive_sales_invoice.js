// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Progressive Sales Invoice", {
	setup(frm) {
       
	},
	refresh(frm)
	{
		if(!frm.is_new())
			{
			update_total_big_display(frm);
			}

			if (frappe.user.has_role('Management')) {
				if(!frm.is_new() && (frm.doc.docstatus == 1)){
				frm.add_custom_button('General Ledgers',() =>{
						general_ledgers(frm)
				}, 'Postings');
					
				}
			}
	},
    progress_entry(frm){
        frappe.call({
            method:"frappe.client.get",
            args:{
                doctype: "Progress Entry",
                name: frm.doc.progress_entry,
            },
            callback: function(response) {
                let progress_entry = response.message;
                if(progress_entry){
                    // console.log(progress_entry.progress_entry_items);
                    progress_entry.progress_entry_items.forEach(element => {
                        let row = {
                            "prev_completion": element.prev_completion,
                            "total_completion": element.total_completion,
                            "current_completion": element.current_completion,
                            "total_net_amount": element.total_net_amount,
                            "prev_net_amount": element.prev_net_amount,
							"total_gross_amount": element.total_gross_amount,
                            "prev_gross_amount": element.prev_gross_amount,
                            "tax": element.tax,
                            "tax_rate": element.tax_rate,
                            "tax_amount": element.tax_amount,
                            "gross_amount": element.gross_amount,
                            "net_amount": element.net_amount,
                            "sales_order_amt": element.sales_order_amt,
                            "item": element.item,
                            "item_name": element.item_name,
                            "item_gross_amount": element.item_gross_amount,
                            "item_tax_amount": element.item_tax_amount,
                            "item_net_amount": element.item_net_amount
                        };
                        frm.add_child('progress_entry_items', row);
                        frm.refresh_fields('progress_entry_items');
                    });

					progress_entry.print_details.forEach(element =>{

						let print_row = {

							"detail": element.detail,
							"total": element.total,
							"previous": element.previous,
							"current":element.current
						}

						frm.add_child('print_details',print_row)
						frm.refresh_fields("print_details")
					});

					

					frm.set_value('gross_total_before_addition', progress_entry.gross_total_before_addition);
					frm.set_value('gross_for_addition', progress_entry.gross_for_addition);
					frm.set_value('gross_total_for_removed_items', progress_entry.gross_total_for_removed_items);
					frm.set_value('net_total_for_removed_items', progress_entry.net_total_for_removed_items);					

					frm.set_value('project_retention_amount', progress_entry.project_retention_amount);
					frm.set_value('project_advance_amount', progress_entry.project_advance_amount);
					frm.set_value('project_advance_percentage', progress_entry.project_advance_percentage);

                    frm.set_value('total_completion_percentage', progress_entry.total_completion_percentage);
					frm.set_value('previous_completion_percentage', progress_entry.previous_completion_percentage);
					frm.set_value('retention_percentage', progress_entry.retention_percentage);
					frm.set_value('deduction_for_retention', progress_entry.deduction_for_retention);
					frm.set_value('deduction_against_advance', progress_entry.deduction_against_advance);

                    frm.set_value('gross_total', progress_entry.gross_total);
                    frm.set_value('tax_total', progress_entry.tax_total);
					frm.set_value('taxable_amount', progress_entry.taxable_amount);
                    frm.set_value('net_total', progress_entry.net_total);
					frm.set_value('in_words', progress_entry.in_words);

					frm.set_value('round_off', progress_entry.round_off);
                    frm.set_value('rounded_total', progress_entry.rounded_total);
                    update_total_big_display(frm);
                }
            }
        })
    },
    get_default_company_and_warehouse(frm) {

		var default_company = ""

		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				'doctype': 'Global Settings',
				'fieldname': 'default_company'
			},
			callback: (r) => {

				default_company = r.message.default_company
				
                frm.set_value("company",default_company)
				
				frappe.call(
                {
                    method: 'frappe.client.get_value',
                    args: {
                        'doctype': 'Company',
                        'filters': { 'company_name': default_company },
                        'fieldname': ['default_income_account','retention_receivable_account']
                    },
                    callback: (r2) => {
                        frm.doc.revenue_account = r2.message.default_income_account
						frm.doc.retention_receivable_account = r2.message.retention_receivable_account

                        console.log(r2)

                    }
                }
				)
			}
		})

	},
    credit_sale(frm) {

		set_default_payment_mode(frm);

		fill_receipt_schedule(frm,refresh= true)
	},
    assign_defaults(frm)
	{
		if(frm.is_new())
		{
			frm.trigger("get_default_company_and_warehouse");

			// frappe.db.get_value('Company', frm.doc.company, 'default_credit_sale',"project_advance_received_account", function(r) {
			// 	if (r && r.default_credit_sale === 1) {
			// 			frm.set_value('credit_sale', 1);
			// 	}
			// });

			frappe.db.get_value('Company', frm.doc.company, 'default_credit_sale', function(r) {
				if (r && r.default_credit_sale === 1) {
						frm.set_value('credit_sale', 1);
				}
				});

			set_default_payment_mode(frm);
		}

	},
	
});

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

frappe.ui.form.on("Progressive Sales Invoice", "onload", function (frm) {

	frm.trigger("assign_defaults")
	fill_receipt_schedule(frm);

});

function set_default_payment_mode(frm)
{
	if(frm.doc.credit_sale == 0){
        frappe.db.get_value('Company', frm.doc.company,'default_payment_mode_for_sales', function(r){

			if (r && r.default_payment_mode_for_sales) {
							frm.set_value('payment_mode', r.default_payment_mode_for_sales);
			} else {
							frappe.msgprint('Default payment mode for purchase not found.');
			}
		});
    }
	else{

		frm.set_value('payment_mode', '');
	}

	frm.set_df_property("credit_days", "hidden", !frm.doc.credit_sale);
	frm.set_df_property("payment_mode", "hidden", frm.doc.credit_sale);
	frm.set_df_property("payment_account", "hidden", frm.doc.credit_sale);
	frm.set_df_property("payment_mode", "mandatory", !frm.doc.credit_sale);
}

function fill_receipt_schedule(frm, refresh=false,refresh_credit_days=false)
{

	if(refresh)
	{
		frm.doc.receipt_schedule = [];
		refresh_field("receipt_schedule");
	}

	console.log("fill_receipt_schedule")
	console.log(frm.doc.credit_sale)

	if (frm.doc.credit_sale) {

		console.log("credit sale")
		console.log(frm.doc.rounded_total)

		var postingDate = frm.doc.posting_date;
		var creditDays = frm.doc.credit_days;
		
		if (!frm.doc.receipt_schedule) {
			frm.doc.receipt_schedule = [];
		}

		var receiptRow = null;

		row_count = 0;
		// Check if a Payment Schedule row already exists
		frm.doc.receipt_schedule.forEach(function(row) {
			if (row){
				receiptRow = row;
				if(refresh || refresh_credit_days)
				{
					receiptRow.date = creditDays ? frappe.datetime.add_days(postingDate, creditDays) : postingDate;
				}

				row_count++;

			}
		});

		//If there is no row exits create one with the relevant values
		if (!receiptRow) {
			// Calculate receipt schedule and add a new row
			receiptRow = frappe.model.add_child(frm.doc, "Receipt Schedule", "receipt_schedule");
			receiptRow.date = creditDays ? frappe.datetime.add_days(postingDate, creditDays) : postingDate;
			receiptRow.payment_mode = "Cash"
			receiptRow.amount = frm.doc.rounded_total;
			refresh_field("receipt_schedule");
			console.log("here 1")
		}
		else if (row_count==1)
		{
			//If there is only one row update the amount. If there is more than one row that means there is manual
			//entry and	user need to manage it by themself
			receiptRow.payment_mode = "Cash"
			receiptRow.amount = frm.doc.rounded_total;
			refresh_field("receipt_schedule");
			console.log("here 2")
		}

		//Update date based on credit_days if there is a credit days change or change in the credit_sales checkbox
		if(refresh || refresh_credit_days)
			receiptRow.date = creditDays ? frappe.datetime.add_days(postingDate, creditDays) : postingDate;
			refresh_field("receipt_schedule");
	}
	else
	{
		frm.doc.receipt_schedule = [];
		refresh_field("receipt_schedule");
	}
}


function update_total_big_display(frm) {

	let netTotal = isNaN(frm.doc.rounded_total) ? 0 : parseFloat(frm.doc.rounded_total).toFixed(2);

    // Add 'AED' prefix and format net_total for display

	let displayHtml = `<div style="font-size: 25px; text-align: right; color: black;">AED ${netTotal}</div>`;


    // Directly update the HTML content of the 'total_big' field
    frm.fields_dict['total_big'].$wrapper.html(displayHtml);

}
