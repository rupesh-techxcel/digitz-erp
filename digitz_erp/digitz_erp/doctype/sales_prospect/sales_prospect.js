// Copyright (c) 2025, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Sales Prospect", {
	refresh: function(frm) {

        frm.set_query("area", function() {
			return {
				"filters": {
					"emirate": frm.doc.emirate
				}
			};
		});

        if (! frm.is_new())
        {
             // Check if the prospect already exists in any customer
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Customer',
                    filters: {
                        prospect: frm.doc.name
                    },
                    fields: ['name']
                },
                callback: function(r) {
                    // If no customer exists with this prospect, show the button
                    if (r.message.length === 0) {
                        frm.add_custom_button(__('Convert to Customer'), function() {
                            frappe.call({
                                method: 'digitz_hr_base.api.lead_prospect_api.convert_prospect_to_customer',
                                args: {
                                    prospect: frm.doc.name
                                },
                                callback: function(r) {
                                    if (r.message) {

                                        let doc = frappe.model.sync(r.message)[0];
                                        frappe.set_route('Form', 'Customer', doc.name);
                                        // Redirect to the newly created customer document
                                        //frappe.set_route('Form', 'Customer', r.message.name);
                                    }
                                }
                            });
                        });
                    }
                }
            });  

        }        
                  
    },
    emirate: function (frm) 
    {
        frm.set_value("area","")
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
});

