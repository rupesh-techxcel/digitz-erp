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
			
    }
	
})

frappe.ui.form.on("Supplier", "onload", function(frm) {
	
		
	});
