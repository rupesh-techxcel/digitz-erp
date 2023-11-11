// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt


frappe.ui.form.on('Supplier', {

	setup: function(frm) {
        // your code here

		frm.set_query("default_price_list", function() {
			return {
				"filters": {
					"is_buying": 1
				}
			};
		});		        		
			
    },
	refresh: function(frm) {
        frm.add_custom_button(__('Show Account Ledger'), function() {
			
            // Handle button click action here
            // You can use `frm.doc` to access the current document
            // For example, you can perform custom logic or open a dialog
        });
		
		frm.set_df_property("default_terms","hidden", frm.doc.use_default_supplier_terms)
		frm.set_df_property("terms","hidden", frm.doc.use_default_supplier_terms)
    },
	before_save: function(frm){

		var address = frm.doc.address;

		var city = frm.doc.city;

		if(typeof(frm.doc.address) != "undefined" && frm.doc.address !="" )
		{
			if(typeof(frm.doc.city) != "undefined" && frm.doc.city !="" )
			{
				city = "\n" + frm.doc.city;
			}
			else
			{
				city ="";
			}
		}		
		else
		{
			address = "";

		}

		var state = frm.doc.state;

		if(typeof(frm.doc.state) != "undefined" && frm.doc.state !="")
		{
			state = "\n" + frm.doc.state
		}
		else
		{
			state ="";
		}
		
		var country = "\n" + frm.doc.country;
		
		frm.doc.full_address = address + city + state + country;
	},
	use_default_supplier_terms(frm)
	{
		frm.set_df_property("default_terms","hidden", frm.doc.use_default_supplier_terms)
		frm.set_df_property("terms","hidden", frm.doc.use_default_supplier_terms)
	}
});
	

frappe.ui.form.on("Supplier", "onload", function(frm) {
	
		
	});

