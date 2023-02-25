// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Stock Transfer', {

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
							console.log(r2);
							frm.doc.source_warehouse = r2.message.default_warehouse;														
							frm.refresh_field("source_warehouse");
						}
					}

				)
			}
		})
	},
	get_item_stock_balance(frm) {

		frm.doc.selected_item_stock_qty_in_the_warehouse =""
		frm.refresh_field("selected_item_stock_qty_in_the_warehouse");

		frappe.call(
			{
				method: 'digitz_erp.api.items_api.get_stock_for_item',
				async: false,
				args: {
					'item': row.item,
					'warehouse': frm.source_warehouse,
					'posting_date': frm.doc.posting_date,
					'posting_time': frm.doc.posting_time
				},
				callback(r) {
					if(typeof(r.message.stock_qty) !='undefined')
						frm.doc.selected_item_stock_qty_in_the_warehouse ="Stock in " + frm.source_warehouse + ": " +  r.message.stock_qty
					
					frm.refresh_field("selected_item_stock_qty_in_the_warehouse");
				}
			});

			frappe.call(
				{
					method: 'digitz_erp.api.items_api.get_stock_for_item',
					async: false,
					args: {
						'item': row.item,
						'warehouse': frm.target_warehouse,
						'posting_date': frm.doc.posting_date,
						'posting_time': frm.doc.posting_time
					},
					callback(r) {
						if(typeof(r2.message.stock_qty) !='undefined')						
							frm.doc.selected_item_stock_qty_in_the_warehouse = frm.doc.selected_item_stock_qty_in_the_warehouse + ", " + frm.target_warehouse + ": " +  r2.message.stock_qty					
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
});

frappe.ui.form.on("Stock Transfer", "onload", function (frm) {

	//Since the default selectionis cash
	//frm.set_df_property("date","read_only",1);	
	// frm.set_query("source_warehouse", function () {
	// 	return {
	// 		"filters": {
	// 			"is_group": 0
	// 		}
	// 	};
	// });

	// frm.set_query("target_warehouse", function () {
	// 	return {
	// 		"filters": {
	// 			"is_group": 0
	// 		}
	// 	};
	// });

	frm.trigger("get_default_company_and_warehouse");
})

frappe.ui.form.on('Stock Transfer Item', {

	item(frm, cdt, cdn) {

		let row = frappe.get_doc(cdt, cdn);		
		frappe.call(
			{
			method: 'frappe.client.get_value',
					args: {
						'doctype': 'Item',
						'filters': { 'item_name': row.item },
						'fieldname': ['item_code', 'base_unit', 'tax', 'tax_excluded']
					},
					callback: (r) => {
						
						row.item_code = r.message.item_code;
						row.base_unit = r.message.base_unit;
						row.unit = r.message.base_unit;
						row.conversion_factor = 1;
						frm.item = row.item
						row.source_warehouse = frm.doc.source_warehouse
						row.target_warehouse = frm.doc.target_warehouse

						frm.source_warehouse = row.source_warehouse
						frm.target_warehouse = row.target_warehouse

						frm.trigger("get_item_stock_balance");
						frm.refresh_field("items");

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
										frappe.call(
											{
												method: 'digitz_erp.api.items_api.get_item_price_for_price_list',
												async: false,
												args: {
													'item': row.item,
													'price_list': "Standard Buying"
												},
												callback(r) {
													if (r.message.length == 1) {										
														row.valuation_rate = r.message[0].price;
														row.rate_in_base_unit = r.message[0].price;
														frm.refresh_field("items");
													}
												}
											});
									}
									else
									{
										row.rate = r.message
										row.rate_in_base_unit = r.message
										frm.refresh_field("items");
									}								
								}
							});
					}
				});
		
		console.log("Before get valuation rate for the item")
		

		frappe.call(
			{
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Item',
					'filters': { 'item_name': row.item },
					'fieldname': ['item_code', 'base_unit', 'tax', 'tax_excluded']
				},
				callback: (r) => {
					
					row.item_code = r.message.item_code;
					//row.uom = r.message.base_unit;	
					row.tax_excluded = r.message.tax_excluded;
					row.base_unit = r.message.base_unit;
					row.unit = r.message.base_unit;
					row.conversion_factor = 1;
					frm.item = row.item
					frm.source_warehouse = row.source_warehouse
					frm.target_warehouse = row.target_warehouse
					frm.trigger("get_item_stock_balance");	

					frm.refresh_field("items");
				}
			});
	},
	source_warehouse(frm, cdt, cdn) {

		let row = frappe.get_doc(cdt, cdn);
		frm.item = row.item
		frm.source_warehouse = row.source_warehouse
		frm.target_warehouse = row.target_warehouse
		frm.trigger("get_item_stock_balance");
	},
	target_warehouse(frm, cdt, cdn) {

		let row = frappe.get_doc(cdt, cdn);
		frm.item = row.item
		frm.source_warehouse = row.source_warehouse
		frm.target_warehouse = row.target_warehouse
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
