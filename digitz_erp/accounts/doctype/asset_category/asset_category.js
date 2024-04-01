// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Asset Category", {
	refresh(frm) {

	},
    setup(frm){

        frm.set_query("asset_account", function () {
			return {
				"filters": {
					"account_type": "Fixed Asset"                    
				}
			};
		});

        frm.set_query("depreciation_account", function () {
			return {
				"filters": {
					"account_type": "Depreciation"                    
				}
			};
		});

        frm.set_query("accumulated_depreciation_account", function () {
			return {
				"filters": {
					"account_type": "Accumulated Depreciation"                    
				}
			};
		});
    }
});
