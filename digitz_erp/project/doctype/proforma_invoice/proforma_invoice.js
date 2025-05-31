// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Proforma Invoice", {
	onload(frm) {

        frm.trigger("assign_defaults")
                         
	},
    assign_defaults(frm)
    {
       frm.trigger('get_default_company_and_warehouse');    
       
       frappe.db.get_value('Company', frm.doc.company, 'default_credit_sale', function(r) {
        if (r && r.default_credit_sale === 1) {
                frm.set_value('credit_sale', 1);
        }
        });

        set_default_payment_mode(frm);
    },
    refresh(frm)
	{
		
	},
    progress_entry(frm) {
        frappe.call({
            method: "frappe.client.get",
            async: false,
            args: {
                doctype: "Progress Entry",
                name: frm.doc.progress_entry,
            },
            callback: function(response) {
                let progress_entry = response.message;
                if (progress_entry) {
                    console.log("Fetched Progress Entry:", progress_entry);
    
                    progress_entry.progress_entry_items.forEach(element => {
                        let row = {
                            "prev_completion": element.prev_completion,
                            "total_completion": element.total_completion,
                            "current_completion": element.current_completion,
                            "prev_net_amount": element.prev_net_amount,
                            "total_net_amount": element.total_net_amount,
                            "prev_gross_amount": element.prev_gross_amount,
                            "total_gross_amount": element.total_gross_amount,
                            "tax": element.tax,
                            "tax_rate": element.tax_rate,
                            "tax_amount": element.tax_amount,
                            "gross_amount": element.gross_amount,
                            "net_amount": element.net_amount,
                            "item": element.item,
                            "item_name": element.item_name,
                            "item_gross_amount": element.item_gross_amount,
                            "item_tax_amount": element.item_tax_amount,
                            "item_net_amount": element.item_net_amount
                        };
                        frm.add_child('progress_entry_items', row);
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
    
                    frm.refresh_field('progress_entry_items');
    
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
        });
    },
    credit_sale(frm)
    {
        set_default_payment_mode(frm);
    },      
    get_default_company_and_warehouse(frm) {

        console.log("get_default_company_and_warehouse")


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
    
});

function set_default_payment_mode(frm)
{
    console.log("set_default_payment_mode")

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

function update_total_big_display(frm) {

	let display_total = isNaN(frm.doc.rounded_total) ? 0 : parseFloat(frm.doc.rounded_total).toFixed(0);

    // Add 'AED' prefix and format net_total for display

    console.log("display_total", display_total)

	let displayHtml = `<div style="font-size: 25px; text-align: right; color: black;">AED ${display_total}</div>`;


    // Directly update the HTML content of the 'total_big' field
    frm.fields_dict['total_big'].$wrapper.html(displayHtml);

    frm.refresh_field('total_big');

}