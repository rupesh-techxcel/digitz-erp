// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Invoice', {
	
	setup: function(frm){

		frm.add_fetch('supplier','account_ledger','supplier_account')
		frm.add_fetch('supplier','tax_id','tax_id')
		frm.add_fetch('supplier','supplier_name','supplier_name')	
		frm.add_fetch('supplier','credit_days','credit_days')
		frm.get_field('taxes').grid.cannot_add_rows = true;
		
	},	
	supplier(frm)
	{		

	},
	edit_posting_date_and_time(frm)
	{
		console.log("here");
		
		//console.log(frm.doc.edit_posting_date_and_time);
		console.log(frm.doc.edit_posting_date_and_time);
		
	 	if(frm.doc.edit_posting_date_and_time ==1)
	 	{
	 		frm.set_df_property("posting_date","read_only",0);
			 frm.set_df_property("posting_time","read_only",0);
	 	}
	 	else
	 	{
	 		frm.set_df_property("posting_date","read_only",1);
			frm.set_df_property("posting_time","read_only",1);
	 	}  
	},
	credit_purchase(frm)	
	{
		 frm.set_df_property("payment_mode","hidden",frm.doc.credit_purchase);
		 frm.set_df_property("payment_account","hidden",frm.doc.credit_purchase);

		if(frm.doc.credit_purchase)
		{
			frm.doc.payment_mode ="";
			frm.doc.payment_account ="";			
		}
	},
	warehouse(frm)
	{
		console.log("warehouse set")
		console.log(frm.doc.warehouse)
	},
	make_taxes_and_totals(frm)	
	{
		console.log("from make totals..")
		frm.clear_table("taxes");
		frm.refresh_field("taxes");		
		
		frm.doc.items.forEach(function(entry) { 
			console.log("Item in Row")	
			console.log(entry.item);		
			var tax_in_rate = 0;
			if(entry.rate_included_tax)
			{
				tax_in_rate = entry.rate * (entry.tax_rate/ (100 + entry.tax_rate));
				entry.rate_excluded_tax = entry.rate - tax_in_rate;
				entry.net_amount = entry.qty * entry.rate - (entry.qty* entry.rate * (entry.tax_rate/(100 + entry.tax_rate) ));
			}
			else
			{
				entry.rate_excluded_tax = entry.rate;
				entry.tax_amount = ((entry.qty* entry.rate ) * (entry.tax_rate /100))
				entry.net_amount = entry.qty* entry.rate + ((entry.qty* entry.rate ) * (entry.tax_rate /100))
			}			

			
			entry.gross_amount = entry.qty * entry.rate_excluded_tax;
		
			var taxesTable = frm.add_child("taxes");
			taxesTable.tax = entry.tax;
			
			frm.refresh_field("items");		
			frm.refresh_field("taxes");
		
	});
	},
	get_default_warehouse(frm)
	{
		var default_company =""	
		console.log("From Get Default Warehouse Method in the parent form")

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
							'fieldname':['default_warehouse']
						},
						callback:(r2)=>
						{		
							console.log("Before assign default warehouse");				
							console.log(r2.message.default_warehouse);
							frm.doc.warehouse =	 r2.message.default_warehouse;		
							console.log(frm.doc.warehouse);
							frm.refresh_field("warehouse");	
						}
					}

				)	
			}
		})

	}
});


frappe.ui.form.on("Purchase Invoice", "onload", function(frm) {

	//Since the default selectionis cash
	//frm.set_df_property("date","read_only",1);	
	frm.set_query("warehouse", function() {
		return {
			"filters": {
				"is_group": 0
			}
		};
	});	

	frm.trigger("get_default_warehouse");	

});


frappe.ui.form.on('Purchase Invoice Item', {
    // cdt is Child DocType name i.e Quotation Item
    // cdn is the row name for e.g bbfcb8da6a
    item(frm, cdt, cdn) {        
		let row = frappe.get_doc(cdt, cdn);
		
		console.log(row.item);
		console.log(row.qty);
		let doc = frappe.model.get_value("", row.item);   
		console.log(doc);
		row.warehouse = frm.doc.warehouse;
		console.log(row.warehouse);
		frm.trigger("make_taxes_and_totals");

		frappe.call(
			{
				method: 'frappe.client.get_value',
				args:{
					'doctype':'Item',
					'filters':{'item_name': row.item},
					'fieldname':['item_code','base_unit','tax','tax_excluded']
				},
				callback:(r)=>
				{
					console.log('Item Code');
					console.log(r.message.item_code);	
					console.log(r.message.base_unit);	
					console.log(r.message.tax);
					console.log(r.message.tax_excluded);		
					row.item_code = r.message.item_code;	
					//row.uom = r.message.base_unit;	
					row.tax_excluded = r.message.tax_excluded;
					row.base_unit = r.message.base_unit;
					row.unit = r.message.base_unit;
					row.conversion_factor = 1;

										
					if(!r.message.tax_excluded)		
					{					
					
						frappe.call(
							{
								method:'frappe.client.get_value',
								args:{
									'doctype':'Tax',
								'filters':{'tax_name': r.message.tax},
								'fieldname':['tax_name','tax_rate']
								},
								callback:(r2)=>
								{
									row.tax = r2.message.tax_name;
									row.tax_rate = r2.message.tax_rate
								}	

							})
					 }
					 else
					 {
						row.tax = "";
						row.tax_rate = 0;					
					 }		

					 frm.refresh_field("items");

				}			
				
			});			
			

			// var child = locals[cdt][cdn];
			// var grid_row = frm.fields_dict['items'].grid.grid_rows_by_docname[child.name];
			// var field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "uom"})[0];
			// console.log(grid_row);
			// field.set_query =  function(){
			// 	return {
			// 	   filters: { parent: row.item}
			// 	}
			//   }

			 



			// frappe.call(
			// 	{
			// 		method:'digitz_erp.events.common_methods.get_item_uoms',
			// 		async:false,
			// 		args:{
			// 			'item': row.item,						
			// 			'fieldname':['uom']
			// 		},
			// 		callback(r)	
			// 		{
			// 			console.log(r.message);
			// 		//	row.set_df_property("uom", "options",r.message.uom);
			// 			//row.uom.options = r.message.uom;
			// 		}

			// 	}
			// );
    },
	tax_excluded(frm, cdt, cdn) {        
		let row = frappe.get_doc(cdt, cdn);	
		
		if(row.tax_excluded)
		{
			row.tax ="";
			row.tax_rate = 0;			
			frm.refresh_field("items");	
			frm.trigger("make_taxes_and_totals");
		}
	},
	tax(frm,cdt,cdn)
	{
		let row = frappe.get_doc(cdt, cdn);	
		
		if(!row.tax_excluded) //For tax excluded, tax and rate already adjusted
		{
			frappe.call(
			{
				method:'frappe.client.get_value',
				args:{
					'doctype':'Tax',
				'filters':{'tax_name': row.tax},
				'fieldname':['tax_name','tax_rate']
				},
				callback:(r2)=>
				{					
					row.tax_rate = r2.message.tax_rate;
					frm.refresh_field("items");		
					frm.trigger("make_taxes_and_totals");
				}	
			});
		}
	},
	qty(frm,cdt,cdn)
	{
		frm.trigger("make_taxes_and_totals");
	},
	rate(frm,cdt,cdn)
	{
		frm.trigger("make_taxes_and_totals");
	},
	rate_included_tax(frm,cdt,cdn)
	{
		frm.trigger("make_taxes_and_totals");
	},
	unit(frm,cdt,cdn)	
	{
		 let row = frappe.get_doc(cdt, cdn);
		 
		 console.log("Item");
		 console.log(row.item);

		//  frappe.call(
		//  	{
		//  		method:'frappe.client.get_valuelist',
		//  		args:{
		//  		'doctype':'Item Unit',
		//  		'filters':{'parent': row.item},
		//  		'fieldname':['unit','conversion_factor']
		//  		},
		//  		callback:(r2)=>
		//  		{					
		//  			console.log(r2.message);
		//  		}	
		//  	});

		console.log(row.item);

		frappe.call(
				{
					method:'digitz_erp.api.common_methods.get_item_uoms',
					async:false,
					args:{
						item: row.item,
						unit: row.unit
					},
					callback(r)	
					{
						if(r.message.length == 0)
						{
							frappe.msgprint("Invalid unit, Unit does not exists for the item.");
							row.unit = row.base_unit;
							row.conversion_factor = 1;
						}
						else
						{														
							console.log(r.message[0].conversion_factor);
							row.conversion_factor = r.message[0].conversion_factor;
						}
						
						frm.refresh_field("items");		
					//	row.set_df_property("uom", "options",r.message.uom);
						//row.uom.options = r.message.uom;
					}

				}
			);
	}	
});

