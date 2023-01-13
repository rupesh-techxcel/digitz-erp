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
		
		if(typeof(frm.doc.address_line_2) != "undefined" && frm.doc.address_line_2 !="")
		{
			addressline_2 = "\n" + frm.doc.address_line_2			
		}

		var area = "";

		if(typeof(frm.doc.area) != "undefined")
		{
			area = "\n" + frm.doc.area
		}

		var emirate = "\n" + frm.doc.emirate;
		var country = "\n" + frm.doc.country;
		
		frm.doc.full_address = addressline_1 + addressline_2 + area + emirate+ country;
	}
});

frappe.ui.form.on("Customer", "onload", function(frm) {
	
})
