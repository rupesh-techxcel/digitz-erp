// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt


frappe.ui.form.on('Supplier', {

	setup: function(frm) {
        // your code here
        		
		if(frm.doc.__islocal == 1)
		{
			frm.doc.create_account_with_supplier_name_while_saving = 1
			frm.set_df_property("account_ledger","hidden",1); 
			frm.set_df_property("create_account_with_supplier_name_while_saving","read_only",1); 
		}
		else
		{
			frm.doc.create_account_with_supplier_name_while_saving = 0;
			frm.set_df_property("create_account_with_supplier_name_while_saving","hidden",1); 
			frm.set_df_property("create_account_with_supplier_name_while_saving","read_only",1); 
			frm.set_df_property("account_ledger","hidden",0); 
		}

        frappe.call({
            method: 'frappe.client.get_value',
            args:{
                'doctype':'Global Settings',
                'fieldname':'default_company'
            },
            callback: (r)=>{
				default_company =r.message.default_company       
				
				
					frappe.call(
					{
						method: 'frappe.client.get_value',
						args:{
							'doctype':'Company',
							'filters':{'company_name': default_company},
							'fieldname':['supplier_account_group']
						},
						callback:(r2)=>
						{
							console.log(r2.message.supplier_account_group)
							frm.doc.account_group = r2.message.supplier_account_group
						}
					}

				)	
            }
        })		
    }
	
})

frappe.ui.form.on("Supplier", "onload", function(frm) {

	if(frm.doc.__islocal == 1)
		{
			frm.doc.create_account_with_supplier_name_while_saving = 1
			frm.set_df_property("account_ledger","hidden",1); 
			frm.set_df_property("create_account_with_supplier_name_while_saving","read_only",1); 
		}
		else
		{
			frm.doc.create_account_with_supplier_name_while_saving = 0;
			frm.set_df_property("create_account_with_supplier_name_while_saving","hidden",1); 
			frm.set_df_property("create_account_with_supplier_name_while_saving","read_only",1); 
			frm.set_df_property("account_ledger","hidden",0); 
		}
	
		frm.set_query("account_group", function() {
			return {
				"filters": {					
					"account_type":"Creditors",
					"is_group": 1
				}
			};
		});

		frm.set_query("account_ledger", function() {
			return {
				"filters": {					
					"account_type":"Creditors",
					"is_group": 0
				}
			};
		});		
	});
