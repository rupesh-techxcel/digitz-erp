// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice', {

	refresh: function (frm) {

		// if(frm.doc.docstatus == 1) 
		// if (!frm.doc.__islocal && !frm.doc.auto_save_delivery_note) {

		// 	frm.add_custom_button('Create/Update Delivery Note', () => {
		// 		frm.call("generate_delivery_note")
		// 	},
		// 	)
		// }

	},
	after_save: function (frm) {

		 if (frm.doc.auto_save_delivery_note) {
			frm.call("auto_generate_delivery_note")
		 }
	},	
	validate: function (frm) {		

		var valid = false;

		frm.doc.items.forEach(function (entry) {

			if (typeof (entry) == 'undefined') {

			}
			else {
				valid = true;
			}
		});

		if(!frm.doc.credit_sale && !frm.doc.payment_account)
		{
			valid = false;
			frappe.msgprint("Select payment account")
		}

		if(!frm.doc.credit_sale && !frm.doc.payment_mode)
		{
			valid = false;
			frappe.msgprint("Select payment mode")
		}

		if (!valid) {
			frappe.message("No valid item found in the document");
			return;
		}

		if(frm.doc.__islocal) //When the invoice is created by duplicating from an existing invoice, there may be delivery notes allocated
		{					// and it needs to be removed
			if(frm.doc.delivery_notes)
			{
					frm.doc.delivery_notes = undefined;
			}
		}
	},
	setup: function (frm) {

		frm.add_fetch('customer', 'full_address', 'customer_address')
		frm.add_fetch('customer', 'salesman', 'salesman')
		frm.add_fetch('customer', 'tax_id', 'tax_id')
		frm.add_fetch('customer', 'credit_days', 'credit_days')
		frm.add_fetch('payment_mode', 'account', 'payment_account')
		

		frm.set_query("ship_to_location", function () {
			return {
				"filters": {
					"parent": frm.doc.customer
				}
			};
		});
	},
	customer(frm) {
		console.log("customer")
		console.log(frm.doc.customer)		
		
		console.log("customer default price list")
		frappe.call(
			{
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Customer',
					'filters': { 'customer_name': frm.doc.customer },
					'fieldname': ['default_price_list','customer_name']
				},
				callback: (r) => {
					if (r.message.default_price_list) {
						frm.doc.price_list = r.message.default_price_list;
					}

					frm.refresh_field("price_list");
				}
			});

			frm.doc.customer_display_name = frm.doc.customer_name
			frm.refresh_field("customer_display_name");

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
	credit_sale(frm) {
		
		frm.set_df_property("credit_days", "hidden", !frm.doc.credit_sale);
		frm.set_df_property("payment_mode", "hidden", frm.doc.credit_sale);
		frm.set_df_property("payment_account", "hidden", frm.doc.credit_sale);
		frm.set_df_property("payment_mode", "mandatory", !frm.doc.credit_sale);
		

		if (frm.doc.credit_sale) {
			frm.doc.payment_mode = "";
			frm.doc.payment_account = "";
		}
		
	},
	warehouse(frm) {
		console.log("warehouse set")
		console.log(frm.doc.warehouse)
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
	make_taxes_and_totals(frm) {
		console.log("from make totals..")
		frm.clear_table("taxes");
		frm.refresh_field("taxes");

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

			//rate_included_tax column in items table is readonly and it depends the form's rate_includes_tax column
			entry.rate_included_tax = frm.doc.rate_includes_tax;
			entry.gross_amount = 0
			entry.tax_amount = 0;
			entry.net_amount = 0
			//To avoid complexity mentioned below, rate_includedd_tax option do not support with line item discount

			if (entry.rate_included_tax) //Disclaimer - since tax is calculated after discounted amount. this implementation 
			{							// has a mismatch with it. But still it approves to avoid complexity for the customer
				// also this implementation is streight forward than the other way										
				tax_in_rate = entry.rate * (entry.tax_rate / (100 + entry.tax_rate));
				entry.rate_excluded_tax = entry.rate - tax_in_rate;
				entry.tax_amount = (entry.qty * entry.rate) * (entry.tax_rate / (100 + entry.tax_rate))
				console.log("Tax Rate %f", entry.tax_rate);
				console.log("Tax Amount %f", entry.tax_amount);
				entry.net_amount = ((entry.qty * entry.rate) - entry.discount_amount);
				entry.gross_amount = entry.net_amount - entry.tax_amount;
			}
			else {
				entry.rate_excluded_tax = entry.rate;
				entry.tax_amount = (((entry.qty * entry.rate) - entry.discount_amount) * (entry.tax_rate / 100))
				entry.net_amount = ((entry.qty * entry.rate) - entry.discount_amount)
					+ (((entry.qty * entry.rate) - entry.discount_amount) * (entry.tax_rate / 100))


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

							if(uomqty == entry.qty_in_base_unit)
							{
								uomqty2 = uomqty + " " + unit + " @ " + uomrate
							}
							else
							{
								if (uomqty > Math.trunc(uomqty)) {	
									var excessqty = Math.round((uomqty - Math.trunc(uomqty)) * conversion, 0);
									uomqty2 = uomqty + " " + unit + "(" + Math.trunc(uomqty) + " " + unit + " " + excessqty + " " + entry.base_unit + ")" + " @ " + uomrate;
								}
								else
								{
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
							'fieldname': ['default_warehouse', 'rate_includes_tax', 'delivery_note_integrated_with_sales_invoice']
						},
						callback: (r2) => {
							console.log("Before assign default warehouse");
							console.log(r2.message.default_warehouse);
							frm.doc.warehouse = r2.message.default_warehouse;
							console.log(frm.doc.warehouse);
							frm.doc.rate_includes_tax = r2.message.rate_includes_tax;
							frm.doc.auto_save_delivery_note = r2.message.delivery_note_integrated_with_sales_invoice;
							frm.refresh_field("warehouse");
							frm.refresh_field("rate_includes_tax");
							console.log(r2.message);
							frm.refresh_field("auto_save_delivery_note");							

							//Have a button to create delivery note in case delivery note is not integrated with SI
							if (!frm.doc.__islocal && !r2.message.delivery_note_integrated_with_sales_invoice) {
								frm.add_custom_button('Create/Update Delivery Note', () => {
									frm.call("auto_generate_delivery_note")
								},
								)
							}

							if (frm.doc.__islocal) {
								frm.add_custom_button('Get Items from Delivery Notes', () => {
									// Commented for correction
									// frm.trigger("get_items_from_delivery_notes");
								},
								)
							}

						}
					}
				)
			}
		})

	}	
});

frappe.ui.form.on("Sales Invoice", "onload", function (frm) {

	//Since the default selectionis cash
	//frm.set_df_property("date","read_only",1);	
	// frm.set_query("warehouse", function () {
	// 	return {
	// 		"filters": {
	// 			"is_group": 0
	// 		}
	// 	};
	// });
	
	console.log(frm.doc);
	
	if(frm.doc.__islocal)
		frm.trigger("get_default_company_and_warehouse");

	frm.set_query("price_list", function () {
		return {
			"filters": {
				"is_selling": 1
			}
		};
	});

	frm.set_query("customer", function () {
		return {
			"filters": {
				"is_disabled": 0
			}
		};
	});	

});

frappe.ui.form.on('Sales Invoice Item', {
	item(frm, cdt, cdn) {

		let row = frappe.get_doc(cdt, cdn);
		console.log(frm.doc.customer);
		console.log(typeof (frm.doc.customer));

		if (typeof (frm.doc.customer) == "undefined") {
			frappe.msgprint("Select customer.")
			row.item = "";
			return;
		}

		console.log(row.item);
		console.log(row.qty);
		let doc = frappe.model.get_value("", row.item);
		console.log(doc);
		row.warehouse = frm.doc.warehouse;
		console.log(row.warehouse);
		frm.trigger("make_taxes_and_totals");

		frappe.call(
			{
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Item',
					'filters': { 'item_name': row.item },
					'fieldname': ['item_code', 'base_unit', 'tax', 'tax_excluded']
				},
				callback: (r) => {
					console.log('Item Code');
					console.log(r.message.item_code);
					console.log(r.message.base_unit);
					console.log(r.message.tax);
					console.log(r.message.tax_excluded);
					row.item_code = r.message.item_code;
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

					var applyStandrPricing = false;

					if (frm.doc.price_list != "Standard Buying") {
						frappe.call(
							{
								method: 'digitz_erp.api.items_api.get_item_price_for_price_list',
								async: false,

								args: {
									'item': row.item,
									'price_list': frm.doc.price_list
								},
								callback(r) {
									if (r.message.length == 1) {
										console.log(r.message[0].price);
										row.rate = r.message[0].price;
										row.rate_in_base_unit = r.message[0].price;
									}
									else {
										applyStandrPricing = true;
									}
								}
							});
					}
					else {
						applyStandrPricing = true;
					}

					if (applyStandrPricing) {
						frappe.call(
							{
								method: 'digitz_erp.api.items_api.get_item_price_for_price_list',
								async: false,

								args: {
									'item': row.item,
									'price_list': 'Standard Selling'
								},
								callback(r) {
									if (r.message.length == 1) {
										console.log(r.message[0].price);
										row.rate = r.message[0].price;
										row.rate_in_base_unit = r.message[0].price;
									}
									else {
										applyStandrPricing = true;
									}
								}
							});
					}

					frm.refresh_field("items");
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
	rate_included_tax(frm, cdt, cdn) {
		frm.trigger("make_taxes_and_totals");
	},
	unit(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		
		console.log("row before get_item_uom")
		console.log(row.item)
	
		// frappe.call(
		// 	{
		// 		method: 'digitz_erp.api.items_api.get_item_uom',
		// 		async: false,
		// 		args: {
		// 			item: row.item,
		// 			unit: row.unit
		// 		},
		// 		callback(r) {
		// 			if (r.message.length == 0) {
		// 				frappe.msgprint("Invalid unit, Unit does not exists for the item.");
		// 				row.unit = row.base_unit;
		// 				row.conversion_factor = 1;
		// 			}
		// 			else {
		// 				console.log(r.message[0].conversion_factor);
		// 				row.conversion_factor = r.message[0].conversion_factor;
		// 				//row.rate = row.rate * row.conversion_factor;							
		// 				//frappe.confirm('Rate converted for the unit selected. Do you want to convert the qty as well ?',
		// 				//() => {
		// 				//row.qty = row.qty/ row.conversion_factor;								
		// 				//})	
		// 			}
		// 			frm.trigger("make_taxes_and_totals");

		// 			frm.refresh_field("items");
		// 		}

		// 	}
		// );
	},
	discount_percentage(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		console.log("from discount_percentage")
		console.log("Gross Amount %f", row.gross_amount);

		var discount_percentage = row.discount_percentage;	

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
	}
});