// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Return', {
	
	refresh: function (frm) {

        if (frm.doc.docstatus < 1) {
            frm.add_custom_button('Get Items From Purchase', function () {
                // Call the custom method
                frm.events.get_items_for_return(frm);
            });
        }
    },
	supplier(frm){

		frappe.call(
			{
				method: 'digitz_erp.accounts.doctype.gl_posting.gl_posting.get_party_balance',
				args: {
					'party_type': 'Supplier',
					'party': frm.doc.supplier
				},
				callback: (r) => {
					frm.set_value('supplier_balance',r.message)
					frm.refresh_field("supplier_balance");
				}
			});
		
	 },
	get_items_for_return: function (frm) {
		if (!frm.doc.supplier) {
			frappe.msgprint("Select supplier.");
			return;
		}
	
		let pending_invoices_data;
	
		// Fetch all supplier pending invoices and invoices already allocated in this payment_entry
		frappe.call({
			method: "digitz_erp.api.purchase_invoice_api.get_purchase_invoices_for_return",
			args: {
				supplier: frm.doc.supplier
			},
			callback: (r) => {
				pending_invoices_data = r.message;
				console.log("pending_invoices_data");
				console.log(pending_invoices_data);
	
				var dialog = new frappe.ui.Dialog({
					title: "Purchase Selection",
					width: '100%',
					fields: [
						{
							fieldtype: "HTML",
							fieldname: "purchase",
							label: "Payment Allocation",
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
									method: "digitz_erp.api.purchase_invoice_api.get_purchase_line_items_for_return",									
									args: {
										purchase_invoice: item.name
									},
									callback: (r) => {

										console.log("digitz_erp.api.purchase_invoice_api.get_purchase_line_items_for_return")
										console.log(r.message)

										const returnRows = r.message;

										// Iterate through each row in the items child table
										returnRows.forEach(newRow => {

											console.log("newRow")
											console.log(newRow)
																						
											// Check if the row already exists in the child table
											const existingRow = frm.doc.items.find(row => row.pi_item_reference === newRow.pi_item_reference);
											

											if (!existingRow) {
												
												console.log("adding new row")

												var return_item = frappe.model.get_new_doc('Purchase Return Item');
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
												return_item.conversion_factor = newrow.conversion_factor
												return_item.unit = newRow.unit
												return_item.base_unit = newRow.base_unit
												return_item.rate = newRow.rate
												return_item.rate_in_base_unit = newRow.rate_in_base_unit
												return_item.tax = newRow.tax
												return_item.tax_rate = newRow.tax_rate
												return_item.rate_includes_tax = newRow.rate_includes_tax
												console.log("before storing item_reference")
												console.log(newRow.pi_item_reference)
												return_item.pi_item_reference = newRow.pi_item_reference
												console.log("after storing item_reference")
												console.log(return_item.pi_item_reference)

												// If the row doesn't exist, add it to the child table
												frm.add_child('items', return_item);
												frm.trigger("make_taxes_and_totals");
												frm.refresh_field('items');
												console.log("child rows added")
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
						fieldname: "payment_allocation",
						fieldtype: "Table",
						cannot_add_rows: true,
						fields: [
							{
								fieldtype: 'Data',
								fieldname: 'name',
								label: 'Purchase Invoice',
								in_place_edit: false,
								in_list_view: true,
								read_only: true
							},
							{
								fieldtype: 'Data',
								fieldname: 'supplier',
								label: 'Supplier',
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
					parent: dialog.get_field("purchase").$wrapper.find('#child-table-wrapper'),
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
  credit_purchase(frm) {
		frm.set_df_property("credit_days", "hidden", !frm.doc.credit_purchase);
		frm.set_df_property("payment_mode", "hidden", frm.doc.credit_purchase);
		frm.set_df_property("payment_account", "hidden", frm.doc.credit_purchase);

		if (frm.doc.credit_purchase) {
			frm.doc.payment_mode = "";
			frm.doc.payment_account = "";
		}
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
				tax_in_rate = entry.rate * (entry.tax_rate / (100 + entry.tax_rate));
				entry.rate_excluded_tax = entry.rate - tax_in_rate;
				entry.tax_amount = (entry.qty * entry.rate) * (entry.tax_rate / (100 + entry.tax_rate))
				entry.net_amount = ((entry.qty * entry.rate) - entry.discount_amount);
				entry.gross_amount = entry.net_amount - entry.tax_amount;
			}
			else {
				entry.rate_excluded_tax = entry.rate;
				entry.tax_amount = (((entry.qty * entry.rate) - entry.discount_amount) * (entry.tax_rate / 100))
				entry.net_amount = ((entry.qty * entry.rate) - entry.discount_amount)
					+ (((entry.qty * entry.rate) - entry.discount_amount) * (entry.tax_rate / 100))
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

        frm.doc.item_units = units
        frm.refresh_field("item_units");
      }
    })
  }
});

frappe.ui.form.on("Purchase Return", "onload", function (frm) {

	// Remove the blank row shows initially
	frm.doc.items = frm.doc.items.filter(function (item) {
		return item.item && item.qty && item.rate;
	});

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


});

frappe.ui.form.on('Purchase Return Item', {
	// cdt is Child DocType name i.e Quotation Item
	// cdn is the row name for e.g bbfcb8da6a
	item(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		console.log("here from item")

		let doc = frappe.model.get_value("", row.item);
		row.warehouse = frm.doc.warehouse;
		frm.item = row.item;
		frm.trigger("get_item_units");
		frm.trigger("make_taxes_and_totals");

		frappe.call(
			{
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Item',
					'filters': { 'item_code': row.item },
					'fieldname': ['item_name', 'base_unit', 'tax', 'tax_excluded']
				},
				callback: (r) => {
					console.log("r")
					console.log(r)
					row.item_name = r.message.item_name;
					//row.uom = r.message.base_unit;
					row.tax_excluded = r.message.tax_excluded;
					row.base_unit = r.message.base_unit;
					row.unit = r.message.base_unit;
					row.conversion_factor = 1;
					row.display_name = row.item
					frm.item = row.item
					frm.warehouse = row.warehouse
					console.log("before trigger")
					frm.trigger("get_item_stock_balance");

					if (!r.message.tax_excluded) {
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
								'currency': currency	,
								'date': frm.doc.posting_date							
							},
							callback(r) {
								console.log("digitz_erp.api.item_price_api.get_item_price")
								console.log(r)
								row.rate = parseFloat(r.message);
								row.rate_in_base_unit = parseFloat(r.message);
							}
						});	

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
		let row = frappe.get_doc(cdt, cdn);
		row.warehouse = frm.doc.warehouse
		frm.trigger("make_taxes_and_totals");
		frm.refresh_field("items");
	},
	items_remove(frm, cdt, cdn) {
		frm.trigger("make_taxes_and_totals");
	}
});
