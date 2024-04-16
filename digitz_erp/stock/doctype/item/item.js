// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item', {
	refresh: function(frm) {
		if (frm.is_new()) {
			// frappe.db.get_value('Company', frm.doc.company, 'tax_excluded', function(r) {
			// 	if (r && r.tax_excluded === 1) {
			// 		frm.set_value('tax_excluded', 1);
			// 	}
			// });
			frappe.db.get_value('Company', frm.doc.company, 'maintain_stock', function(r) {
				if (r && r.maintain_stock === 1) {
						frm.set_value('maintain_stock', 1);
				}
			});
	}
 },
	 setup: function(frm) {
		frm.set_query("asset_category", function () {
			return {
				"filters": {
					"is_disabled": 0
				}
			};
		});
	 },
	 assign_defaults(frm)
	 {
		if(frm.is_new())
		{
			frm.trigger("get_default_company_and_settings");
			frm.trigger("assign_default_tax");
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
	assign_default_tax(frm)
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
							frm.refresh_field("tax");
						}
					}
				)
			}
		})
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
			baseuom.parent = frm.doc.item;
			console.log("Base UOM")
			console.log(baseuom);
		}
	},
	before_save: function(frm)
	{
		if(!frm.doc.tax_excluded)
		{
			if(!frm.doc.tax)
			{
				frm.trigger("assign_default_tax");
			}
		}
		else
		{
			frm.doc.tax ="";
		}
	},
	standard_buying_price:function(frm)
	{
		frm.trigger("get_margin_from_rates");
	},
	standard_selling_price:function(frm)
	{
		frm.trigger("get_margin_from_rates");		
	},
	margin_:function(frm)
	{
		if(!isNaN(frm.doc.standard_buying_price) && !isNaN(frm.doc.margin_))
		{
			selling_price = parseFloat(frm.doc.standard_buying_price) + (parseFloat(frm.doc.standard_buying_price) * parseFloat(frm.doc.margin_) / 100)

			frm.doc.standard_selling_price = selling_price

			frm.refresh_field("standard_selling_price")


		}
	},
	is_fixed_asset(frm)
	{
		if(frm.doc.is_fixed_asset)
		{			
			frm.set_value("maintain_stock",false)
		}
	},
	maintain_stock(frm)
	{
		if(frm.doc.maintain_stock)
		{
			frm.set_value("is_fixed_asset",false)			
		}

	},
	get_margin_from_rates(frm)
	{
		if(!isNaN(frm.doc.standard_buying_price) && !isNaN(frm.doc.standard_selling_price))
		{
			margin = (parseFloat(frm.doc.standard_selling_price) / parseFloat(frm.doc.standard_buying_price) *100) - 100			
			frm.doc.margin_ = margin
			frm.refresh_field("margin_")
		}
	},
	get_default_company_and_settings(frm)
	{

		var default_company = ""
	
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
									frm.refresh_field("tax");

								}
							}

						)
					}
				});
			}
			
			if (frappe.user.has_role('Management')) {
				console.log("supplier prices visisble")
				// Show the child table if the user is an Administrator            
				frm.set_df_property('supplier_rates', 'hidden', false); // This will hide the 'supplier_rates' field

			} else {
				// Hide the child table if the user is not an Administrator
				frm.set_df_property('supplier_rates', 'hidden', true); // This will hide the 'supplier_rates' field

				frm.toggle_display('supplier_rates', false); // This will hide the 'supplier_rates' field

				console.log("supplier prices hidden")
			}
		}

});

frappe.ui.form.on("Item", "onload", function(frm) {

	frm.trigger("assign_defaults");
	}
);

