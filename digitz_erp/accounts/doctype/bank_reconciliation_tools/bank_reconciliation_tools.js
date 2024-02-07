// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bank Reconciliation Tools", {
	refresh(frm) {
	},
  get_bank_entries: function(frm){
		frappe.call({
    method: 'digitz_erp.accounts.doctype.bank_reconciliation_tools.bank_reconciliation_tools.get_all_bank_entries',
    args: {},
    callback: function(response) {
        var child_table = frm.fields_dict['bank_reconciliation_details'].grid;
        child_table.remove_all();
        for (var i = 0; i < response.message.length; i++) {
            var entry = response.message[i];
            var row = frappe.model.add_child(frm.doc, 'Bank Reconciliation Details', 'bank_reconciliation_details');
						row.bank_reconciliation = entry.name;
            row.reference_no = entry.reference_no;
            row.reference_date = entry.reference_date;
            row.status = entry.status;
            row.settlement_date = entry.settlement_date;
        }
        frm.refresh();
    }
});

}
});
