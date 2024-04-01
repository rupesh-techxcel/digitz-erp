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
					"is_fixed_asset": 1                  
				}
			};
		});
    }
});
