// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Invoice', {

	setup: function (frm) {

		frm.add_fetch('supplier', 'tax_id', 'tax_id')
		frm.add_fetch('supplier', 'credit_days', 'credit_days')
		frm.add_fetch('supplier', 'full_address', 'supplier_address')
		frm.add_fetch('supplier', 'tax_id', 'tax_id')
		frm.add_fetch('payment_mode', 'account', 'payment_account')
		//frm.get_field('taxes').grid.cannot_add_rows = true;

	},
	refresh:function (frm) {
		if(!frm.is_new()){
			frm.add_custom_button('Purchase Return', () =>{
				frappe.model.open_mapped_doc({
	        method: 'digitz_erp.buying.doctype.purchase_invoice.purchase_invoice.create_purchase_return',
					frm: cur_frm
	      });
			})
		}
	},
	validate:function(frm){

		if(!frm.doc.credit_purchase)
		{
			if(!frm.doc.payment_mode)
			{
				frappe.throw("Please select payment mode")
			}
		}
	},
	supplier(frm) {
		console.log("supplier")
		console.log(frm.doc.supplier)

		console.log("supplier default price list")
		frappe.call(
			{
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Supplier',
					'filters': { 'supplier_name': frm.doc.supplier },
					'fieldname': ['default_price_list']
				},
				callback: (r) => {
					console.log(r.message.default_price_list);

					frm.doc.price_list = r.message.default_price_list;
					frm.refresh_field("price_list");
				}
			});
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
	credit_purchase(frm) {
		frm.set_df_property("credit_days", "hidden", !frm.doc.credit_purchase);
		frm.set_df_property("payment_mode", "hidden", frm.doc.credit_purchase);
		frm.set_df_property("payment_account", "hidden", frm.doc.credit_purchase);

		if (frm.doc.credit_purchase) {
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

				console.log("get_item_uoms")

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
	get_user_warehouse(frm)
	{
		frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'User Warehouse',
                filters: {
                    user: frappe.session.user
                },
                fieldname: 'warehouse'
            },
            callback: function(response) {
				if (response && response.message && response.message.warehouse) {
					window.warehouse = response.message.warehouse;					
					// Do something with warehouseValue
				}
			}
		});
	},
	get_default_company_and_warehouse(frm) {
		var default_company = ""
		console.log("From Get Default Warehouse Method in the parent form")
		frm.trigger("get_user_warehouse")

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
							'fieldname': ['default_warehouse', 'rate_includes_tax','update_price_list_price_with_purchase_invoice','use_supplier_last_price']
						},
						callback: (r2) => {


							if (typeof window.warehouse !== 'undefined') {
								// The value is assigned to window.warehouse
								// You can use it here
								frm.doc.warehouse = window.warehouse;
							}
							else
							{
								frm.doc.warehouse = r2.message.default_warehouse;
							}
							
							console.log(frm.doc.warehouse);
							//frm.doc.rate_includes_tax = r2.message.rate_includes_tax;
							frm.refresh_field("warehouse");
							frm.refresh_field("rate_includes_tax");
							console.log("use_supplier_last_price")
							console.log(r2.message.use_supplier_last_price)

							console.log("update_price_list_price_with_purchase_invoice")

							console.log(r2.message.update_price_list_price_with_purchase_invoice)

							if(r2.message.use_supplier_last_price  == 0)
							{
								frm.doc.update_rates_in_price_list = r2.message.update_price_list_price_with_purchase_invoice;
								frm.refresh_field("update_rates_in_price_list");
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


frappe.ui.form.on("Purchase Invoice", "onload", function (frm) {

	// Code to fix the visibility issue in case PI is created from PO
	if(!frm.doc.credit_purchase)
	{
		frm.set_df_property("payment_mode","hidden",0);
		frm.set_df_property("payment_account","hidden",0);
		frm.set_df_property("credit_days","hidden",1);
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


});


frappe.ui.form.on('Purchase Invoice Item', {
	// cdt is Child DocType name i.e Quotation Item
	// cdn is the row name for e.g bbfcb8da6a
	
	item(frm, cdt, cdn) {

		if (typeof (frm.doc.supplier) == "undefined") {
			frappe.msgprint("Select Supplier.")
			row.item = "";
			return;
		}

		let row = frappe.get_doc(cdt, cdn);
		row.warehouse = frm.doc.warehouse;
		frm.item = row.item;
		frm.trigger("get_item_units");
		frm.trigger("make_taxes_and_totals");

		console.log("item")
		console.log(row.item)
		console.log("frappe.client.get_value,item")

		frappe.call(
			{
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Item',
					'filters': { 'item_code': row.item },
					'fieldname': ['item_code', 'base_unit', 'tax', 'tax_excluded']
				},
				callback: (r) => {
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

					var use_supplier_last_price =0 ;
					console.log("before call digitz_erp.api.settings_api.get_company_settings")

					frappe.call(
						{
							method:'digitz_erp.api.settings_api.get_company_settings',
							async:false,
							callback(r){								
								console.log("digitz_erp.api.settings_api.get_company_settings")
								console.log(r)								
								use_supplier_last_price = r.message[0].use_supplier_last_price								
								console.log("use_customer_last_price")
								console.log(use_supplier_last_price)
							}
						}
					);

					var use_price_list_price = 1
					if(use_supplier_last_price == 1)
					{
						console.log("before call digitz_erp.api.item_price_api.get_supplier_last_price_for_item")
						frappe.call(
							{
								method:'digitz_erp.api.item_price_api.get_supplier_last_price_for_item',
								args:{
									'item': row.item,
									'supplier': frm.doc.supplier
								},
								async:false,
								callback(r){
									console.log("digitz_erp.api.item_price_api.get_supplier_last_price_for_item")
									console.log(r)
									if(r.message != undefined)
									{
										row.rate = parseFloat(r.message);
										row.rate_in_base_unit = parseFloat(r.message);		
									}

									console.log("supplier last price")
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
									if(r.message != undefined)
									{
										row.rate = parseFloat(r.message);
										row.rate_in_base_unit = parseFloat(r.message);
									}
								}
							});			
					}	

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
	rate_included_tax(frm, cdt, cdn) {
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
	warehouse(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		frm.item = row.item
		frm.warehouse = row.warehouse
		frm.trigger("get_item_stock_balance");
	},
	items_add(frm, cdt, cdn) {
		frm.trigger("make_taxes_and_totals");
	},
	items_remove(frm, cdt, cdn) {
		frm.trigger("make_taxes_and_totals");
	}
});
