// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Mode', {
	// refresh: function(frm) {

	// }

	mode(frm)
	{
		console.log(frm.doc.mode);
		if(frm.doc.mode == "Bank")
		{
			frm.set_query("account", function() {
				console.log("for bank");
		
				return {
				"filters": {
					"account_type": "Bank",
					"is_group": 0
					}
				};
			});
		}
		else
		{
			frm.set_query("account", function() {
				console.log("for cash");		
				return {
				"filters": {
					"account_type": "Cash",
					"is_group": 0
				}
			};
		});
		}
	}	
});

frappe.ui.form.on("Payment Mode", "onload", function(frm) {
	//Since the default selectionis cash
		frm.set_query("account", function() {
			return {
				"filters": {
					//"account_type": ["in", ["Bank","Cash"]],
					"account_type":"Cash",
					"is_group": 0
				}
			};
		});
	});


