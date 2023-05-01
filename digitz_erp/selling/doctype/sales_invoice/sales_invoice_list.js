frappe.listview_settings['Sales Invoice'] = {
    refresh: function(me) {
		
		console.log("listview_settings")

        me.page.add_action_item(__('Submit'), function() {
            var selected_docs = me.get_checked_items();
            if(selected_docs.length > 0) {
                frappe.confirm(__('Are you sure you want to submit selected documents?'), function() {

					selected_docs.forEach(function(doc) {
                        frappe.call({
                            method: 'digitz_erp.api.sales_invoice_api.submit_sales_invoice',
                            async: false,
                            args: {
                                docname: doc.name
                            },
                            callback: (r) => {

                            }
        
                       
                    })
                });
            })
            } else {
                frappe.msgprint(__('Please select at least one document.'));
            }
        });
    }
}
