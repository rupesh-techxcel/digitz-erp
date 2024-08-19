// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Order', {
	refresh: function(frm) {
		
		var pending_items_exists = false

		if(frm.doc.docstatus == 1)
		{
			frappe.call(
			{
				method: 'digitz_erp.api.sales_order_api.check_pending_items_exists',
				async: false,
				args: {
					'sales_order': frm.doc.name
				},
				callback(r) {

					if (r.message)
					{
						pending_items_exists = true
					}
				}
			});

			if(pending_items_exists)
			{

				allow_delivery_note_creation = false
				allow_sales_invoice_creation = false

				frappe.call(
					{
						method: 'digitz_erp.api.sales_restriction_rules_api.do_not_allow_multiple_doctype_creation',
						async: false,
						args: {
							'sales_order': frm.doc.name
						},
						callback(r) {
		
							console.log("from do_not_allow_multiple_doctype_creation");
							// Sales Invoice can be created only if sales order does not exist in Delivery Note
							allow_sales_invoice_creation  = !r.message.exists_in_delivery_note
							// Delivery Note can be created only if Sales Order does not exist in Sales Invoice
							allow_delivery_note_creation= !r.message.exists_in_sales_invoice
						}
					});
				
				console.log(allow_delivery_note_creation)
				console.log(allow_sales_invoice_creation)

				if (allow_delivery_note_creation == true)
				{
					console.log("here")
					frm.add_custom_button('Create Delivery Note', () => {
						frm.call({
						method: 'digitz_erp.selling.doctype.sales_order.sales_order.generate_do',					
						args: {
							sales_order_name: frm.doc.name
						},
						callback: function(r)
						{
							frm.reload_doc();
							if(r.message){
								frappe.set_route('Form', 'Delivery Note', r.message);
							}
						}

					})});
				}	

				if (allow_sales_invoice_creation== true)
				{
					frm.add_custom_button('Create Sales Invoice', () => {
						frm.call({
						method: 'digitz_erp.selling.doctype.sales_order.sales_order.generate_sales_invoice',					
						args: {
							sales_order_name: frm.doc.name
						},
						callback: function(r)
						{
							frm.reload_doc();
							if(r.message){
								frappe.set_route('Form', 'Sales Invoice', r.message);
							}
						}
	
					})});
				}
				
			}
		}

		if (!frm.is_new()) {
			frm.add_custom_button(__('Duplicate'), function() {
				// Call the method directly on the server-side document instance
				frm.call({
					method: "generate_sales_order",
					doc: frm.doc,
					callback: function(r) {
						if (!r.exc) {
							// Navigate to the new duplicated invoice
							frappe.set_route("Form", "Sales Order", r.message);
							frappe.show_alert({
								message: __("New Sales Order " + r.message + " has been opened."),
								indicator: 'green'
							});
						}
					}
				});
			} );
		}

		update_total_big_display(frm);
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
					"disabled": 0
				}
			};
		});

		frm.set_query("warehouse", function() {
			return {
				"filters": {
					"disabled": 0
				}
			};
		});

		frm.set_query("salesman", function() {
			return {
				"filters": {
					"disabled": 0,
					"status": ["!=", "On Boarding"]
				}
			};
		});

		frm.fields_dict['items'].grid.get_field('warehouse').get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    disabled: 0
                }
            };
		}
	},
	customer(frm) {
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
		console.log("customer")
		console.log(frm.doc.customer)

		console.log("customer default price list")
		frappe.call(
			{
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Customer',
					'filters': { 'customer_name': frm.doc.customer },
					'fieldname': ['default_price_list']
				},
				callback: (r) => {
					if (r.message.default_price_list) {
						frm.doc.price_list = r.message.default_price_list;
					}

					frm.refresh_field("price_list");
				}
			});

		frm.set_value('customer_display_name', frm.doc.customer_name)
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

			set_default_payment_mode(frm)
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
	credit_sale(frm) {
		console.log("credit_sale")
		set_default_payment_mode(frm);
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

		if(frm.doc.item_table.length>0){
			update_total_big_display_1(frm);
			frm.set_df_property("items","read_only",1)
		}
		else{
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
			if(entry.lumpsum_amount){
					gross_total += entry.gross_amount;entry.tax_amount;
					tax_total += entry.tax_amount;
					net_total += entry.net_amount + entry.tax_amount;
			}
			else
			{
			console.log("entry")
			console.log(entry);
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

		update_total_big_display(frm);
	}
	},
	get_item_stock_balance(frm) {

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
					console.log("frm.unit")
					console.log(frm.unit)
					if (r2 && r2.message && r2.message.stock_qty !== undefined)
					{
						frm.doc.selected_item_stock_qty_in_the_warehouse = "Stock Bal: "  + r2.message.stock_qty + " "+ frm.unit +  " for " + frm.item + " at w/h: "+ frm.warehouse + ": "
						frm.refresh_field("selected_item_stock_qty_in_the_warehouse");
					}

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
							frm.doc.rate_includes_tax = r2.message.rate_includes_tax;
							frm.refresh_field("warehouse");
							frm.refresh_field("rate_includes_tax");
						}
					}

				)
			}
		})

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

		// if (!valid) {
		// 	frappe.msgprint("No valid item found in the document");
		// 	return;
		// }
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
	}
});

function update_total_big_display(frm) {

	let netTotal = isNaN(frm.doc.net_total) ? 0 : parseFloat(frm.doc.net_total).toFixed(2);

    // Add 'AED' prefix and format net_total for display

	let displayHtml = `<div style="font-size: 25px; text-align: right; color: black;">AED ${netTotal}</div>`;


    // Directly update the HTML content of the 'total_big' field
    frm.fields_dict['total_big'].$wrapper.html(displayHtml);

}

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
	else
	{
		frm.set_value('payment_mode', "");
	}

	frm.set_df_property("credit_days", "hidden", !frm.doc.credit_sale);
	frm.set_df_property("payment_mode", "hidden", frm.doc.credit_sale);
	frm.set_df_property("payment_account", "hidden", frm.doc.credit_sale);
}

frappe.ui.form.on("Sales Order", "onload", function (frm) {

	frm.trigger("assign_defaults")

});

frappe.ui.form.on('Sales Order Item', {

	item(frm, cdt, cdn) {

		let row = frappe.get_doc(cdt, cdn);

		if (typeof (frm.doc.customer) == "undefined") {
			frappe.msgprint("Select customer.")
			row.item = "";
			return;
		}

		let doc = frappe.model.get_value("", row.item);

		row.warehouse = frm.doc.warehouse;

		frm.item = row.item
		frm.trigger("get_item_units");
		// frm.trigger("make_taxes_and_totals");

		let tax_excluded_for_company = false
		frappe.call(
			{
				method:'digitz_erp.api.settings_api.get_company_settings',
				async:false,
				callback(r){
					console.log("digitz_erp.api.settings_api.get_company_settings")
					console.log(r)
					tax_excluded_for_company = r.message[0].tax_excluded
				}
			}
		);

		console.log("tax_excluded_for_company")
		console.log(tax_excluded_for_company)

		frappe.call(
			{
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Item',
					'filters': { 'item_code': row.item },
					'fieldname': ['item_name', 'base_unit', 'tax', 'tax_excluded']
				},
				callback: (r) => {
					console.log("item")
					console.log(r)
					row.item_name = r.message.item_name;
					row.display_name = r.message.item_name;
					//row.uom = r.message.base_unit;
					if(tax_excluded_for_company)
					{
						row.tax_excluded = true;
						console.log("tax excluded assinged in")
					}
					else
					{
						row.tax_excluded = r.message.tax_excluded;
					}

					console.log("tax excluded?")
					console.log(row.tax_excluded)
					row.base_unit = r.message.base_unit;
					row.unit = r.message.base_unit;
					row.conversion_factor = 1;

					frm.item = row.item;
					frm.warehouse = row.warehouse
					frm.unit = row.base_unit

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

					var currency = ""
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

					var use_customer_last_price =0 ;
					console.log("before call digitz_erp.api.settings_api.get_company_settings")

					frappe.call(
						{
							method:'digitz_erp.api.settings_api.get_company_settings',
							async:false,
							callback(r){
								console.log("digitz_erp.api.settings_api.get_company_settings")
								console.log(r)
								use_customer_last_price = r.message[0].use_customer_last_price
								console.log("use_customer_last_price")
								console.log(use_customer_last_price)
							}
						}
					);

					console.log("use customer last price")
					console.log(use_customer_last_price)

					var use_price_list_price = 1
					if(use_customer_last_price == 1)
					{
						console.log("before call digitz_erp.api.item_price_api.get_customer_last_price_for_item")
						frappe.call(
							{
								method:'digitz_erp.api.item_price_api.get_customer_last_price_for_item',
								args:{
									'item': row.item,
									'customer': frm.doc.customer
								},
								async:false,
								callback(r){

									console.log("digitz_erp.api.item_price_api.get_customer_last_price_for_item")
									console.log(r)

									if (r.message !== undefined && r.message.length > 0) {
										// Assuming r.message is an array, you might want to handle this differently based on your actual response
										row.rate = parseFloat(r.message[0]);
										row.rate_in_base_unit = parseFloat(r.message[0]);
									}
									else if (r.message!= undefined) {
										row.rate = parseFloat(r.message)
										row.rate_in_base_unit = parseFloat(r.message)
									}

									console.log("customer last price")
									console.log(row.rate)

									if(r.message != undefined && r.message > 0 )
									{
										use_price_list_price = 0
									}
								}
							}
						);
					}

					if(use_price_list_price ==1)
					{
						console.log("digitz_erp.api.item_price_api.get_item_price")
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
									// row.rate = r.message;
									// row.rate_in_base_unit = r.message;

									if (r.message !== undefined && r.message.length > 0) {
										// Assuming r.message is an array, you might want to handle this differently based on your actual response
										row.rate = r.message[0];
										row.rate_in_base_unit = r.message[0];
									}
									else if (r.message!= undefined) {
										row.rate = parseFloat(r.message)
										row.rate_in_base_unit = parseFloat(r.message)
									}
								}
							});
					}
					frm.trigger("make_taxes_and_totals");
					frm.refresh_field("items");
				}
			});
	},
	tax_excluded(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);

		if (row.tax_excluded) {
			row.tax = "";
			row.tax_rate = 0;
			row.tax_amount = 0;
			frm.refresh_field("items");
			frm.trigger("make_taxes_and_totals");
		}
		update_row(frm,cdt,cdn);
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
						update_row(frm,cdt,cdn);
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

		console.log("Item");
		console.log(row.item);

		//  frappe.call(
		//  	{
		//  		method:'frappe.client.get_valuelist',
		//  		args:{
		//  		'doctype':'Item Unit',
		//  		'filters':{'parent': row.item},
		//  		'fieldname':['unit','conversion_factor']
		//  		},
		//  		callback:(r2)=>
		//  		{
		//  			console.log(r2.message);
		//  		}
		//  	});

		console.log(row.item);

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
	},
	tax_rate(frm,cdt,cdn){
		update_row(frm,cdt,cdn);
	},
	gross_amount(frm,cdt,cdn){
		// update_amount_with_lumpsum(frm,cdt,cdn);
		update_row(frm,cdt,cdn);
	},
	lumpsum_amount(frm,cdt,cdn){
		update_row(frm,cdt,cdn);
	},


});


function update_row(frm,cdt,cdn){
	let row = frappe.get_doc(cdt,cdn);

	if(row.lumpsum_amount){
		let tax_amount = row.gross_amount * row.tax_rate/100;

		frappe.model.set_value(cdt,cdn,'tax_amount', tax_amount);
		frappe.model.set_value(cdt,cdn,'qty', 0);
		frappe.model.set_value(cdt,cdn,'net_amount', row.gross_amount + tax_amount); 
		frm.trigger("make_taxes_and_totals");
	}
	
}


frappe.ui.form.on('Sales Order New Item Details', {
    qty: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.qty && row.rate) {
            let amt = row.qty * row.rate;
            frappe.model.set_value(cdt, cdn, 'amount', amt);
			update_total_big_display_1(frm)
        }
    },
    rate: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.qty && row.rate) {
            let amt = row.qty * row.rate;
            frappe.model.set_value(cdt, cdn, 'amount', amt);
			update_total_big_display_1(frm)
        }
    },
});




































frappe.ui.form.on("Sales Order",{
    refresh: function(frm){
        let displayHtml = `<div style="font-size: 25px; text-align: right; color: black;">AED ${frm.doc.net_total}</div>`;
		frm.fields_dict['total_big'].$wrapper.html(displayHtml);

		// if(frm.doc.items.length > 0){
		// }

		if(frm.doc.item_table.length > 0){
			update_total_big_display_1(frm);
		}else{
			update_total_big_display(frm);
		}

		

		if(frm.doc.quotation_id){
			frm.set_df_property('item_table','hidden',0)
		}

        if(!frm.is_new()){
            frm.add_custom_button(__('Create Project'), function() {
                
				frappe.new_doc("Project", {
					"customer":frm.doc.customer,
					"project_amount": frm.doc.net_amount,
					"sales_order":frm.doc.name
				});
				
            },__("Project Actions"));

            frm.add_custom_button(__('Show Created Project'), function() {
                // Redirect to BOQ list view with filters applied
                frappe.set_route('List', 'Project', {'sales_order' : frm.doc.name} );
            },__("Project Actions"));

			frm.add_custom_button(__("Create Progress Entry"), function(){
				frappe.new_doc("Progress Entry",{}, pe =>{
					pe.customer = frm.doc.customer;
					pe.company = frm.doc.company;
					pe.project = frm.doc.project;
					pe.warehouse = frm.doc.warehouse;
					pe.sales_order_id = frm.doc.name;

					frm.doc.items.forEach(item =>{
						let row =  frappe.model.add_child(pe, 'progress_entry_items');

						for(i in item){
							row[i] = item[i]
						}
					})

					pe.gross_total = frm.doc.gross_total;
					pe.net_total = frm.doc.net_total;
					pe.tax_total = frm.doc.tax_total;

					pe.total_discount_in_line_items = frm.doc.total_discount_in_line_items;
					pe.additional_discount = frm.doc.additional_discount;
					pe.rounded_total = frm.doc.rounded_total;
					pe.in_words = frm.doc.in_words;
					let displayHtml = `<div style="font-size: 25px; text-align: right; color: black;">AED ${pe.net_total}</div>`;
					pe.total_big = displayHtml;
				})
			},__("Progress Entry"));

			
			frm.add_custom_button(__("Show Created Progress Entry"), function(){
				frappe.set_route('List', 'Progress Entry', { 'sales_order_id': frm.doc.name });
			},__("Progress Entry"));
        }
    },
    // make_taxes_and_total(frm){
	// 	if(frm.doc.item_table.length>0){
	// 		update_total_big_display_1(frm);
	// 	}else{
	// 		// make_taxes_and_totals(frm);
	// 	}

    // },
    setup: function(frm){
        let data = localStorage.getItem('sales_order_data');
			frm.trigger("get_default_company_and_warehouse").then(()=>{
	
				if (data) {
					data = JSON.parse(data);
					data = data[0]
					console.log("sales_order_data",data)
					// Set the fields with the retrieved data
					frm.set_value('customer', data.customer);
                    frm.set_value('quotation_id', data.name);
					// if(data['items'] && data['items'].length > 0){
						// frm.set_df_property('items','hidden',0)

						
						data["items"].forEach(item => {
							let row = frm.add_child('items');
	
							for(let key in item){
								row[key] = item[key]
							}
						});
					// }else{
						// frm.set_df_property('item_table','hidden',1)
					// }
                    // if(data['item_table'] && data['item_table'].length > 0){
						// frm.set_df_property('items','hidden',0)
						data["item_table"].forEach(item =>{
							let row = frm.add_child('item_table');
	
							for(let key in item){
								row[key] = item[key]
							}
						})
					// }else{
					// 	frm.set_df_property('item_table','hidden',1)
					// }
				frm.refresh_field('items');
                frm.refresh_field('item_table');
				// Call other_fields_orcustom function
				// frappe.ui.form.trigger('Quotation', 'rate_includes_tax', frm);
				
				// Refresh the field to show the added rows
				frm.refresh_field('items');
                frm.refresh_field('item_table');
				if(frm.doc.item_table && frm.doc.item_table.length > 0){
					update_total_big_display_1(frm)
				}
				// Clear the data from localStorage
				localStorage.removeItem('sales_order_data');
				console.log("removed data",localStorage.getItem('sales_order_data'))
                frm.trigger("make_taxes_and_totals");
			}
		})
    },
    
})


function update_total_big_display_1(frm) {

	// let netTotal = isNaN(frm.doc.net_total) ? 0 : parseFloat(frm.doc.net_total).toFixed(2);
	let netTotal=0;
	frm.doc.item_table.forEach((e)=>{
			netTotal+= e.amount;
	})
    netTotal = netTotal.toFixed(2);
	
    // Add 'AED' prefix and format net_total for display
	
    frm.set_value("net_total",netTotal)
	frm.set_value("gross_total",netTotal)

	let displayHtml = `<div style="font-size: 25px; text-align: right; color: black;">AED ${netTotal}</div>`;


    // Directly update the HTML content of the 'total_big' field
    frm.set_value("total_big",displayHtml)
	frm.fields_dict['total_big'].$wrapper.html(displayHtml);

}