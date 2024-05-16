// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer', {
	
	refresh:function(frm)
	{

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
