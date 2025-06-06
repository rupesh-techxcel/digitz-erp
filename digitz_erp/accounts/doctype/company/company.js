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
		   frm.doc.tax_account = ""
		   frm.refresh_field("tax");
		   frm.refresh_field("tax_account");
	   }
	},	
	refresh_account_balances: function(frm) {
        frappe.confirm(
            'Are you sure you want to refresh all account balances?',
            () => {
                frappe.call({
                    method: "digitz_erp.api.gl_posting_api.update_all_account_balances",
                    callback: function(r) {
                        frappe.msgprint("✅ Account balances refreshed successfully");
                    },
                    error: function(err) {
                        frappe.msgprint("❌ Failed to refresh account balances");
                    }
                });
            },
            () => {
                frappe.msgprint("❌ Action cancelled");
            }
        );
    },
	create_all_expense_heads: function(frm) {
        frappe.confirm(
            'Are you sure you want to create all missing expense heads?',
            () => {
                frappe.call({
                    method: "digitz_erp.api.expense_api.create_expense_heads_from_accounts",
                    callback: function(r) {
                        frappe.msgprint("✅ Expense heads created successfully");
                    },
                    error: function(err) {
                        frappe.msgprint("❌ Failed to create expense heads");
                    }
                });
            },
            () => {
                frappe.msgprint("❌ Action cancelled");
            }
        );
    },

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

	frm.set_query("default_product_expense_account", function() {
		return {
			"filters": {
				"is_group": 0,
				"root_type":"Expense"
			}
		};
	});

	frm.doc.rules_for_prices = "Default Selling Price List : Standard Selling" +
	"\nDefault Buying Price List : Standard Buying" +
	"\nUse Default price LIst when customer or supplier price not available: Yes"

});
