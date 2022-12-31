// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item', {
	 setup: function(frm) {
		if(frm.is_new() == 1)
		{
			frappe.call({
				method: 'frappe.client.get_value',
				args:{
					'doctype':'Global Settings',
					'fieldname':'default_company'
				},
				callback: (r)=>{
					
						frappe.call(
						{
							method: 'frappe.client.get_value',
							args:{
								'doctype':'Company',
								'filters':{'company_name': r.message.default_company},
								'fieldname':['tax']
							},
							callback:(r2)=>
							{
								console.log('Tax')
								console.log(r2.message.tax)
								frm.doc.tax = r2.message.tax;																							
							}
						}
					)	
				}
			})
		}
	 },
	tax_excluded(frm)
	{
		frm.set_df_property("tax","read_only",frm.doc.tax_excluded);
		
	   if(frm.doc.tax_excluded)
	   {
		   console.log("Tax excluded?");
		   console.log(frm.doc.tax_excluded);
		   frm.doc.tax ="";		
		   frm.refresh_field("tax");   	
	   }
	},
	validate: function(frm)
	{	
		console.log("validate event");
		console.log("Base Unit");
		console.log(frm.doc.base_unit);

		var baseUnitFound = false;

		try
		{
		frm.doc.units.forEach(function(entry) { 
			if(frm.doc.base_unit == entry.unit)
			{
				baseUnitFound= true;
			}
		});
		}
		catch(err)
		{

		}
		console.log("baseUnitFound");
		console.log(baseUnitFound);

		if(!baseUnitFound)
		{
			var baseuom = frm.add_child("units");
			baseuom.unit = frm.doc.base_unit;
			baseuom.conversion_factor = 1;
			baseuom.parent = doc.item;
			console.log("Base UOM")
			console.log(baseuom);
		}
	}
});

frappe.ui.form.on("Item", "onload", function(frm) {

	var default_company = ""
	console.log("Is New")
	console.log(frm.is_new())

	if(frm.is_new())
	{
			console.log("New doc");

			frappe.call({
				method: 'frappe.client.get_value',
				args:{
					'doctype':'Global Settings',
					'fieldname':'default_company'
				},
				callback: (r)=>{
					
						frappe.call(
						{
							method: 'frappe.client.get_value',
							args:{
								'doctype':'Company',
								'filters':{'company_name': r.message.default_company},
								'fieldname':['tax']
							},
							callback:(r2)=>
							{
								console.log('Tax')
								console.log(r2.message.tax)
								frm.doc.tax = r2.message.tax;		
																					
							}
						}

					)	
				}
			})
		}

	}
);

