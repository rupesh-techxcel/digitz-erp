// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Company', {
	refresh: function(frm) {
		frm.set_query("default_warehouse", function() {
			return {
				"filters": {
					"disabled": 0
				}
			};
		});
	},
	tax_excluded(frm)
	{
		frm.set_df_property("tax","read_only",frm.doc.tax_excluded);

	   if(frm.doc.tax_excluded)
	   {
		   console.log("Tax excluded?");
		   console.log(frm.doc.tax_excluded);
		   frm.doc.tax ="";
		   frm.refresh_field("tax");
	   }
	}

});

frappe.ui.form.on("Company", "onload", function(frm) {
	//Since the default selectionis cash
	frm.set_query("default_payable_account", function() {
		return {
			"filters": {
				"is_group": 0,
				"root_type":"Liability"
			}
		};
	});

	frm.set_query("default_receivable_account", function() {
		return {
			"filters": {
				"is_group": 0,
				"root_type":"Asset"
			}
		};
	});
	frm.set_query("default_advance_received_account",function(){
		return{
			"filters": {
				"is_group":0,
				"root_type":"Liability"
			}
		}
	})
	frm.set_query("default_advance_paid_account",function(){
		return{
			"filters": {
				"is_group":0,
				"root_type":"Asset"
			}
		}
	})

	frm.set_query("stock_received_but_not_billed", function() {
		return {
			"filters": {
				"is_group": 0,
				"account_type":"Stock Received But Not Billed"
			}
		};
	});

	frm.set_query("default_inventory_account", function() {
		return {
			"filters": {
				"is_group": 0,
				"account_type":"Stock"
			}
		};
	});

	frm.set_query("cost_of_goods_sold_account", function() {
		return {
			"filters": {
				"is_group": 0,
				"account_type":"Cost Of Goods Sold"
			}
		};
	});

	frm.set_query("default_income_account", function() {
		return {
			"filters": {
				"is_group": 0,
				"root_type":"Income"
			}
		};
	});

	frm.doc.rules_for_prices = "Default Selling Price List : Standard Selling" +
	"\nDefault Buying Price List : Standard Buying" +
	"\nUse Default price LIst when customer or supplier price not available: Yes"

});
