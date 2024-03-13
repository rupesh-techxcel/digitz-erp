// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Return', {

  refresh: function(frm){
    create_custom_buttons(frm)
    frappe.db.get_value('Company', frm.doc.company, 'default_credit_sale', function(r) {
       if (r && r.default_credit_sale === 1) {
           frm.set_value('credit_sale', 1);
       }
   });

	if (frm.doc.docstatus < 1) {
		frm.add_custom_button('Get Items From Sales', function () {
			// Call the custom method
			frm.events.get_items_for_return(frm);
		});
	}
  },
  get_items_for_return: function (frm) {

	if (!frm.doc.customer) {
		frappe.msgprint("Select Customer.");
		return;
	}

	let pending_invoices_data;

	// Fetch all supplier pending invoices and invoices already allocated in this payment_entry
	frappe.call({
		method: "digitz_erp.api.sales_invoice_api.get_sales_invoices_for_return",
		args: {
			customer: frm.doc.customer
		},
		callback: (r) => {
			pending_invoices_data = r.message;
			console.log("pending_invoices_data");
			console.log(pending_invoices_data);

			var dialog = new frappe.ui.Dialog({
				title: "Sales Selection",
				width: '100%',
				fields: [
					{
						fieldtype: "HTML",
						fieldname: "sales",
						label: "Sales Selection",
						options: '<div id="child-table-wrapper"></div>',
					},
				],
				primary_action: function () {


					var child_table_data_updated = child_table_control.get_value();

					// Iterate through the selected items
					child_table_data_updated.forEach(function (item) {

						if(item.__checked)
						{
							// Access item fields using item.fieldname
							console.log("Selected Item: ", item.name);
							frappe.call({
								method: "digitz_erp.api.sales_invoice_api.get_sales_line_items_for_return",
								args: {
									sales_invoice: item.name
								},
								callback: (r) => {

									const returnRows = r.message;

									console.log("r.message")
									console.log(r.message)

									// Iterate through each row in the items child table
									returnRows.forEach(newRow => {

										console.log(newRow)

										let existingRow =[]

										if(frm.doc.items)
											// Check if the row already exists in the child table
											 existingRow =  frm.doc.items.find(row => row.si_item_reference === newRow.si_item_reference);

										if (!frm.doc.items ||  !existingRow) {

											var return_item = frappe.model.get_new_doc('Sales Return Item');
												return_item.item = newRow.item
												return_item.warehouse = frm.doc.warehouse
												return_item.item_name = newRow.item_name
												return_item.display_name = newRow.display_name

												if(! newRow.display_name || newRow.display_name == "")
												{
													return_item.display_name = newRow.item_name
												}

												return_item.qty = newRow.qty
												return_item.qty_in_base_unit = newRow.qty_in_base_unit
												return_item.conversion_factor = newRow.conversion_factor

												return_item.unit = newRow.unit
												return_item.base_unit = newRow.base_unit
												return_item.rate = newRow.rate
												return_item.rate_in_base_unit = newRow.rate_in_base_unit
												return_item.tax = newRow.tax
												return_item.tax_rate = newRow.tax_rate
												return_item.rate_includes_tax = newRow.rate_includes_tax
												return_item.si_item_reference = newRow.si_item_reference

											console.log("return_item")
											console.log(return_item)
											// If the row doesn't exist, add it to the child table
											frm.add_child('items', return_item);
											frm.trigger("make_taxes_and_totals");
											frm.refresh_field('items');

											console.log(frm.doc.items)

										} else {
											// console.log("exists")
											// // If the row exists, you might want to update the existing row or handle it as needed
											// console.log(`Row with pi_item_reference ${newRow.pi_item_reference} already exists`);
										}
									});

								}})
						}

					});

					dialog.hide();
					// Refresh the child table after adding all rows

				}
			});

			dialog.$wrapper.find('.modal-dialog').css("max-width", "90%").css("width", "90%");
			dialog.show();

			// Create child table control and add it to the dialog after the dialog is created
			let child_table_control = frappe.ui.form.make_control({
				df: {
					fieldname: "sales_selection",
					fieldtype: "Table",
					cannot_add_rows: true,
					fields: [
						{
							fieldtype: 'Data',
							fieldname: 'name',
							label: 'Sales Invoice',
							in_place_edit: false,
							in_list_view: true,
							read_only: true
						},
						{
							fieldtype: 'Data',
							fieldname: 'customer',
							label: 'Customer',
							in_place_edit: false,
							in_list_view: true,
							read_only: true
						},
						{
							fieldtype: 'Date',
							fieldname: 'posting_date',
							label: 'Date',
							in_place_edit: false,
							in_list_view: true,
							read_only: true
						},
						{
							fieldtype: 'Currency',
							fieldname: 'rounded_total',
							label: 'Amount',
							in_place_edit: false,
							in_list_view: true,
							read_only: true
						},

					],
				},
				parent: dialog.get_field("sales").$wrapper.find('#child-table-wrapper'),
				render_input: true,
			});

			child_table_control.df.data = pending_invoices_data;
			child_table_control.refresh();
		}
	});
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
  setup: function (frm){
    frm.add_fetch('customer', 'full_address', 'customer_address')
		frm.add_fetch('customer', 'salesman', 'salesman')
		frm.add_fetch('customer', 'tax_id', 'tax_id')
		frm.add_fetch('customer', 'credit_days', 'credit_days')
		frm.add_fetch('payment_mode', 'account', 'payment_account')

  },
  credit_sale(frm) {
		frm.set_df_property("credit_days", "hidden", !frm.doc.credit_sale);
		frm.set_df_property("payment_mode", "hidden", frm.doc.credit_sale);
		frm.set_df_property("payment_account", "hidden", frm.doc.credit_sale);

		// if (frm.doc.credit_sale) {
		// 	frm.doc.payment_mode = "";
		// 	frm.doc.payment_account = "";
		// }
	},
  make_taxes_and_totals(frm) {
		frm.clear_table("taxes");
		frm.refresh_field("taxes");

		var gross_total = 0;
		var tax_total = 0;
		var net_total = 0;
		var discount_total = 0;

		//Avoid Possible NaNs
		frm.doc.gross_total = 0;
		frm.doc.net_total = 0;
		frm.doc.tax_total = 0;
		frm.doc.total_discount_in_line_items = 0;
		frm.doc.round_off = 0;
		frm.doc.rounded_total = 0;

		frm.doc.items.forEach(function (entry) {
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
					entry.net_amount = ((entry.qty * entry.rate) - entry.discount_amount)
					+ (((entry.qty * entry.rate) - entry.discount_amount) * (entry.tax_rate / 100))
				}
				else{

					entry.tax_amount = 0;
					entry.net_amount = ((entry.qty * entry.rate) - entry.discount_amount)
				}


				console.log("entry.tax_amount")
				console.log(entry.tax_amount)

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

							console.log(uomqty)
							console.log(uomrate)

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
		frm.refresh_field("items");
		frm.refresh_field("taxes");
		frm.refresh_field("gross_total");
		frm.refresh_field("net_total");
		frm.refresh_field("tax_total");
		frm.refresh_field("round_off");
		frm.refresh_field("rounded_total");

	},
  additional_discount(frm) {
    frm.trigger("make_taxes_and_totals");
  },
  rate_includes_tax(frm) {
    frappe.confirm('Are you sure you want to change this setting which will change the tax calculation in the line items ?',
      () => {
        frm.trigger("make_taxes_and_totals");
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
							console.log("Before assign default warehouse");
							console.log(r2.message.default_warehouse);
							frm.doc.warehouse = r2.message.default_warehouse;
							console.log(frm.doc.warehouse);
							//frm.doc.rate_includes_tax = r2.message.rate_includes_tax;
							frm.refresh_field("warehouse");
							frm.refresh_field("rate_includes_tax");
						}
					}

				)
			}
		})

	},
  get_item_units(frm) {

    frappe.call({
      method: 'digitz_erp.api.items_api.get_item_uoms',
      async: false,
      args: {
        item: frm.item
      },
      callback: (r) => {

        console.log(r)
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
  },
  customer(frm){

	frappe.call(
		{
			method: 'digitz_erp.accounts.doctype.gl_posting.gl_posting.get_party_balance',
			args: {
				'party_type': 'Customer',
				'party': frm.doc.customer
			},
			callback: (r) => {
				frm.set_value('customer_balance',r.message)
				frm.refresh_field("customer_balance");
			}
		});

  },
});

frappe.ui.form.on("Sales Return", "onload", function (frm) {
  if(frm.doc.credit_sale == 0){
        frappe.call({
                method: 'digitz_erp.selling.doctype.sales_return.sales_return.get_default_payment_mode',
                callback: function(response) {
                        if (response && response.message) {
                                frm.set_value('payment_mode', response.message);
                        } else {
                                frappe.msgprint('Default payment mode for sales not found.');
                        }
                }
        });
    }
	frm.trigger("get_default_company_and_warehouse");

	frm.set_query("price_list", function () {
		return {
			"filters": {
				"is_buying": 1
			}
		};
	});

	frm.set_query("supplier", function () {
		return {
			"filters": {
				"is_disabled": 0
			}
		};
	});
    frm.set_query("ship_to_location", function () {
      return {
        "filters": {
          "parent": frm.doc.customer
        }
      };
    });
});

frappe.ui.form.on('Sales Return Item', {
	// cdt is Child DocType name i.e Quotation Item
	// cdn is the row name for e.g bbfcb8da6a
	item(frm, cdt, cdn) {

		let row = frappe.get_doc(cdt, cdn);

		row.warehouse = frm.doc.warehouse;

		frm.item = row.item;
		frm.trigger("get_item_units");

		let tax_excluded_for_company = false
		frappe.call(
			{
				method:'digitz_erp.api.settings_api.get_company_settings',
				async:false,
				callback(r){
					console.log("digitz_erp.api.settings_api.get_company_settings")
					console.log(r)
					tax_excluded_for_company = r.message[0].tax_excluded
					console.log("use_customer_last_price")
					console.log(use_customer_last_price)
				}
			}
		);


		frappe.call(
			{
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Item',
					'filters': { 'item_code': row.item },
					'fieldname': ['item_name', 'base_unit', 'tax', 'tax_excluded']
				},
				callback: (r) => {
					row.item_name = r.message.item_name;
					//row.uom = r.message.base_unit;

					if(tax_excluded_for_company)
					{
						row.tax_excluded = true;
					}
					else
					{
						row.tax_excluded = r.message.tax_excluded;
					}

					row.base_unit = r.message.base_unit;
					row.unit = r.message.base_unit;
					row.conversion_factor = 1;
					row.display_name = row.item_name
					frm.item = row.item
					frm.warehouse = row.warehouse
					console.log("before trigger")
					frm.trigger("get_item_stock_balance");

					if (!row.tax_excluded) {
						frappe.call(
							{
								method: 'frappe.client.get_value',
								args: {
									'doctype': 'Tax',
									'filters': { 'tax_name': r.message.tax },
									'fieldname': ['tax_name', 'tax_rate']
								},
								callback: (r2) => {
									row.tax = r2.message.tax_name;
									row.tax_rate = r2.message.tax_rate
								}
							})
					}
					else {
						row.tax = "";
						row.tax_rate = 0;
					}

					console.log("Item:- %s", row.item);
					console.log("Price List");
					console.log(frm.doc.price_list);

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
								'price_list': frm.doc.price_list,
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

					frm.trigger("make_taxes_and_totals");
					frm.refresh_field("items");
					//  Get current stock for the item in the warehouse
				}
			});
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
	qty(frm, cdt, cdn) {
		frm.trigger("make_taxes_and_totals");
	},
	rate(frm, cdt, cdn) {
		frm.trigger("make_taxes_and_totals");
	},
	rate_includes_tax(frm, cdt, cdn) {
		frm.trigger("make_taxes_and_totals");
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
					}
					frm.trigger("make_taxes_and_totals");

					frm.refresh_field("items");
				}

			}
		);
	},
	discount_percentage(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		console.log("from discount_percentage")
		console.log("Gross Amount %f", row.gross_amount);


		var discount_percentage = row.discount_percentage;

		console.log("Percentage %s", row.discount_percentage);

		if (row.discount_percentage > 0) {
			console.log("Apply Discount Percentage")
			var discount = row.gross_amount * (row.discount_percentage / 100);
			row.discount_amount = discount;
		}
		else {
			row.discount_amount = 0;
			row.discount_percentage = 0;
		}

		frm.trigger("make_taxes_and_totals");
		frm.refresh_field("items");
	},
	discount_amount(frm, cdt, cdn) {
		console.log("from discount_amount")

		let row = frappe.get_doc(cdt, cdn);
		var discount = row.discount_amount;

		if (row.discount_amount > 0) {
			var discount_percentage = discount * 100 / row.gross_amount;
			row.discount_percentage = discount_percentage;
		}
		else {
			row.discount_amount = 0;
			row.discount_percentage = 0;
		}

		frm.trigger("make_taxes_and_totals");

		frm.refresh_field("items");
	},
	warehouse(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		frm.item = row.item
		frm.warehouse = row.warehouse
		frm.trigger("get_item_stock_balance");
	},
	items_add(frm, cdt, cdn) {
    var child = locals[cdt][cdn];
		if (frm.doc.default_cost_center) {
			frappe.model.set_value(cdt, cdn, 'cost_center', frm.doc.default_cost_center);
		}

		console.log("from item_add")
		let row = frappe.get_doc(cdt, cdn);
		row.warehouse = frm.doc.warehouse

		frm.trigger("make_taxes_and_totals");

	},
	items_remove(frm, cdt, cdn) {
		frm.trigger("make_taxes_and_totals");
	}
});


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
