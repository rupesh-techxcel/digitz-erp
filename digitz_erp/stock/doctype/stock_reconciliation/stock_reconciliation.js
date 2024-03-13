// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Stock Reconciliation', {
	refresh: function(frm) {
		create_custom_buttons(frm)
		frm.set_query('account', () => {
    return {
        filters: {
            root_type: 'Liability',
						// is_group: 1
        }
    }
})
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
		var default_company = ""
		console.log("From Get Default Warehouse Method in the parent form")

		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				'doctype': 'Global Settings',
				'fieldname': 'default_company'
			},
			callback: (r) => {

				default_company = r.message.default_company
				frm.doc.company = r.message.default_company
				frm.refresh_field("company");
				frappe.call(
					{
						method: 'frappe.client.get_value',
						args: {
							'doctype': 'Company',
							'filters': { 'company_name': default_company },
							'fieldname': ['default_warehouse', 'rate_includes_tax']
						},
						callback: (r2) => {
							frm.doc.warehouse = r2.message.default_warehouse;
							frm.refresh_field("warehouse");
						}
					}

				)
			}
		})
	},
	get_item_stock_balance(frm) {

		console.log("From get_item_stock_balance")
		console.log(frm.item)
		console.log(frm.warehouse)

		frappe.call(
			{
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Stock Balance',
					'filters': { 'item': frm.item, 'warehouse': frm.warehouse },
					'fieldname': ['stock_qty']
				},
				callback: (r2) => {
					console.log(r2)
					frm.doc.selected_item_stock_qty_in_the_warehouse = r2.message.stock_qty
					frm.refresh_field("selected_item_stock_qty_in_the_warehouse");

				}
			});
	},
	make_totals(frm) {
		console.log("from make totals..")
		frm.clear_table("taxes");
		frm.refresh_field("taxes");

		var gross_total = 0;
		var tax_total = 0;
		var net_total = 0;
		var discount_total = 0;

		//Avoid Possible NaN

		frm.doc.net_total = 0;
		net_total = 0

		frm.doc.items.forEach(function (entry) {

				entry.net_amount = entry.qty * entry.rate
				net_total= net_total + entry.net_amount

				entry.qty_in_base_unit = entry.qty * entry.conversion_factor;
				entry.rate_in_base_unit = entry.rate / entry.conversion_factor;
			})

			frm.doc.net_total = net_total
			frm.refresh_field("items");
			frm.refresh_field("net_total");
	}
	,
	get_item_units(frm) {

		frappe.call({
			method: 'digitz_erp.api.items_api.get_item_uoms',
			async: false,
			args: {
				item: frm.item
			},
			callback: (r) => {

				var units = ""
				for(var i = 0; i < r.message.length; i++)
				{
					if(i==0)
					{
						units = r.message[i].unit
					}
					else
					{
						units = units + ", " + r.message[i].unit
					}
				}

				frm.doc.item_units = "Unit(s) for "+ frm.item +": " +units
				frm.refresh_field("item_units");
			}
		})
	}
});

frappe.ui.form.on("Stock Reconciliation", "onload", function (frm) {

	//Since the default selectionis cash
	//frm.set_df_property("date","read_only",1);
	frm.set_query("warehouse", function () {
		return {
			"filters": {
				"is_group": 0
			}
		};
	});

	frm.trigger("get_default_company_and_warehouse");
})

frappe.ui.form.on('Stock Reconciliation Item', {
	item(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (frm.doc.default_cost_center) {
			frappe.model.set_value(cdt, cdn, 'cost_center', frm.doc.default_cost_center);
		}

		let row = frappe.get_doc(cdt, cdn);
		frappe.call(
			{
			method: 'frappe.client.get_value',
					args: {
						'doctype': 'Item',
						'filters': { 'item_code': row.item },
						'fieldname': ['item_name', 'base_unit', 'tax', 'tax_excluded']
					},
					callback: (r) => {

						console.log(r.message)

						row.item_name = r.message.item_name;
						row.base_unit = r.message.base_unit;
						row.unit = r.message.base_unit;

						console.log("unit, baseunit, r.message.base_unit")
						console.log(row.unit)
						console.log(row.base_unit)
						console.log(r.message.base_unit)

						frm.item = row.item
						frm.trigger("get_item_units");

						row.conversion_factor = 1;
						frm.warehouse = row.warehouse

						row.warehouse = frm.doc.warehouse
						row.display_name = row.item_name
						frm.trigger("get_item_stock_balance");

						console.log("row")
						console.log(row)

						frappe.call(
							{
								method: 'digitz_erp.api.items_api.get_item_valuation_rate',
								async: false,
								args: {
									'item': row.item,
									'posting_date': frm.doc.posting_date,
									'posting_time': frm.doc.posting_time
								},
								callback(r) {
									console.log("Valuation rate in console")
									console.log(r.message)

									if(r.message == 0)
									{
										let currency = ""
										console.log("before call digitz_erp.api.settings_api.get_default_currency")
										frappe.call(
											{
												method:'digitz_erp.api.settings_api.get_default_currency',
												async:false,
												callback(r){
													console.log(r)
													currency = r.message
													console.log("currency")
													console.log(currency)
												}
											}
										);

										frappe.call(
											{
												method: 'digitz_erp.api.item_price_api.get_item_price',
												async: false,

												args: {
													'item': row.item,
													'price_list': 'Standard Buying',
													'currency': currency,
													'date': frm.doc.posting_date
												},
												callback(r) {
													console.log("digitz_erp.api.item_price_api.get_item_price")
													console.log(r)
													row.rate = parseFloat(r.message);
													row.rate_in_base_unit = parseFloat(r.message);
												}
											});

									}
									else
									{
										row.rate = r.message
										row.rate_in_base_unit = r.message

									}

								}
							});
					}
				});

		frm.refresh_field("items");
		console.log("Before get valuation rate for the item")

	},
	warehouse(frm, cdt, cdn) {

		let row = frappe.get_doc(cdt, cdn);
		frm.item = row.item
		frm.warehouse = row.warehouse
		frm.trigger("get_item_stock_balance");
	},
	qty(frm, cdt, cdn) {

		frm.trigger("make_totals")
	},
	rate(frm, cdt, cdn) {

		frm.trigger("make_totals")
	},
	unit(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);

		frappe.call(
			{
				method: 'digitz_erp.api.items_api.get_item_uom',
				async: false,
				args: {
					item: row.item,
					unit: row.unit
				},
				callback(r) {
					if (r.message.length == 0) {
						frappe.msgprint("Invalid unit, Unit does not exists for the item.");
						row.unit = row.base_unit;
						row.conversion_factor = 1;
					}
					else {
						console.log(r.message[0].conversion_factor);
						row.conversion_factor = r.message[0].conversion_factor;
						row.rate = row.rate_in_base_unit * row.conversion_factor;
						//row.rate = row.rate * row.conversion_factor;
						//frappe.confirm('Rate converted for the unit selected. Do you want to convert the qty as well ?',
						//() => {
						//row.qty = row.qty/ row.conversion_factor;
						//})
					}
					frm.trigger("make_totals");

					frm.refresh_field("items");
				}

			}
		);
	},
}
)


let create_custom_buttons = function(frm){
	if (frappe.user.has_role('Management')) {
		if(!frm.is_new() && (frm.doc.docstatus == 1)){
		frm.add_custom_button('General Ledgers',() =>{
				general_ledgers(frm)
		}, 'Postings');
			frm.add_custom_button('Stock Ledgers',() =>{
				stock_ledgers(frm)
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


let stock_ledgers = function (frm) {
    frappe.call({
        method: "digitz_erp.api.accounts_api.get_stock_ledgers",
        args: {
			voucher: frm.doc.doctype,
            voucher_no: frm.doc.name
        },
        callback: function (response) {
            let stock_ledgers_data = response.message;

            // Generate HTML content for the popup
            let htmlContent = '<div style="max-height: 400px; overflow-y: auto;">' +
                              '<table class="table table-bordered" style="width: 100%;">' +
                              '<thead>' +
                              '<tr>' +                              
                              '<th style="width: 10%;">Item Code</th>' +
							  '<th style="width: 20%;">Item Name</th>' +
                              '<th style="width: 15%;">Warehouse</th>' +
                              '<th style="width: 10%;">Qty In</th>' +
                              '<th style="width: 10%;">Qty Out</th>' +
                              '<th style="width: 15%;">Valuation Rate</th>' +
                              '<th style="width: 15%;">Balance Qty</th>' +
                              '<th style="width: 15%;">Balance Value</th>' +
                              '</tr>' +
                              '</thead>' +
                              '<tbody>';

            // Loop through the data and create rows
            stock_ledgers_data.forEach(function (ledger) {
                htmlContent += '<tr>' +                               
                               `<td><a href="/app/item/${ledger.item}" target="_blank">${ledger.item}</a></td>` +
							   `<td>${ledger.item_name}</td>` +
                               `<td>${ledger.warehouse}</td>` +
                               `<td>${ledger.qty_in}</td>` +
                               `<td>${ledger.qty_out}</td>` +
                               `<td>${ledger.valuation_rate}</td>` +
                               `<td>${ledger.balance_qty}</td>` +
                               `<td>${ledger.balance_value}</td>` +
                               '</tr>';
            });

            htmlContent += '</tbody></table></div>';

            // Create and show the dialog
            let d = new frappe.ui.Dialog({
                title: 'Stock Ledgers',
                fields: [{
                    fieldtype: 'HTML',
                    fieldname: 'stock_ledgers_html',
                    options: htmlContent
                }],
                primary_action_label: 'Close',
                primary_action: function () {
                    d.hide();
                }
            });

            // Set custom width for the dialog
            d.$wrapper.find('.modal-dialog').css('max-width', '85%'); // or any specific width like 800px

            d.show();
        }
    });
};
