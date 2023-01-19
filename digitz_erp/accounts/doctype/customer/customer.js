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
		}
		else
		{
			addressline_1 = "";
		}

		
		if(frm.doc.address_line_2 && frm.doc.address_line_2 !="")
		{
			if(addressline_1 !="")
			{
				addressline_2 = "</br>" + frm.doc.address_line_2;				
			}
			else
			{
				addressline_2 = frm.doc.address_line_2;			
			}			
		}

		var area = "";

		console.log("1");
		if(frm.doc.area_name && frm.doc.area_name !="")
		{			
			if((!addressline_1 && !addressline_2) || (addressline_1 =="" && addressline_2==""))
			{
				area = frm.doc.area_name;								
			}
			else
			{
				area = "</br>" + frm.doc.area_name;
			}
		}
		else
		{
			
		}

		var emirate = "</br>" + frm.doc.emirate;
		var country = "</br>" + frm.doc.country;
		
		frm.doc.full_address = "<p>" + addressline_1 + addressline_2  + area + emirate +  country + "</p>"
		console.log(frm.doc.full_address);

		
	},
	emirate(frm)
	{
		frm.doc.area = ""; //Change default area for the emirate selected
	}

});

frappe.ui.form.on("Customer", "onload", function(frm) {
	
})
