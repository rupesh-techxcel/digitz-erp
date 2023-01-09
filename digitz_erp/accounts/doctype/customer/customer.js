// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer', {
	
	 setup: function(frm) {

		frm.set_query("billing_address", function() {
			return {
				"filters":{"customer": ["in" ,frm.doc.customer_name, ""]}				
			};
		});		

		frm.set_query("shipping_address", function() {
			return {
				"filters":{"customer": ["in" ,frm.doc.customer_name, ""]}				
			};
		});	
	 },
	 billing_address(frm)
	 {
		frappe.call({
			method: 'frappe.client.get_value',
			args:{
				'doctype':'Customer Address',
				'filters':{'title': frm.doc.billing_address},
				'fieldname':['full_address']
			},
			callback: (r)=>{
				console.log(r);
				frm.doc.billing_address_details = r.full_address;
			}	
	 	});
	},
	shipping_address(frm)
	{
	   frappe.call({
		   method: 'frappe.client.get_value',
		   args:{
			   'doctype':'Customer Address',
			   'filters':{'title': frm.doc.shipping_address},
			   'fieldname':['full_address']
		   },
		   callback: (r)=>{
			   console.log(r);
			   frm.doc.shipping_address_details = r.full_address;
		   }	
		});
   }
});

frappe.ui.form.on("Customer", "onload", function(frm) {

	frm.add_fetch('billing_address','full_address','billing_address_details');	
	frm.add_fetch('shipping_address','full_address','shipping_address_details');	
})
