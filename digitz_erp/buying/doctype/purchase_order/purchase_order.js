// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Order', {

	show_a_message: function (frm,message) {
		frappe.call({
			method: 'digitz_erp.api.settings_api.show_a_message',
			args: {
				msg: message
			}
		});
	},
	refresh:function(frm){

		frappe.call({
            method: "digitz_erp.api.purchase_order_api.services_module_exists",
            args: {
                module_name: "Digitz.Services"
            },
            callback: function(response) {

                if (response.message) { 					
					frm.set_df_property("for_sub_contracting", "hidden", 0);
					create_sub_contract_button(frm);
                }
				else
				{
					frm.set_df_property("for_sub_contracting", "hidden", 1);
				}
				
            }
        });


		if (frm.doc.docstatus == 1)

			if (frm.doc.docstatus == 1) {
				console.log("frm.doc.name")
				console.log(frm.doc.name)

				frappe.call({
                    method: "digitz_erp.api.purchase_order_api.check_pending_items_in_purchase_order",
                    args: {
                        po_no: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message === true) {  // Check if server-side method returned True

							let create_pr = false

							if (frm.doc.order_status != "Completed")
							{
								create_pr = true
							}

							if(create_pr)
							{
								frm.add_custom_button('Create Purchase Receipt', () => {
											frappe.call({
												method: 'digitz_erp.api.purchase_order_api.create_purchase_receipt_for_purchase_order',
												args: {
													purchase_order: frm.doc.name
												},
												callback: function(r) {

													console.log("purchase receipt client side")
													console.log(r.message)
													if (r.message) {
														// Open the Purchase Order in the UI without saving it
														let pr_doc = frappe.model.sync([r.message])[0];
														console.log("pr_doc")
														console.log(pr_doc)
														frappe.set_route("Form", "Purchase Receipt", pr_doc.name);
													}
												}										
											});
										},"Create");
								}

								let create_pi = false

								if (frm.doc.order_status != "Completed")
								{
									create_pi = true
								}
	
								if(create_pi)
								{
									frm.add_custom_button('Create Purchase Invoice', () => {
										frappe.call({
											method: 'digitz_erp.api.purchase_order_api.create_purchase_invoice_for_purchase_order',
											args: {
												purchase_order: frm.doc.name
											},
											callback: function(r) {
												let pr_doc = frappe.model.sync([r.message])[0];
												frappe.set_route("Form", "Purchase Invoice", pr_doc.name);
											}
										});
									}, "Create");
								}
							}

							
						}}
					
					);	

				

			}

			update_total_big_display(frm)
	},
	setup: function (frm) {

		frm.add_fetch('supplier', 'tax_id', 'tax_id')
		frm.add_fetch('supplier', 'credit_days', 'credit_days')
		frm.add_fetch('supplier', 'full_address', 'supplier_address')
		frm.add_fetch('supplier', 'tax_id', 'tax_id')
		frm.add_fetch('payment_mode', 'account', 'payment_account')

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

		frm.set_query("warehouse", function() {
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


		

		// frm.doc.items.forEach((item)=>{
		// 	console.log("hello")
		// 	frappe.model.trigger("item", item.doctype, item.name);
		// })
	},
	for_sub_contracting(frm)
	{
		create_sub_contract_button(frm);
	},
	assign_defaults(frm)
	{
		console.log("assign_defaults")

		

		if(frm.is_new())
		{
			// frm.clear_table('items');

			console.log("material request checking")

			if(frm.doc.material_request != undefined){
				frm.doc.items.forEach(function(item) {
					// Call the update_item_row method for each item in the child table
					update_item_row(frm, item.doctype, item.name);
				});
			}
			else
			{
				console.log("table cleared")
				frm.clear_table('items');
			}

			frm.trigger("get_default_company_and_warehouse")
		
			set_default_payment_mode(frm);
			
		}
	},
	validate:function(frm){

		if(!frm.doc.credit_purchase)
		{
			if(!frm.doc.payment_mode)
			{
				frappe.throw("Please select Payment Mode")
			}
		}
	},
	supplier(frm) {
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



		for(item of frm.doc.items){
			// console.log(item.doctype,item.name)
			update_item_row(frm,item.doctype,item.name);
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
	credit_purchase(frm) {
		set_default_payment_mode(frm)
	},
	warehouse(frm) {
		console.log("warehouse set")
		console.log(frm.doc.warehouse)

		frm.doc.items.forEach((item)=>{
			item.warehouse = frm.doc.warehouse
		})

		frm.refresh_fields('items');
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

					frappe.call({
						method: 'frappe.client.get_value',
						args: {
							doctype: 'Company',
							filters: { company_name: default_company },
							fieldname: ['default_warehouse', 'rate_includes_tax']
						},
						callback: function (r2) {
							if (r2 && r2.message) {
								if (r2.message.default_warehouse) {
									frm.set_value('warehouse', r2.message.default_warehouse);
								}
								if ('rate_includes_tax' in r2.message) {
									frm.set_value('rate_includes_tax', r2.message.rate_includes_tax);
								}
							} else {
								console.error('No data found for Company: ', default_company);
							}
						}
					});

					frappe.db.get_value('Company', 
						{ name: frm.doc.company }, 
						['default_credit_purchase', 'allow_purchase_with_dimensions', 'allow_purchase_with_dimensions_2'], 
						function (r) {
							if (r) {
								// Check and set the value for credit_purchase
								if (r.default_credit_purchase === 1) {
									frm.set_value('credit_purchase', 1);
								}
					
								// Update field properties for "use_dimensions" and "use_dimensions_2"
								frm.set_df_property("use_dimensions", "hidden", r.allow_purchase_with_dimensions ? 0 : 1);
								frm.set_df_property("use_dimensions_2", "hidden", r.allow_purchase_with_dimensions_2 ? 0 : 1);

								if(r.allow_purchase_with_dimensions_2)
								{
									console.log("creating button for rate update!!!")									
									create_button_for_rate_per_kg(frm);
								}

							} else {
								console.error("No data found for the selected company.");
							}
						}
					);
					

				} else {
					console.error('No default company found in Global Settings.');
				}
			}
		});
	},
	calculate_qty: function (frm) {
    
        if (frm.doc.use_dimensions) {
            frm.doc?.items.forEach(function (entry) {
                let width = entry.width || 0;
                let height = entry.height || 0;
                let no_of_pieces = entry.no_of_pieces || 0;
                entry.qty = width * height * no_of_pieces;
            });

            frm.refresh_field("items");
        }
    },
	calculate_rate: function (frm) {

		if (frm.doc.use_dimensions_2) {
        
            frm.doc?.items.forEach(function (entry) {
                let length = entry.length || 0;
                let weight_per_meter = entry.weight_per_meter || 0;                
				let rate_per_kg = entry.rate_per_kg || 0;
                entry.rate = length * weight_per_meter * rate_per_kg;
            });

			frm.trigger("make_taxes_and_totals");
			
            frm.refresh_field("items");
        }
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

		update_total_big_display(frm)

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

function set_default_payment_mode(frm)
{
	console.log("hi")
	console.log(frm .doc.company)
	if(!frm.doc.credit_purchase)
	{
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
		frm.set_value('payment_mode', "");
	}

	frm.set_df_property("credit_days", "hidden", !frm.doc.credit_purchase);
	frm.set_df_property("payment_mode", "hidden", frm.doc.credit_purchase);
	frm.set_df_property("payment_account", "hidden", frm.doc.credit_purchase);

}


frappe.ui.form.on("Purchase Order", "onload", function (frm) {

	frm.trigger("assign_defaults")

	 //When purchase order created from Material Request,client side ensure that the item method is calling for each method
	 

});

frappe.ui.form.on('Purchase Order Item', {
	// cdt is Child DocType name i.e Quotation Item
	// cdn is the row name for e.g bbfcb8da6a
	item(frm,cdt,cdn){
		let row = frappe.get_doc(cdt, cdn);
		if(frm.doc.supplier)
		{
			check_budget_utilization(frm, cdt, cdn,row.item, row.item_group);
			update_item_row(frm,cdt,cdn);
		}
		else{
			frappe.msgprint("Select supplier to proceed further.")
			row.item = ""
		}
		
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
	height: function (frm, cdt, cdn) {
        console.log("height")
        let row = locals[cdt][cdn];
        frm.trigger("calculate_qty");
    },
    width: function (frm, cdt, cdn) {
        console.log("width")
        let row = locals[cdt][cdn];
        frm.trigger("calculate_qty");
    },
    no_of_pieces: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        console.log("no_of_pieces")
        frm.trigger("calculate_qty");
    },
	length: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        console.log("length")
        frm.trigger("calculate_rate");
    },
	rate_per_kg: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
		console.log("rate_per_kg")        
        frm.trigger("calculate_rate");
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

		let row = frappe.get_doc(cdt, cdn);
		row.warehouse = frm.doc.warehouse

		frm.trigger("make_taxes_and_totals");

	},
	items_remove(frm, cdt, cdn) {
		frm.trigger("make_taxes_and_totals");
	}
});


function update_item_row(frm,cdt,cdn){

		var child = locals[cdt][cdn];
		if (frm.doc.default_cost_center) {
			frappe.model.set_value(cdt, cdn, 'cost_center', frm.doc.default_cost_center);
		}

		let row = frappe.get_doc(cdt, cdn);

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
					'fieldname': ['item_name','description', 'base_unit', 'tax', 'tax_excluded','height','width','area','length']
				},
				callback: (r) => {

					console.log("r.message")
					console.log(r.message)

					row.item_name = r.message.item_name;
					row.display_name = r.message.description;
					//row.uom = r.message.base_unit;
					row.tax_excluded = r.message.tax_excluded;
					row.base_unit = r.message.base_unit;
					row.unit = r.message.base_unit;
					row.height = r.message.height
					row.width = r.message.width
					row.area = r.message.area
					row.length = r.message.length
					row.conversion_factor = 1;
					frm.warehouse = row.warehouse
					console.log("before trigger")
					frm.trigger("get_item_stock_balance");
					frm.refresh_field("items");


					console.log("r.message.tax_excluded")
					console.log(r.message.tax_excluded)

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
									row.tax_rate = r2.message.tax_rate;
									// console.log("ajay", row.tax,row.tax_rate,(row.tax_rate * row.gross_amount), row.gross_amount)
									frm.trigger("make_taxes_and_totals");
										frm.refresh_field("items");
								}

							})
					}
					else {
						row.tax = "";
						row.tax_rate = 0;
					}

					console.log("row.tax_rate")
					console.log(row.tax_rate)

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

					if(use_price_list_price ==1 && frm.doc.price_list)
					{
						console.log("digitz_erp.api.item_price_api.get_item_price")
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
					}
					frm.trigger("make_taxes_and_totals");
					frm.refresh_field("items");
					
					//  Get current stock for the item in the warehouse
				}
			});

			
}

function update_total_big_display(frm) {

	let netTotal = isNaN(frm.doc.rounded_total) ? 0 : parseFloat(frm.doc.rounded_total).toFixed(0);

    // Add 'AED' prefix and format net_total for display

	let displayHtml = `<div style="font-size: 25px; text-align: right; color: black;">AED ${netTotal}</div>`;


    // Directly update the HTML content of the 'total_big' field
    frm.fields_dict['total_big'].$wrapper.html(displayHtml);

}

let create_button_for_rate_per_kg = function (frm) {
    frm.add_custom_button('Import Excel with Rates', () => {

        if (!(frm.doc.use_dimensions_2)) {
            frappe.throw("Please enable 'Use Dimensions 2' to upload the Excel file for rates.");
        }

		if(!frm.doc.supplier)
		{
			frappe.throw("Please select Supplier first.");
		}

        const dialog = new frappe.ui.Dialog({
            title: 'Upload Excel Sheet',
            fields: [
                {
                    fieldname: 'excel_file',
                    label: 'Excel File',
                    fieldtype: 'Attach',
                    reqd: 1
                }
            ],
            primary_action_label: 'Upload and Update',
            primary_action: function () {
                const file = dialog.get_value('excel_file');
                if (!file) {
                    frappe.msgprint('Please upload a file.');
                    return;
                }

                // Call server-side method to process the file
                frappe.call({
                    method: 'digitz_erp.api.purchase_order_api.update_item_rate_per_kg',
                    args: { file_url: file },
                    callback: function (response) {
                        if (response.message.success) {
                            const items = response.message.data;

							console.log("items,",items)

                            // Update the child table rows based on the returned data
                            frm.doc.items.forEach(row => {
								console.log("row,",row)
                                const item_data = items.find(item => item.item_code === row.item);
                                if (item_data) {
									console.log("item_data,",item_data)                                    
									frappe.model.set_value(row.doctype, row.name, 'rate_per_kg', item_data.rate_per_kg);
                                }
                            });

							frm.trigger("calculate_rate");
                            frm.trigger("make_taxes_and_totals");
                            frm.refresh_field('items');

                            // Notify the user
                            frappe.msgprint({
                                title: "Success",
                                indicator: "green",
                                message: "Rates have been updated successfully."
                            });
                        } else {
                            frappe.msgprint({
                                title: "Error",
                                indicator: "red",
                                message: response.message.message
                            });

                            if (response.message.errors && response.message.errors.length) {
                                console.error("Errors:", response.message.errors);
                            }
                        }
                    }
                });

                dialog.hide();
            }
        });

        dialog.show();
    });
};

let create_sub_contract_button = function(frm) {
    // Check if the document is submitted and 'for_sub_contracting' is true
    if (frm.doc.docstatus === 1 && frm.doc.for_sub_contracting) {
        // Call the server-side method to check if the Sub Contracting Order exists

        frappe.call({
            method: "digitz_erp.api.purchase_order_api.sub_contracting_order_exists",
            args: {
                purchase_order: frm.doc.name
            },
            callback: function(response) {
                if (!response.message) { // If Sub Contracting Order does not exist
                    if (!frm.custom_buttons || !frm.custom_buttons["Create Sub Contract Order"]) {
						
                        frm.add_custom_button("Create Sub Contract Order", () => {

							if(!frm.doc.project)
							{
								frappe.throw("Please select a project and save the document to proceed with the subcontracting order.")
							}

							if (frm.is_dirty()) {
								frappe.throw("Form has unsaved changes. Save the document to continue..");
							}

                            // Use `frappe.new_doc` to create a new document in the UI
                            frappe.new_doc("Sub Contracting Order", {
                                purchase_order: frm.doc.name,
								company:frm.doc.company,
                                project: frm.doc.project, // Assign project from the current form
                                supplier: frm.doc.supplier, // Assign supplier from the current form
								material_issue_warehouse: frm.doc.warehouse,
								material_return_warehouse: frm.doc.warehouse
                            });
                        });
                    }
                }
            }
        });
    }
};

function check_budget_utilization(frm, cdt, cdn, item, item_group) {
	
    const row = frappe.get_doc(cdt, cdn);

    console.log("from check_budget method");

    if (!row.item) {
        return;
    }

    // Call server method to get budget details
    frappe.call({
        method: "digitz_erp.api.accounts_api.get_balance_budget_value",
        args: {
            reference_type: "Item",
            reference_value: item,
            doc_type: "Purchase Order",
            doc_name: frm.doc.name,
            transaction_date: frm.doc.posting_date || frappe.datetime.nowdate(),
            company: frm.doc.company,
            project: frm.doc.project || null,
            cost_center: frm.doc.default_cost_center || null
        },
        callback: function (response) {
            if (response && response.message) {
                const result = response.message;
                console.log("Budget Result:", result);

                if (!result.no_budget) {
                    const details = result.details || {};
                    
                    const budget_amount = Number(details["Budget Amount"]) || 0;
                    let used_amount = Number(details["Used Amount"]) || 0;
                    const available_balance = Number(details["Available Balance"]) || 0;

                    const ref_type = details["Reference Type"];
                    let total_map = 0;

                    // Iterate through items dynamically based on reference type
                    frm.doc.items.forEach(row => {
                        
                        let gross_amount = Number(row.gross_amount) || 0;

                        if (ref_type === "Item" && row.item === item) {
                            total_map += gross_amount;
                        } else if (ref_type === "Item Group" && row.item_group === item_group) {
                            total_map += gross_amount;
                        }
                    });

                    used_amount += total_map;

                    if (budget_amount < used_amount) {
                        row.item = "";
                        frm.events.show_a_message("Over budget allocation!!!");
                    }

                    // Fetch item valuation rate
                    frappe.call({
                        method: 'digitz_erp.api.items_api.get_item_valuation_rate_default',
                        async: false,
                        args: {
                            'item': row.item,
                            'posting_date': frm.doc.posting_date,
                            'posting_time': frm.doc.posting_time
                        },
                        callback(r) {
                            console.log("Valuation rate in console", r.message);

                            if (r.message == 0) {
                                frappe.throw("No valuation rate has been specified for the item, " + row.item + ". Please update the Item Master with the appropriate valuation rate to proceed.");
                                row.item = "";
                                frm.refresh_field("items");
                            } else {
                                row.valuation_rate = r.message;

                                if (!frm.doc.project) {
                                    frm.events.show_a_message(frm, "Please select a project if required.");
                                }

                                const budgetMessage = `
                                    <strong>Budget Against:</strong> ${details["Budget Against"] || "N/A"}<br>
                                    <strong>Reference Type:</strong> ${details["Reference Type"] || "N/A"}<br>
                                    <strong>Budget Amount:</strong> ${budget_amount}<br>
                                    <strong>Utilized Amount:</strong> ${used_amount}<br>
                                    <strong>Remaining Balance:</strong> ${available_balance}
                                `;

                                row.available_amount_in_budget = available_balance
                            
                                frm.events.show_a_message(frm, budgetMessage);
                            }
                        }
                    });
                }
            } else {
                frappe.msgprint({
                    title: __("Error"),
                    indicator: "red",
                    message: __("No response received from the server.")
                });
            }
        }
    });
}