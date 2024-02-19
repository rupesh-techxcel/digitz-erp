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

		// Use the nullish coalescing operator to default to an empty string if the value is null or undefined
		var address = frm.doc.address ?? '';
		var city = frm.doc.city ?? '';
		var state = frm.doc.state ?? '';
		var country = frm.doc.country ?? '';

		// Concatenate with a newline separator, ensuring no 'null' or 'undefined' values are added
		frm.doc.full_address = (address ? address + '\n' : '') +
					(city ? city + '\n' : '') +
					(state ? state + '\n' : '') +
					(country || ''); // Assuming country is always defined; if not, use ?? like others

		// Trim the trailing newline for cases where not all components are present
		frm.doc.full_address = frm.doc.full_address.replace(/\n$/, '');	
	},
	use_default_supplier_terms(frm)
	{
		frm.set_df_property("default_terms","hidden", frm.doc.use_default_supplier_terms)
		frm.set_df_property("terms","hidden", frm.doc.use_default_supplier_terms)
	}
});
	

frappe.ui.form.on("Supplier", "onload", function(frm) {
	
		
	});

