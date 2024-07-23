// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Stock Repost", {
	refresh(frm) {

        frm.add_custom_button('Stock Repost', () => {
            frm.call("stock_repost")
        });

        // frm.add_custom_button('GL Repost', () => {
        //     frm.call("do_repost")
        // });

	},
});
