frappe.ui.form.on('Payment Entry', {
	// refresh: function(frm) {

	// }
});

frappe.ui.form.on("Payment Entry Detail", {
	sup_and_exp: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.sup_and_exp == 'Supplier') {
			frappe.db.get_value("Company", "Dolphin Chemicals", "default_payable_account").then((r) => {
				var default_payable_account = r.message.default_payable_account;
				frappe.model.set_value(cdt, cdn, 'account', default_payable_account);
			});
		}
		else {
			frappe.model.set_value(cdt, cdn, 'account', '');
		}
	},

	supplier: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		var existing_suppliers = [];

		// check if the selected supplier already exists in any other row
		frm.doc.payment_entry_details.forEach(function(d) {
			if (d.supplier && d.supplier === row.supplier && d.name !== row.name) {
			existing_suppliers.push(d.supplier);
		}
		});

		// if (existing_suppliers.length > 0) {
		// 	frappe.model.set_value(cdt, cdn, 'supplier', '');
		// 	frappe.throw(__('Supplier already exists in another row.'));
		// 	return;
		// }

		frappe.call({
			method: 'digitz_erp.accounts.doctype.payment_entry.payment_entry.create_dr_supplier_entry',
			args: { doc: frm.doc,
				"supplier":row.supplier
				},
			callback: (r) => {
				if (r.message == "No pending invoice") {
					frappe.throw(`No pending invoice for supplier ${row.supplier}`, () => {
					});
				}
				frappe.model.set_value(cdt, cdn, 'payment_entry_details', r.message);
			}
		});
	},

    allocation: function(frm, cdt, cdn){
    
        frappe.msgprint("allocatiuon");

    },


	payment_entry_details: function(frm, cdt, cdn) {

    },

    view:function(frm,cdt,cdn) {
    	var row = locals[cdt][cdn];
        var link_field_value = row.payment_entry_details;
        var child_table_control;

        

        frappe.call({
			        method: "digitz_erp.accounts.doctype.payment_entry.payment_entry.check_for_new_record",
			        args: {
						"payment_entry_details":link_field_value,
						"supplier":row.supplier
			        },
			        callback: function(response) {
			        	dialog.hide();			            
			        }
				});

        if (link_field_value) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Payment entry Details",
                    name: link_field_value,
                },
                callback(r) {
                    if (r.message) {
                        var doc = r.message;
                        var child_table_data = doc.payment_allocation;

                        child_table_control = frappe.ui.form.make_control({
                            df: {
                                fieldname: "payment_allocation",
                                label: "Payment Allocation",
                                fieldtype: "Table",
                                cannot_add_rows:true,
                                fields: [
                                    {
                                        fieldtype: "Link",
                                        fieldname: "purchase",
                                        label: "Purchase Invoice",
                                        options:"Purchase Invoice",
                                        in_place_edit: true,
                                        in_list_view: true,
                                        width: "100px",
                                        read_only:true
                                    },
                                    {
                                        fieldtype: "Float",
                                        fieldname: "paid_amount",
                                        label: "Paid Amount",
                                        in_place_edit: false,
                                        in_list_view: true,
                                        width: "100px",
                                        read_only:true
                                    },
                                    {
                                        fieldtype: "Float",
                                        fieldname: "invoice_ammount",
                                        label: "Invoice Amount",
                                        in_place_edit: false,
                                        in_list_view: true,
                                        width: "100px",
                                        read_only:true
                                    },
                                    {
                                        fieldtype: "Float",
                                        fieldname: "balance_ammount",
                                        label: "Balance Amount",
                                        in_place_edit: false,
                                        in_list_view: true,
                                        width: "100px",
                                        read_only:true
                                    },
                                    {
                                        fieldtype: "Float",
                                        fieldname: "pay",
                                        label: "Pay",
                                        in_place_edit: true,
                                        in_list_view: true,
                                        width: "100px",
                                    }
                                ],
                            },
                            parent: dialog.get_field("purchase").$wrapper,
                            render_input: true,
                        });
                        child_table_control.df.data = child_table_data;
                        child_table_control.refresh();
                    }
                }
            });

            var dialog = new frappe.ui.Dialog({
                title: "Payment Allocation",
                width: '100%',
                fields: [
                    {
                        fieldtype: "HTML",
                        fieldname: "purchase",
                        label: "Payment Allocation",
                        options: '<div id="child-table-wrapper"></div>',
                    },
                ],
                primary_action: function() {
                    var child_table_data_updated = child_table_control.get_value();
                    var payment_entry_details =  row.payment_entry_details
                    var supplier = row.supplier
                    
                    frappe.call({
				        method: "digitz_erp.accounts.doctype.payment_entry.payment_entry.update_payment",
				        args: {
				            "child_table_data": child_table_data_updated,
				            "supplier":supplier
				        },
				        callback: function(response) {
				        	dialog.hide();
				        	var totalPay = response.message
				        	frappe.model.set_value(cdt, cdn, 'total_amount', totalPay);
				            
				        }
				    });
                },


            });
            dialog.show();
        }
    }

});

