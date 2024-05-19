// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer', {
	
	refresh:function(frm)
	{

		frm.add_custom_button(__('Merge Customer'), function() {
            // Open the merge popup
            open_merge_popup(frm);
        });

		frm.set_query("area", function() {
			return {
				"filters": {
					"emirate": frm.doc.emirate
				}
			};
		});	

		frm.set_query("default_price_list", function() {
			return {
				"filters": {
					"is_selling": 1
				}
			};
		});	

		frm.set_query("salesman", function() {
			return {
				"filters": {
					"disabled": 0,
					"status": ["!=", "On Boarding"]
				}
			};
		});

		frm.set_df_property("default_terms","hidden", frm.doc.use_default_customer_terms)
		frm.set_df_property("terms","hidden", frm.doc.use_default_customer_terms)
	},	 
	before_save: function(frm){

		var addressline_1 = frm.doc.address_line_1;
		var addressline_2 = "";
		
		if(frm.doc.address_line_1 && frm.doc.address_line_1 !="")
		{
			addressline_1 = frm.doc.address_line_1;			
		}
		else
		{
			addressline_1 = "";
		}
		
		if(frm.doc.address_line_2 && frm.doc.address_line_2 !="")
		{
			if(addressline_1 !="")
			{
				addressline_2 = "\n" + frm.doc.address_line_2;				
			}
			else
			{
				addressline_2 = frm.doc.address_line_2;			
			}			
		}

		var area = "";
		
		if(frm.doc.area_name && frm.doc.area_name !="")
		{			
			if((!addressline_1 && !addressline_2) || (addressline_1 =="" && addressline_2==""))
			{
				area = frm.doc.area_name;								
			}
			else
			{
				area = "\n" + frm.doc.area_name;
			}
		}
		else
		{
			
		}

		var emirate = "\n" + frm.doc.emirate;
		var country = "\n" + frm.doc.country;
		
		frm.doc.full_address = addressline_1 + addressline_2  + area + emirate +  country + "\n"
		console.log(frm.doc.full_address);
	},
	emirate(frm)
	{
		// frm.doc.area = ""; //Change default area for the emirate selected
		frm.set_value("area","")
	},
	use_default_customer_terms(frm)
	{
		frm.set_df_property("default_terms","hidden", frm.doc.use_default_customer_terms)
		frm.set_df_property("terms","hidden", frm.doc.use_default_customer_terms)
	}

});

frappe.ui.form.on("Customer", "onload", function(frm) {
	
})


function open_merge_popup(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Merge Customer'),
        fields: [
            {
                fieldtype: 'HTML',
                options: `
                    <div style="color: red; font-weight: bold;">
                        Warning: Merging customers is irreversible. Please proceed with caution.
                    </div>
                    <div style="margin-top: 10px;">
                        <p>The system expects this merging operation to avoid duplication of records.</p>
                        <p>Only the details of the merged customer will persist in the system.</p>
                    </div>`
            },
            {
                label: __('Current Customer'),
                fieldname: 'current_customer',
                fieldtype: 'Data',
                read_only: 1,
                default: frm.doc.name
            },
            {
                label: __('Select Customer to Merge'),
                fieldname: 'merge_customer',
                fieldtype: 'Link',
                options: 'Customer',
                reqd: 1
            }
        ],
        primary_action_label: __('Merge'),
        primary_action(values) {
            // Call the merge function
            merge_customer(frm, values.merge_customer);
            d.hide();
			frappe.set_route("List", "Customer"); 
        }
    });

    d.show();
}


function merge_customer(frm, merge_customer) {
    frappe.call({        
		method: 'digitz_erp.api.customer_api.merge_customer',
        args: {
            current_customer: frm.doc.name,
            merge_customer: merge_customer
        },
        callback: function(r) {
            if (!r.exc) {
                frappe.msgprint(__('Customers merged successfully.'));
                frm.reload_doc();
            } else {
                frappe.msgprint(__('An error occurred while merging the customers.'));
            }
        }
    });
}