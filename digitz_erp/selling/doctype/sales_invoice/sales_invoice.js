// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice', {

	 refresh: function (frm) {
		 create_custom_buttons(frm);
	
		 if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Get Items From Delivery Note'), function () {
						delivery_note_dialog(frm)
					});
			}

		if(frm.doc.docstatus == 1 && frm.doc.update_stock == false)
		{
			frm.add_custom_button('Create Delivery Note', () => {
				frm.call("generate_delivery_note")
			})
		}


		// if(!frm.is_new()){
		// 	frm.add_custom_button('Sales Return', () =>{
		// 		frappe.model.open_mapped_doc({
	    //     method: 'digitz_erp.selling.doctype.sales_invoice.sales_invoice.create_sales_return',
		// 			frm: cur_frm
	    //   });
		// 	})
		// }
	 },
	 setup: function (frm) {

		frm.add_fetch('customer', 'full_address', 'customer_address')
		frm.add_fetch('customer', 'salesman', 'salesman')
		frm.add_fetch('customer', 'tax_id', 'tax_id')
		frm.add_fetch('customer', 'credit_days', 'credit_days')
		frm.add_fetch('payment_mode', 'account', 'payment_account')

		frm.set_query("warehouse", function() {
			return {
				"filters": {
					"is_disabled": 0
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
					"is_disabled": 0
				}
			};
		});

		frm.fields_dict['items'].grid.get_field('warehouse').get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    is_disabled: 0
                }
            };
		}

		frm.set_query("ship_to_location", function () {
			return {
				"filters": {
					"parent": frm.doc.customer
				}
			};
		});
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
	after_save: function (frm) {

		 if (frm.doc.auto_save_delivery_note) {
			// frm.call("auto_generate_delivery_note")
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
			frm.set_df_property("payment_account", "hidden", frm.doc.credit_sale);
			frm.refresh_field("payment_account");
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

		if (frm.doc.tab_sales)
			frappe.throw("Cannot change Sales Invoice created from a Tab Sales. Do it from the correspodning Tab Sale")

		if(frm.doc.__islocal) //When the invoice is created by duplicating from an existing invoice, there may be delivery notes allocated
		{					// and it needs to be removed
			if(frm.doc.delivery_notes)
			{
					frm.doc.delivery_notes = undefined;
			}
		}
	},
	
	customer(frm) {

		frappe.call(
			{
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Customer',
					'filters': { 'customer_name': frm.doc.customer_name },
					'fieldname': ['default_price_list','customer_name']
				},
				callback: (r) => {

					console.log("r.message.default_price_list")
					console.log(r.message.default_price_list)

					if (r.message.default_price_list) {
						frm.doc.price_list = r.message.default_price_list;
					}

					frm.refresh_field("price_list");
					console.log("frm.doc.price_list")
					console.log(frm.doc.price_list)
				}
			});

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

			frm.doc.customer_display_name = frm.doc.customer_name
			frm.refresh_field("customer_display_name");

		frappe.call(
			{
				method:'digitz_erp.api.settings_api.get_customer_terms',
				args:{
					'customer': frm.doc.customer
				},
				callback(r){
					console.log(r.message)
					if(r.message && typeof(r.message.template_name)!= undefined && r.message.template_name)
					{
						frm.doc.terms = r.message.template_name;
						frm.refresh_field("terms");
					}
					if( r.message && typeof(r.message.terms != undefined) && r.message.terms )
					{
						frm.doc.terms_and_conditions = r.message.terms
						frm.refresh_field("terms_and_conditions");
					}


				}
			}
		);

		fill_receipt_schedule(frm);
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
	credit_sale(frm) {

		set_default_payment_mode(frm);

		fill_receipt_schedule(frm,refresh= true)
	},
	credit_days(frm)
	{
		fill_receipt_schedule(frm,refresh_credit_days= true);
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
			console.log("tax_total")
			console.log(tax_total)
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

						var units = r.message;
						var output = "";
						var output2 = "";
						entry.unit_conversion_details = "";
						$.each(units, (a, b) => {

							var conversion = b.conversion_factor
							var unit = b.unit

							var uomqty = entry.qty_in_base_unit / conversion;

							var uomrate = entry.rate_in_base_unit * conversion;

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
						entry.unit_conversion_details = output
					}
				}

				)
			}
			else {

			}

		});

		if (isNaN(frm.doc.additional_discount)) {
			frm.doc.additional_discount = 0;
		}

		frm.doc.gross_total = gross_total;
		frm.doc.net_total = gross_total + tax_total - frm.doc.additional_discount;

		console.log("frm.doc.additional discount")
		console.log(frm.doc.additional_discount)

		console.log("gross total")
		console.log(gross_total)

		console.log("tax total")
		console.log(tax_total)

		console.log("frm.doc.net_total")
		console.log(frm.doc.net_total)

		frm.doc.tax_total = tax_total;
		frm.doc.total_discount_in_line_items = discount_total;

		frappe.db.get_value('Company', frm.doc.company, 'do_not_apply_round_off_in_si', function(data) {
			console.log("Value of do_not_apply_round_off_in_si:", data.do_not_apply_round_off_in_si);
			if (data && data.do_not_apply_round_off_in_si == 1) {
				frm.doc.rounded_total = frm.doc.net_total;
				frm.refresh_field('rounded_total');
				console.log("here 1")
			}
			else {
			 if (frm.doc.net_total != Math.round(frm.doc.net_total)) {
				 frm.doc.round_off = Math.round(frm.doc.net_total) - frm.doc.net_total;
				 frm.doc.rounded_total = Math.round(frm.doc.net_total);
				 frm.refresh_field('round_off');
				 frm.refresh_field('rounded_total');
				 console.log("here 2")
			 }
			 else{

				console.log("here 3-----")
				frm.doc.rounded_total = frm.doc.net_total;
				frm.refresh_field("rounded_total");

				console.log(frm.doc.net_total)
				console.log(frm.doc.rounded_total)
			 }
		 }
		});

		fill_receipt_schedule(frm);

		frm.refresh_field("items");
		frm.refresh_field("taxes");

		frm.refresh_field("gross_total");
		frm.refresh_field("net_total");
		frm.refresh_field("tax_total");
		frm.refresh_field("round_off");
		frm.refresh_field("rounded_total");

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
							'fieldname': ['default_warehouse', 'rate_includes_tax', 'delivery_note_integrated_with_sales_invoice','update_price_list_price_with_sales_invoice','use_customer_last_price','customer_terms','update_stock_in_sales_invoice']
						},
						callback: (r2) => {

							frm.doc.warehouse = r2.message.default_warehouse;

							frm.doc.rate_includes_tax = r2.message.rate_includes_tax;

							frm.doc.update_stock = r2.message.update_stock_in_sales_invoice

							// frm.doc.auto_save_delivery_note = r2.message.delivery_note_integrated_with_sales_invoice;
							frm.doc.auto_save_delivery_note = false

							if(r2.message.use_customer_last_price  == 0)
							{
								frm.doc.update_rates_in_price_list = r2.message.update_price_list_price_with_sales_invoice;
							}

							frm.refresh_field("warehouse");
							frm.refresh_field("rate_includes_tax");
							frm.refresh_field("update_rates_in_price_list");

							frm.refresh_field("auto_save_delivery_note");
							frm.refresh_field("update_stock");

							//Have a button to create delivery note in case delivery note is not integrated with SI
							// if (!frm.doc.__islocal && !r2.message.delivery_note_integrated_with_sales_invoice) {
							// 	frm.add_custom_button('Create/Update Delivery Note', () => {
							// 		frm.call("auto_generate_delivery_note")
							// 	},
							// 	)
							// }

							if(r2.message.customer_terms)
							{
								frm.doc.terms = r2.message.customer_terms
								frm.refresh_field("terms");

								frappe.call(
									{
										method:'digitz_erp.api.settings_api.get_terms_for_template',
										args:{
											'template': r2.message.customer_terms
										},
										callback(r){

											frm.doc.terms_and_conditions = r.message.terms
											frm.refresh_field("terms_and_conditions");
										}
									});
							}



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
});

function fill_receipt_schedule(frm, refresh=false,refresh_credit_days=false)
{

	if(refresh)
	{
		frm.doc.receipt_schedule = [];
		refresh_field("receipt_schedule");
	}

	console.log("fill_receipt_schedule")

	if (frm.doc.credit_sale) {


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
			receiptRow.amount = roundedTotal;
			refresh_field("receipt_schedule");
		}
		else if (row_count==1)
		{
			//If there is only one row update the amount. If there is more than one row that means there is manual
			//entry and	user need to manage it by themself
			receiptRow.payment_mode = "Cash"
			receiptRow.amount = roundedTotal;
			refresh_field("receipt_schedule");
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

frappe.ui.form.on("Sales Invoice", "onload", function (frm) {

	frm.trigger("assign_defaults")	
	fill_receipt_schedule(frm);

});

frappe.ui.form.on('Sales Invoice Item', {
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

					row.base_unit = r.message.base_unit;
					row.unit = r.message.base_unit;
					row.conversion_factor = 1;

					frm.item = row.item;
					frm.warehouse = row.warehouse

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

		var discount_percentage = row.discount_percentage;

		if (row.discount_percentage > 0) {

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

		let row = frappe.get_doc(cdt, cdn);
		row.warehouse = frm.doc.warehouse

		frm.trigger("make_taxes_and_totals");

	},
	items_remove(frm, cdt, cdn) {
		frm.trigger("make_taxes_and_totals");
	}
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



let delivery_note_dialog = function (frm) {
    let d = new frappe.ui.Dialog({
        title: 'Select Delivery Notes',
        fields: [{
            label: 'Delivery Note Details',
            fieldname: 'delivery_note_details',
            fieldtype: 'Table',
            fields: [{
                label: 'Delivery Note',
                fieldtype: 'Link',
                options: 'Delivery Note',
                fieldname: 'delivery_note',
                in_list_view: 1,
                get_query: function(doc) {
                    const customer = frm.doc.customer;
                    if (customer) {
                        return {
                            filters: {
                                "customer": customer
                            }
                        };
                    }
                }
            }]
        }],
        primary_action_label: 'Submit',
        primary_action(values) {
            const selectedDeliveryNotes = values.delivery_note_details.map(row => row.delivery_note);
            frappe.call({
                method: 'digitz_erp.selling.doctype.sales_invoice.sales_invoice.get_delivery_note_items',
                args: { delivery_notes: selectedDeliveryNotes },
                callback: function(response) {
                    const items = response.message;
                    items.forEach(item => {
                        frm.add_child('items', {
                            item: item.item,
                            item_name: item.item_name,
                            qty: item.qty,
                            warehouse: item.warehouse,
                            display_name: item.display_name,
                            unit: item.unit,
                            rate: item.rate,
                            base_unit: item.base_unit,
                            qty_in_base_unit: item.qty_in_base_unit,
                            rate_in_base_unit: item.rate_in_base_unit,
                            conversion_factor: item.conversion_factor,
                            rate_includes_tax: item.rate_includes_tax,
                            tax_excluded: item.tax_excluded,
                            tax_rate: item.tax_rate,
                            tax_amount: item.tax_amount,
                            discount_percentage: item.discount_percentage,
                            discount_amount: item.discount_amount,
                            net_amount: item.net_amount,
                            delivery_note_item_reference_no: item.delivery_note_item_reference_no
                        });
                    });
                    frm.refresh_field('items');
                }
            });
            d.hide();
        }
    });

    d.show();
}


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
