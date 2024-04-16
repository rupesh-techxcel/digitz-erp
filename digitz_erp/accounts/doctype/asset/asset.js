// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Asset", {
	refresh(frm) {

	},
    setup(frm)
    {
        frm.set_query("item", function () {
			return {
				"filters": {
					"is_fixed_asset": 1 ,
					"disabled":0
				}
			};
		});

		frm.set_query("asset_credit_account", function () {
			return {
				"filters": {
					"root_type": "Liability" ,
					"is_group":0
				}
			};
		});

		
		frm.set_df_property('asset_credit_account', 'hidden', frm.doc.purchase_invoice);
		frm.set_df_property('opening_depreciation', 'hidden', frm.doc.purchase_invoice);
		frm.set_df_property('asset_credit_account', 'reqd', !frm.doc.purchase_invoice);
		frm.set_df_property('opening_depreciation', 'reqd', !frm.doc.purchase_invoice);


    },
	assign_defaults(frm){

		if(frm.is_new())
		{
			frappe.call(
				{
					method:'digitz_erp.api.settings_api.get_company_settings',
					async:false,
					callback(r){
						
						 console.log(r.message)
						 console.log(r.message[0])

						if (r.message && r.message[0] && r.message[0].default_asset_location) {
							frm.doc.asset_location = r.message[0].default_asset_location;
							refresh_field('asset_location'); // Refresh the field on the form to show the updated value
						} else {
							frappe.msgprint("The 'Default Asset Location' field has not been set in the company settings.");
						}						
					}
				}
			);
		}

	}

});

frappe.ui.form.on("Asset", "onload", function (frm) {

	frm.trigger("assign_defaults")

});
