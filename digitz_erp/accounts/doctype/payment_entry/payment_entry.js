// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Entry', {
	// refresh: function(frm) {

	// }
});


frappe.ui.form.on("Payment Entry Detail", {
	sup_and_exp:function(frm,cdt,cdn){
		var row = locals[cdt][cdn]
		if (row.sup_and_exp == 'Supplier'){
			frappe.db.get_value("Company", "Dolphin Chemicals", "default_payable_account").then((r) => {
					var default_payable_account = r.message.default_payable_account
					frappe.model.set_value(cdt,cdn,'account',default_payable_account)
					
			})
		}if (row.sup_and_exp !="Supplier"){
			frappe.model.set_value(cdt,cdn,'account',"")

		}
	},
	supplier:function(frm,cdt,cdn){
		frappe.call(
			{
				method: 'digitz_erp.accounts.doctype.payment_entry.payment_entry.create_dr_supplier_entry',
				args:{doc:frm.doc},		
				callback: (r) => {
					frm.doc.payment_allocation = []
					$.each(r.message,function(idx,elm){
						var row = frm.add_child("payment_allocation");
						row.purchase = elm.name
						row.paid_amount = elm.gross_total

					})
					frm.refresh_field("payment_allocation")
				}
			});


	}


});