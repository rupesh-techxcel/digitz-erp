// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('User Warehouse', {
    onload: function(frm) {
        let current_user = frappe.session.user;
        frappe.call({
            method: 'digitz_erp.accounts.doctype.user_warehouse.user_warehouse.check_user_entry',
            args: {
                user: current_user
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_df_property('warehouse', 'read_only', 1);
                } else {
                    frm.set_df_property('warehouse', 'read_only', 0);
                }
            }
        });
        frm.set_query("warehouse", function() {
    			return {
    				"filters": {
    					"is_disabled": 0
    				}
    			};
    		});
    }
});
