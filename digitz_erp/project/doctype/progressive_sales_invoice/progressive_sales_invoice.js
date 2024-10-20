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
                            "total_amount": element.total_amount,
                            "prev_amount": element.prev_amount,
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

                    frm.set_value('total_completion_percentage', progress_entry.total_completion_percentage);
                    frm.set_value('gross_total', progress_entry.gross_total);
                    frm.set_value('tax_total', progress_entry.tax_total);
                    frm.set_value('net_total', progress_entry.net_total);

					frappe.db.get_value('Company', frm.doc.company, 'do_not_apply_round_off_in_si', function(data) {
                        console.log("Value of do_not_apply_round_off_in_si:", data.do_not_apply_round_off_in_si);
                        if (data && data.do_not_apply_round_off_in_si == 1) {
                          frm.doc.rounded_total = frm.doc.net_total;
                          frm.refresh_field('rounded_total');				
                        }
                        else {
                         if (frm.doc.net_total != Math.round(frm.doc.net_total)) {
                           frm.doc.round_off = Math.round(frm.doc.net_total) - frm.doc.net_total;
                           frm.doc.rounded_total = Math.round(frm.doc.net_total);
                           frm.refresh_field('round_off');
                           frm.refresh_field('rounded_total');				 
                         }
                         else{
                    
                          frm.doc.rounded_total = frm.doc.net_total;
                          frm.refresh_field("rounded_total");
                    
                          console.log(frm.doc.net_total)
                          console.log(frm.doc.rounded_total)
                          
                          
                         }
                       }
                       
                      });
                    
                      update_total_big_display(frm)  
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
                        'fieldname': ['default_advance_received_account']
                    },
                    callback: (r2) => {
                        frm.doc.advance_account = r2.message.default_advance_received_account
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

			frappe.db.get_value('Company', frm.doc.company, 'default_credit_sale', function(r) {
				if (r && r.default_credit_sale === 1) {
						frm.set_value('credit_sale', 1);
				}
			});

			set_default_payment_mode(frm);
		}

	},
});

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
		var roundedTotal = frm.doc.rounded_total;

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

	let netTotal = isNaN(frm.doc.net_total) ? 0 : parseFloat(frm.doc.net_total).toFixed(2);

    // Add 'AED' prefix and format net_total for display

	let displayHtml = `<div style="font-size: 25px; text-align: right; color: black;">AED ${netTotal}</div>`;


    // Directly update the HTML content of the 'total_big' field
    frm.fields_dict['total_big'].$wrapper.html(displayHtml);

}
