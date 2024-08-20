// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Project Budget", {
	refresh(frm) {

	},
});

frappe.ui.form.on("Project Budget Item Table", {
    rate(frm,cdt,cdn){
        let row = frappe.get_doc(cdt,cdn);
        frappe.model.set_value(cdt, cdn, 'gross_amount', (row.qty * row.rate));
        frm.refresh_fields('items');
    },
    qty(frm,cdt,cdn){
        let row = frappe.get_doc(cdt,cdn);
        frappe.model.set_value(cdt, cdn, 'gross_amount', (row.qty * row.rate));
        frm.refresh_fields('items');
    },
    gross_amount(frm,cdt,cdn){
        let row = frappe.get_doc(cdt,cdn);
        if(!row.tax_excluded && row.tax && (row.tax_rate > 0)){
            console.log("I am finding the tax and net amount.")
            let tax_amount = (row.gross_amount * row.tax_rate)/100;
            frappe.model.set_value(cdt, cdn, 'tax_amount', tax_amount);
            console.log(tax_amount)
        }

        frappe.model.set_value(cdt,cdn, 'net_amount', (row.gross_amount + row.tax_amount));
        update_total_amounts(frm);
    },
    tax_excluded(frm,cdt,cdn){
        let row = frappe.get_doc(cdt, cdn);
        frappe.model.set_value(cdt,cdn,'tax',"");
        frappe.model.set_value(cdt,cdn,'tax_rate',0);
        frappe.model.set_value(cdt,cdn,'tax_amount',0);
        frappe.model.set_value(cdt,cdn, 'net_amount', (row.gross_amount));
    },
    tax(frm,cdt,cdn){
        let row = frappe.get_doc(cdt, cdn);
        if(row.tax_rate){
            let tax_amount = (row.gross_amount * row.tax_rate)/100;
            frappe.model.set_value(cdt, cdn, 'tax_amount', tax_amount);

            frappe.model.set_value(cdt,cdn, 'net_amount', (row.gross_amount + row.tax_amount));
            
            update_total_amounts(frm);

            frm.refresh_fields('net_amount');
        }
    },
    tax_rate(frm, cdt,cdn){
        let row = frappe.get_doc(cdt, cdn);
        if(row.tax_rate){
            let tax_amount = (row.gross_amount * row.tax_rate)/100;
            frappe.model.set_value(cdt, cdn, 'tax_amount', tax_amount);
            frm.refresh_fields('tax_amount');
            frappe.model.set_value(cdt,cdn, 'net_amount', (row.gross_amount + row.tax_amount));
            frm.refresh_fields('net_amount');

            update_total_amounts(frm);

        }
    },
    items_remove(frm,cdt,cdn){
        update_total_amounts(frm);
    }
})



function update_total_amounts(frm){
        let gross_total = 0;
        let tax_total = 0;
        let net_total = 0;
        frm.doc.items.forEach(element => {
            gross_total += element.gross_amount;
            tax_total += element.tax_amount;
            net_total += element.net_amount;
        });

        frm.set_value('gross_total', gross_total);
        frm.set_value('tax_total', tax_total);
        frm.set_value('net_total', net_total);
}