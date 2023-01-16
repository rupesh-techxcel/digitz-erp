// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer', {
	
	setup:function(frm)
	{

		frm.set_query("area", function() {
			return {
				"filters": {
					"emirate": frm.doc.emirate
				}
			};
		});	
	},	 
	before_save: function(frm){

		var addressline_1 = frm.doc.address_line_1;
		var addressline_2 = "";
		
		if(frm.doc.address_line_1 && frm.doc.address_line_1 !="")
		{
			addressline_1 = frm.doc.address_line_1;
			console.log("address line 1")			
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
				console.log("address line 2")			
			}
			else
			{
				addressline_2 = frm.doc.address_line_2;			
			}			
		}

		var area = "";

		if( frm.doc.area)
		{
			console.log("area")	
			if((!addressline_1 && !addressline_2) || (addressline_1 =="" && addressline_2==""))
			{
				area = frm.doc.area_name
			}
			else
			{
				area = "\n" + frm.doc.area_name
			}
		}

		var emirate = "\n" + frm.doc.emirate;
		var country = "\n" + frm.doc.country;
		
		frm.doc.full_address = addressline_1 + addressline_2 + area + emirate+ country;
	},
	emirate(frm)
	{
		frm.doc.area = ""; //Change default area for the emirate selected
	}

});

frappe.ui.form.on("Customer", "onload", function(frm) {
	
})
