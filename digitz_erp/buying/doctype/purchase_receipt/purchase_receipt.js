// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Receipt", {

	show_a_message: function (frm,message) {
		frappe.call({
			method: 'digitz_erp.api.settings_api.show_a_message',
			args: {
				msg: message
			}
		});
	},

//   refresh(frm) {
//     if (frm.doc.docstatus == 1) {
//       // frappe.call(
//       // {
//       // 	method: 'digitz_erp.api.purchase_order_api.check_invoices_for_purchase_order',

//       // 	async: false,
//       // 	args: {
//       // 		'purchase_order': frm.doc.name
//       // 	},
//       // 	callback(pi_for_po_exists) {
//       // 		console.log("po_exists.message")
//       // 		console.log(pi_for_po_exists.message)

//       // 		let create_pi = false

//       // 		if (pi_for_po_exists.message == false)
//       // 		{
//       // 			create_pi = true
//       // 		}
//       // 		else if (frm.doc.order_status != "Completed")
//       // 		{
//       // 			create_pi = true
//       // 		}

//       // 		if(create_pi)
//       // 		{
//       frm.add_custom_button("Create Purchase Invoice", () => {
//         frappe.call({
//           method:
//             "digitz_erp.buying.doctype.purchase_receipt.purchase_receipt.generate_purchase_invoice_for_purchase_receipt",
//           args: {
//             purchase_receipt: frm.doc.name,
//           },
//           callback: function (r) {
//             frappe.show_alert(
//               {
//                 message: __(
//                   "The purchase invoice has been successfully generated and saved in draft mode."
//                 ),
//                 indicator: "green",
//               },
//               3
//             );
//             frm.reload_doc();
//             if (r.message != "No Pending Items")
//               frappe.set_route("Form", "Purchase Invoice", r.message);
//           },
//         });
//       });
//     }
//   },
//   // 		});
//   //     }
//   // },
});



frappe.ui.form.on('Purchase Receipt', {

	refresh:function (frm) {
		if (frm.doc.docstatus == 1) {


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


			frm.add_custom_button("Create Purchase Invoice", () => {
			  frappe.call({
				method:
				  "digitz_erp.buying.doctype.purchase_receipt.purchase_receipt.generate_purchase_invoice_for_purchase_receipt",
				args: {
				  purchase_receipt: frm.doc.name,
				},
				callback: function (r) {
				  frappe.show_alert(
					{
					  message: __(
						"The purchase invoice has been successfully generated and saved in draft mode."
					  ),
					  indicator: "green",
					},
					3
				  );
				  frm.reload_doc();
				  if (r.message != "No Pending Items")
					frappe.set_route("Form", "Purchase Invoice", r.message);
				},
			  });
			});
		  }

		update_total_big_display(frm)
	},
	setup: function (frm) {

		frm.add_fetch('supplier', 'tax_id', 'tax_id')
		frm.add_fetch('supplier', 'credit_days', 'credit_days')
		frm.add_fetch('supplier', 'full_address', 'supplier_address')
		frm.add_fetch('supplier', 'tax_id', 'tax_id')
		frm.add_fetch('payment_mode', 'account', 'payment_account')
		frm.set_df_property("supplier_inv_no", "mandatory", 1);
		//frm.get_field('taxes').grid.cannot_add_rows = true;

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
					"disabled": 0
				}
			};
		});

		frm.set_query("warehouse", function () {
			return {
				"filters": {
					"disabled": 0
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
	assign_defaults(frm)
	{
		if(frm.is_new())
		{
			// Remove the initial blank item row
			if (frm.doc.purchase_order== undefined)
				frm.clear_table('items');

			frm.trigger("get_default_company_and_warehouse");

			frappe.db.get_value('Company', frm.doc.company, 'default_credit_purchase', function(r) {

				if (r && r.default_credit_purchase === 1) {
					console.log("credit purchase from  assign_defaults")
					console.log(r.default_credit_purchase)
						frm.set_value('credit_purchase', 1);
				}

			});

			set_default_payment_mode(frm);
		}

		set_payment_visibility(frm)
	},
	validate:function(frm){

		if(!frm.doc.credit_purchase)
		{
			if(!frm.doc.payment_mode)
			{
				frappe.throw("Please select payment mode")
			}
		}
		else if(frm.doc.credit_purchase)
		{
			total_scheduled_amount  = 0

			frm.doc.payment_schedule.forEach(function(row) {
				if (row){
					if(row.amount)
						total_scheduled_amount = total_scheduled_amount + row.amount;
				}
			});

			if(frm.doc.rounded_total != total_scheduled_amount)
			{
				frappe.throw("Scheduled amount mismatch!!! Scheduled amount must be equal to rounded total")
			}

		}
	},
	supplier(frm) {

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
			method: 'digitz_erp.api.accounts_api.get_supplier_balance',
			args: {
				'supplier': frm.doc.supplier,
				'date':frm.doc.posting_date
			},
			callback: (r) => {
				frm.set_value('supplier_balance',r.message[0].supplier_balance)
				frm.refresh_field("supplier_balance");
			}
		});
		frappe.call(
			{
				method:'digitz_erp.api.settings_api.get_supplier_terms',
				args:{
					'supplier': frm.doc.supplier
				},
				callback(r){
					frm.doc.terms = r.message.template_name,
					frm.doc.terms_and_conditions = r.message.terms
					frm.refresh_field("terms_and_conditions");
					frm.refresh_field("terms");
				}
			}
		);

		fill_payment_schedule(frm);
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

		set_default_payment_mode(frm);

		fill_payment_schedule(frm,refresh=true);
	},
	credit_days(frm){
		fill_payment_schedule(frm,refresh_credit_days= true);
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
            console.log(r2);
            if (r2 && r2.message && r2.message.stock_qty !== undefined)
            {
                const itemRow = frm.doc.items.find(item => item.item === frm.item && item.warehouse === frm.warehouse);
                if (itemRow) {
                    const unit = itemRow.unit;
                    frm.doc.selected_item_stock_qty_in_the_warehouse = "Stock Bal: "  + r2.message.stock_qty +  " " + unit + " for " + frm.item + " at w/h: "+ frm.warehouse + ": ";
                    frm.refresh_field("selected_item_stock_qty_in_the_warehouse");
                }
            }
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

		fill_payment_schedule(frm);

		frm.refresh_field("items");
		frm.refresh_field("taxes");

		frm.refresh_field("gross_total");
		frm.refresh_field("net_total");
		frm.refresh_field("tax_total");
		frm.refresh_field("round_off");
		frm.refresh_field("rounded_total");

		update_total_big_display(frm)

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
							'fieldname': ['default_warehouse', 'rate_includes_tax','update_price_list_price_with_purchase_invoice','use_supplier_last_price', 'supplier_terms']
						},
						callback: (r2) => {

							console.log(r2)

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

							// if(r2.message.use_supplier_last_price  == 0)
							// {
							frm.doc.update_rates_in_price_list = r2.message.update_price_list_price_with_purchase_invoice;
							frm.refresh_field("update_rates_in_price_list");
							// }

							if(r2.message.supplier_terms)
							{
								frm.doc.terms = r2.message.supplier_terms
								frm.refresh_field("terms");

								frappe.call(
									{
										method:'digitz_erp.api.settings_api.get_terms_for_template',
										args:{
											'template': r2.message.supplier_terms
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

frappe.ui.form.on("Purchase Receipt", "onload", function (frm) {

	frm.trigger("assign_defaults")
	fill_payment_schedule(frm);
});


frappe.ui.form.on('Purchase Receipt Item', {
	// cdt is Child DocType name i.e Quotation Item
	// cdn is the row name for e.g bbfcb8da6a

	item(frm, cdt, cdn) {
		var child = locals[cdt][cdn];

		check_budget_utilization(frm, cdt, cdn,"Item");
		
		if (frm.doc.default_cost_center) {
			frappe.model.set_value(cdt, cdn, 'cost_center', frm.doc.default_cost_center);
		}

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
					'fieldname': ['item_name', 'base_unit', 'tax', 'tax_excluded']
				},
				callback: (r) => {

					console.log(r.message)

					row.item_name = r.message.item_name;

					//row.uom = r.message.base_unit;
					row.tax_excluded = r.message.tax_excluded;
					row.base_unit = r.message.base_unit;
					row.unit = r.message.base_unit;
					row.conversion_factor = 1;
					row.display_name = row.item_name
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
	console.log("from set_default_payment_mode")

	if(!frm.doc.credit_purchase){

		frappe.db.get_value('Company', frm.doc.company, 'default_payment_mode_for_purchase', function(r) {

			if (r && r.default_payment_mode_for_purchase) {
				frm.set_value('payment_mode', r.default_payment_mode_for_purchase);
			}
			else {
				frappe.msgprint('Default payment mode for purchase not found.');
			}
		});
    }
	else
	{
		frm.set_value('payment_mode','');
	}

	set_payment_visibility(frm)
}

function set_payment_visibility(frm)
{
	frm.set_df_property("credit_days", "hidden", !frm.doc.credit_purchase);
	frm.set_df_property("payment_mode", "hidden", frm.doc.credit_purchase);
	frm.set_df_property("payment_account", "hidden", frm.doc.credit_purchase);
}

function fill_payment_schedule(frm, refresh=false,refresh_credit_days=false)
{
	console.log("from fill_payment_schedule")
	console.log("refresh")
	console.log(refresh)
	if(refresh)
	{
		frm.doc.payment_schedule = [];
		refresh_field("payment_schedule");
	}

	if (frm.doc.credit_purchase) {
		var postingDate = frm.doc.posting_date;
		var creditDays = frm.doc.credit_days;
		var roundedTotal = frm.doc.rounded_total;
		console.log("ROUNDED TOTAL:",roundedTotal);

		if (!frm.doc.payment_schedule) {
			frm.doc.payment_schedule = [];
		}

		var paymentRow = null;

		row_count = 0;
		// Check if a Payment Schedule row already exists
		frm.doc.payment_schedule.forEach(function(row) {
			if (row){
				paymentRow = row;
				if(refresh || refresh_credit_days)
				{
					paymentRow.date = creditDays ? frappe.datetime.add_days(postingDate, creditDays) : postingDate;
				}

				row_count++;
			}
		});
		console.log("row_count")
		console.log(row_count)
		console.log("paymentRow")
		console.log(paymentRow)
		console.log("refresh_credit_days")
		console.log(refresh_credit_days)

		//If there is no row exits create one with the relevant values
		if (!paymentRow) {
			// Calculate payment schedule and add a new row
			paymentRow = frappe.model.add_child(frm.doc, "Payment Schedule", "payment_schedule");
			paymentRow.date = creditDays ? frappe.datetime.add_days(postingDate, creditDays) : postingDate;
			paymentRow.payment_mode = "Cash"
			paymentRow.amount = roundedTotal;
			refresh_field("payment_schedule");
		}
		else if (row_count==1)
		{
			//If there is only one row update the amount. If there is more than one row that means there is manual
			//entry and	user need to manage it by themself
			paymentRow.amount = roundedTotal;
			refresh_field("payment_schedule");
		}

		//Update date based on credit_days if there is a credit days change or change in the credit_purchase checkbox
		if(refresh || refresh_credit_days)
			paymentRow.date = creditDays ? frappe.datetime.add_days(postingDate, creditDays) : postingDate;
			refresh_field("payment_schedule");
	}
	else
	{
		frm.doc.payment_schedule = [];
		refresh_field("payment_schedule");
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
            let gl_postings = response.message.gl_postings;
            let totalDebit = parseFloat(response.message.total_debit).toFixed(2);
            let totalCredit = parseFloat(response.message.total_credit).toFixed(2);

            // Generate HTML content for the popup
            let htmlContent = '<div style="max-height: 680px; overflow-y: auto;">' +
                              '<table class="table table-bordered" style="width: 100%;">' +
                              '<thead>' +
                              '<tr>' +
                              '<th style="width: 15%;">Account</th>' +
							  '<th style="width: 25%;">Remarks</th>' +
                              '<th style="width: 10%;">Debit Amount</th>' +
                              '<th style="width: 10%;">Credit Amount</th>' +
							  '<th style="width: 10%;">Party</th>' +
                              '<th style="width: 10%;">Against Account</th>' +                              
                              '<th style="width: 10%;">Project</th>' +
                              '<th style="width: 10%;">Cost Center</th>' +                              
                              '</tr>' +
                              '</thead>' +
                              '<tbody>';

			console.log("gl_postings",gl_postings)

            gl_postings.forEach(function (gl_posting) {
                let remarksText = gl_posting.remarks || '';
                let debitAmount = parseFloat(gl_posting.debit_amount).toFixed(2);
                let creditAmount = parseFloat(gl_posting.credit_amount).toFixed(2);

                htmlContent += '<tr>' +
                               `<td>${gl_posting.account}</td>` +
							   `<td>${remarksText}</td>` +
                               `<td style="text-align: right;">${debitAmount}</td>` +
                               `<td style="text-align: right;">${creditAmount}</td>` +
							   `<td>${gl_posting.party}</td>` +
                               `<td>${gl_posting.against_account}</td>` +                               
                               `<td>${gl_posting.project}</td>` +
                               `<td>${gl_posting.cost_center}</td>` +
                               
                               '</tr>';
            });

            // Add totals row
            htmlContent += '<tr>' +
                           '<td style="font-weight: bold;">Total</td>' +
						   '<td></td>'+
                           `<td style="text-align: right; font-weight: bold;">${totalDebit}</td>` +
                           `<td style="text-align: right; font-weight: bold;">${totalCredit}</td>` +
                           '<td colspan="5"></td>' +
                           '</tr>';

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
            d.$wrapper.find('.modal-dialog').css('max-width', '90%'); 

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


function check_budget_utilization(frm, cdt, cdn, reference_type) {
    const row = frappe.get_doc(cdt, cdn);

    // Ensure the item field is filled before proceeding
    if (!row.item) {
        return;
    }

    // Call server method to get budget details
    frappe.call({
        method: "digitz_erp.api.accounts_api.get_balance_budget_value",
        args: {
            reference_type: "Item",
            reference_value: row.item,
            transaction_date: frm.doc.transaction_date || frappe.datetime.nowdate(),
            company: frm.doc.company,
            project: frm.doc.project || null,
            cost_center: frm.doc.cost_center || null
        },
        callback: function (response) {
            if (response && response.message) {
                const result = response.message;

                // Log the response for debugging
                console.log("Budget Result:", result);

                if (!result.no_budget) {
                    // Display budget details if available
                    const details = result.details || {};
                    const budgetMessage = `
                        <strong>Budget Against:</strong> ${details["Budget Against"] || "N/A"}<br>
                        <strong>Reference Type:</strong> ${details["Reference Type"] || "N/A"}<br>
                        <strong>Budget Amount:</strong> ${details["Budget Amount"] || 0}<br>
                        <strong>Utilized Amount:</strong> ${details["Used Amount"] || 0}<br>
                        <strong>Remaining Balance:</strong> ${details["Available Balance"] || 0}
                    `;

                    // Custom method to display the message (replace with your own if needed)
                   
                    frm.events.show_a_message(frm,budgetMessage);
                    
                }
            } else {
                // Handle case where no response is received
                frappe.msgprint({
                    title: __("Error"),
                    indicator: "red",
                    message: __("No response received from the server.")
                });
            }
        }
    });
}