// Copyright (c) 2025,   and contributors
// For license information, please see license.txt

frappe.ui.form.on("Sub Contracting Order", {

    refresh(frm) {

		if (frm.doc.docstatus === 1) { // Check if the document is submitted
            toggle_material_issue_button(frm);
		}
	},
    edit_posting_date_and_time(frm) {

		//console.log(frm.doc.edit_posting_date_and_time);
		console.log(frm.doc.edit_posting_date_and_time);

		if (frm.doc.edit_posting_date_and_time == 1) {
			frm.set_df_property("posting_date", "read_only", 0);
			frm.set_df_property("posting_time", "read_only", 0);
		}
		else {
			frm.set_df_property("posting_date", "read_only", 1);
			frm.set_df_property("posting_time", "read_only", 1);
		}
	},

    get_default_company_and_warehouse(frm) {
		
        console.log("From Get Default Warehouse Method in the parent form");

        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Global Settings',
                fieldname: 'default_company'
            },
            callback: function (r) {
                if (r && r.message && r.message.default_company) {
                    const default_company = r.message.default_company;
                    frm.set_value('company', default_company);
                }
            
                frappe.call({
                    method: 'frappe.client.get_value',
                    args: {
                        doctype: 'Company',
                        filters: { company_name: r.message.default_company },
                        fieldname: ['default_warehouse', 'rate_includes_tax','tax']
                    },
                    callback: function (r2) {
                        if (r2 && r2.message) {
                            if (r2.message.default_warehouse) {
                                frm.set_value('warehouse', r2.message.default_warehouse);
                            }

                            if ('rate_includes_tax' in r2.message) {
                                frm.set_value('rate_includes_tax', r2.message.rate_includes_tax);
                            }

                            if('tax' in r2.message)
                            {
                                frm.set_value('tax', r2.message.tax);
                            }
                        } else {
                            console.error('No data found for Company: ', default_company);
                        }
                    }
                });
            
            }})
    },
    assign_defaults(frm)
	{
        if(frm.is_new())
        {
            frm.trigger("get_default_company_and_warehouse")
        }
    },   
    make_taxes_and_totals(frm) {

		console.log("from make totals..")
		

		var gross_total = 0;
		var tax_total = 0;
		var net_total = 0;
		var discount_total = 0;

		//Avoid Possible NaN
		frm.doc.gross_total = 0;
		frm.doc.net_total = 0;
		frm.doc.tax_total = 0;
		frm.doc.total_discount_in_line_items = 0;
		frm.doc.round_off = 0;
		frm.doc.rounded_total = 0;
        

		frm.doc.items.forEach(function (entry) {

			console.log("Item in Row")
			console.log(entry.item);

			var tax_in_rate = 0;

			//rate_includes_tax column in items table is readonly and it depends the form's rate_includes_tax column
			entry.rate_includes_tax = frm.doc.rate_includes_tax;
			entry.gross_amount = 0
			entry.tax_amount = 0;
			entry.net_amount = 0
			//To avoid complexity mentioned below, rate_includes_tax option do not support with line item discount

			if (entry.rate_includes_tax) //Disclaimer - since tax is calculated after discounted amount. this implementation
			{							// has a mismatch with it. But still it approves to avoid complexity for the customer
				// also this implementation is streight forward than the other way
				if( entry.tax_rate >0){

					tax_in_rate = entry.rate * (entry.tax_rate / (100 + entry.tax_rate));
					entry.rate_excluded_tax = entry.rate - tax_in_rate;
					entry.tax_amount = (entry.qty * entry.rate) * (entry.tax_rate / (100 + entry.tax_rate))
				}
				else
				{
					entry.rate_excluded_tax = entry.rate
					entry.tax_amount = 0
				}

				entry.net_amount = ((entry.qty * entry.rate) - entry.discount_amount);
				entry.gross_amount = entry.net_amount - entry.tax_amount;
			}
			else {
				entry.rate_excluded_tax = entry.rate;

				if( entry.tax_rate >0){
					entry.tax_amount = (((entry.qty * entry.rate) - entry.discount_amount) * (entry.tax_rate / 100))

                    console.log("entry.discount_amount")
                    console.log(entry.discount_amount)
                    
					entry.net_amount = ((entry.qty * entry.rate) - entry.discount_amount)
					+ (((entry.qty * entry.rate) - entry.discount_amount) * (entry.tax_rate / 100))
				}
				else{

					entry.tax_amount = 0;
					entry.net_amount = ((entry.qty * entry.rate) - entry.discount_amount)
				}


				console.log("entry.tax_amount")
				console.log(entry.tax_amount)
				console.log("entry.tax_rate",entry.tax_rate)

				console.log("Net amount %f", entry.net_amount);
				entry.gross_amount = entry.qty * entry.rate_excluded_tax;
			}

			//var taxesTable = frm.add_child("taxes");
			//taxesTable.tax = entry.tax;
			gross_total = gross_total + entry.gross_amount;
			tax_total = tax_total + entry.tax_amount;
			discount_total = discount_total + entry.discount_amount;

			entry.qty_in_base_unit = entry.qty * entry.conversion_factor;
			entry.rate_in_base_unit = entry.rate / entry.conversion_factor;

			if (!isNaN(entry.qty) && !isNaN(entry.rate)) {

				frappe.call({
					method: 'digitz_erp.api.items_api.get_item_uoms',
					async: false,
					args: {
						item: entry.item
					},
					callback: (r) => {
						console.log("get_item_uoms result")
						console.log(r.message);

						var units = r.message;
						var output = "";
						var output2 = "";
						entry.unit_conversion_details = "";
						$.each(units, (a, b) => {

							var conversion = b.conversion_factor
							var unit = b.unit
							console.log("uomqty")

							var uomqty = entry.qty_in_base_unit / conversion;
							console.log("uomrate")
							var uomrate = entry.rate_in_base_unit * conversion;

							var uomqty2 = "";

							if (uomqty == entry.qty_in_base_unit) {
								uomqty2 = uomqty + " " + unit + " @ " + uomrate
							}
							else {
								if (uomqty > Math.trunc(uomqty)) {
									var excessqty = Math.round((uomqty - Math.trunc(uomqty)) * conversion, 0);
									uomqty2 = uomqty + " " + unit + "(" + Math.trunc(uomqty) + " " + unit + " " + excessqty + " " + entry.base_unit + ")" + " @ " + uomrate;
								}
								else {
									uomqty2 = uomqty + " " + unit + " @ " + uomrate
								}
							}

							output = output + uomqty2 + "\n";
							//output2 = output2 + unit + " rate: " + uomrate + "\n";

						}
						)
						console.log(output + output2);
						entry.unit_conversion_details = output
					}
				}

				)
			}
			else {
				console.log("Qty and Rate are NaN");
			}

		});

		if (isNaN(frm.doc.additional_discount)) {
			frm.doc.additional_discount = 0;
		}

		frm.doc.gross_total = gross_total;
		frm.doc.net_total = gross_total + tax_total - frm.doc.additional_discount;
		frm.doc.tax_total = tax_total;
		frm.doc.total_discount_in_line_items = discount_total;
		console.log("Net Total Before Round Off")
		console.log(frm.doc.net_total)

		if (frm.doc.net_total != Math.round(frm.doc.net_total)) {
			frm.doc.round_off = Math.round(frm.doc.net_total) - frm.doc.net_total;
			frm.doc.rounded_total = Math.round(frm.doc.net_total);
		}
		else {
			frm.doc.rounded_total = frm.doc.net_total;
		}

		// update_total_big_display(frm)

		console.log("Totals");

		console.log(frm.doc.gross_total);
		console.log(frm.doc.tax_total);
		console.log(frm.doc.net_total);
		console.log(frm.doc.round_off);
		console.log(frm.doc.rounded_total);

		frm.refresh_field("items");
		frm.refresh_field("taxes");

		frm.refresh_field("gross_total");
		frm.refresh_field("net_total");
		frm.refresh_field("tax_total");
		frm.refresh_field("round_off");
		frm.refresh_field("rounded_total");

	},
});

function toggle_material_issue_button(frm) {

    frappe.call({
		method: "digitz_erp.api.sub_contracting_api.check_pending_items_for_material_issue",
		args: {
			sub_contracting_order: frm.doc.name
		},
		callback: function(response) {
			if (response.message) {
                    
                frm.add_custom_button('Material Issue', function () {
                    // Call the server-side method to create Material Issue
                    frappe.call({
                        method: 'digitz_erp.api.sub_contracting_api.create_material_issue',
                        args: {
                            sub_contracting_order: frm.doc.name,
                        },
                        callback: function (response) {
                            if (response.message) {
                                // Sync the returned document with the client-side model
                                frappe.model.sync(response.message);
                    
                                // Open the Material Issue document in the form view
                                frappe.set_route('Form', 'Material Issue', response.message.name);
                            } else {
                                frappe.msgprint('No Material Issue was generated. All items might have been issued already.');
                            }
                        },
                        error: function (error) {
                            // Handle any error from the server-side call
                            frappe.msgprint('Failed to create Material Issue. Please check the server logs for more details.');
                        }
                    });
                    
                });
            }
            else
            {
                frm.remove_custom_button('Material Issue'); // Remove the button if no items require issuance
            }}
    });
}

frappe.ui.form.on("Sub Contracting Order", "onload", function (frm) {

	frm.trigger("assign_defaults") 

});

frappe.ui.form.on('Sub Contracting Order Item', {

    single_bom(frm,cdt,cdn)
    {
        console.log("from single_bom")
        let row = frappe.get_doc(cdt, cdn);
        row.tax = frm.doc.tax
        if(frm.doc.tax)
        {
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
                        frm.refresh_field("items");
                        frm.trigger("make_taxes_and_totals");
                    }
                });

        }
        else
        {
            row.tax_rate = 0
        }
        frm.refresh_field("items")
    },

// item(frm,cdt,cdn){

//     let row = frappe.get_doc(cdt, cdn);

//     frappe.cal
// l(
//         {
//             method: 'frappe.client.get_value',
//             args: {
//                 'doctype': 'Item',
//                 'filters': { 'item_code': row.item },
//                 'fieldname': ['item_name','description', 'base_unit', 'tax', 'tax_excluded','height','width','area','length']
//             },
//             callback: (r) => {

//     if (!r.message.tax_excluded) {
//         frappe.call(
//             {
//                 method: 'frappe.client.get_value',
//                 args: {
//                     'doctype': 'Tax',
//                     'filters': { 'tax_name': r.message.tax },
//                     'fieldname': ['tax_name', 'tax_rate']
//                 },
//                 callback: (r2) => {
//                     row.tax = r2.message.tax_name;
//                     row.tax_rate = r2.message.tax_rate;
//                     // console.log("ajay", row.tax,row.tax_rate,(row.tax_rate * row.gross_amount), row.gross_amount)
//                     frm.trigger("make_taxes_and_totals");
//                         frm.refresh_field("items");
//                 }

//             })
//         }    
//         else {
//             row.tax = "";
//             row.tax_rate = 0;
//         }
        
//     }});
    

// },

qty(frm, cdt, cdn) {
		
    frm.trigger("make_taxes_and_totals");
},
rate(frm, cdt, cdn) {
    
    frm.trigger("make_taxes_and_totals");
},
rate_includes_tax(frm, cdt, cdn) {
    frm.trigger("make_taxes_and_totals");
},
tax_excluded(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);

    if (row.tax_excluded) {
        row.tax = "";
        row.tax_rate = 0;
        frm.refresh_field("items");
        frm.trigger("make_taxes_and_totals");
    }
},
tax(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);

    if (!row.tax_excluded) //For tax excluded, tax and rate already adjusted
    {
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
                    frm.refresh_field("items");
                    frm.trigger("make_taxes_and_totals");
                }
            });
    }
},
});

