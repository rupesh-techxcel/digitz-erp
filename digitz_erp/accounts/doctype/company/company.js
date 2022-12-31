// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Company', {
	// refresh: function(frm) {

	// }
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
		frm.set_query("customer_account_group", function() {
			return {
				"filters": {
					//"account_type": ["in", ["Bank","Cash"]],
					"account_type":"Debtors",
					"is_group": 1
				}
			};
		});
		
		frm.set_query("supplier_account_group", function() {
			return {
				"filters": {
					//"account_type": ["in", ["Bank","Cash"]],
					"account_type":"Creditors",
					"is_group": 1
				}
			};
		});
	});