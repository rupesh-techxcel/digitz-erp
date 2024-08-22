// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Advance Entry", {
	refresh(frm) {
        // frm.add_custom_button(__("Create Pro"))
        console.log("refresh")
	},
    setup(frm){
        if(frm.is_new()){
            console.log("setup")
            let row = frm.add_child('advance_item_table');

            if (frm.doc.project) {
                row.description = "Advance for the project " + frm.doc.project;
            } else {
                row.description = "Advance payment";
            }

            frm.trigger('get_default_company_and_warehouse');   

            frm.add_fetch('customer', 'full_address', 'customer_address')
		    frm.add_fetch('customer', 'salesman', 'salesman')
		    frm.add_fetch('customer', 'tax_id', 'tax_id')
        }
    },
    onload(frm){
        console.log("onload")
    },
    project(frm)
    {
        frm.clear_table('advance_item_table');
        let row = frm.add_child('advance_item_table');
        row.description = "Advance for the project " + frm.doc.project
        frm.refresh_field('advance_item_table')
        frm.trigger('get_customer_details')
    },  
    customer(frm)  
    {
        frm.trigger('get_customer_details')
    },
    get_customer_details(frm)
    {
        
        frappe.call(
        {
            method: 'digitz_erp.api.customer_api.get_customer_details',
            args: {
                'customer': frm.doc.customer
            },
            callback: (r) => {
                console.log("r")
                console.log(r)
                frm.set_value('customer_display_name',r.message.customer_name)
                frm.refresh_field("customer_display_name");
            }
        });

        frappe.call(
            {
                method: 'digitz_erp.accounts.doctype.gl_posting.gl_posting.get_party_balance',
                args: {
                    'party_type': 'Customer',
                    'party': frm.doc.customer
                },
                callback: (r) => {
                    console.log("r")
                    console.log(r)
                    frm.set_value('customer_balance',r.message)
                    frm.refresh_field("customer_balance");
                }
            });
    
            frm.set_value('customer_display_name', frm.doc.customer)
            frm.refresh_field("customer_display_name");
    },
    get_default_company_and_warehouse(frm) {

		var default_company = ""

		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				'doctype': 'Global Settings',
				'fieldname': 'default_company'
			},
			callback: (r) => {

				default_company = r.message.default_company
				
                frm.set_value("company",default_company)
				
				frappe.call(
                {
                    method: 'frappe.client.get_value',
                    args: {
                        'doctype': 'Company',
                        'filters': { 'company_name': default_company },
                        'fieldname': ['default_advance_received_account']
                    },
                    callback: (r2) => {
                        frm.doc.advance_account = r2.message.default_advance_received_account
                        console.log(r2)

                    }
                }
				)
			}
		})

	},
    
    
});


frappe.ui.form.on("Advance Entry Item",{
    amount(frm,cdt,cdn){
        let row = frappe.get_doc(cdt,cdn);
        if(row.tax_rate){
            let tax_amount = row.amount * row.tax_rate/100;
            frappe.model.set_value(cdt,cdn,'tax_amount',tax_amount);
        }
        update_net_amount(frm,cdt,cdn)
        // frm.trigger('tax');
        update_net_total(frm);
    },
    advance_item_table_remove(frm){
        update_net_total(frm);
    },
    tax(frm,cdt,cdn){
        update_tax_amount(frm,cdt,cdn);
        update_net_amount(frm,cdt,cdn)
        update_net_total(frm);
    },
    tax_rate(frm,cdt,cdn){
        update_tax_amount(frm,cdt,cdn);
        update_net_amount(frm,cdt,cdn);

        update_net_total(frm);
    }
})

function update_net_amount(frm,cdt,cdn){
    let row = frappe.get_doc(cdt,cdn);
    // frm.trigger('tax')
    let tax_amount = row.tax_amount || 0;
    frappe.model.set_value(cdt,cdn,'net_amount',(row.amount + tax_amount))
}
function update_tax_amount(frm,cdt,cdn){
    let row = frappe.get_doc(cdt,cdn);
    let tax_amount = 0;
        if(row.tax_rate){
            tax_amount = (row.amount * row.tax_rate)/100;
        }
        frappe.model.set_value(cdt,cdn,'tax_amount',tax_amount);
}
function update_net_total(frm){
    let net_total = 0;
    frm.doc.advance_item_table.forEach(item =>{
        net_total += item.net_amount;
    })

    frm.set_value("net_total",net_total);
}