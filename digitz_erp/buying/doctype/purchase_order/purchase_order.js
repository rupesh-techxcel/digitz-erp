// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Order', {
	refresh(frm) {
	    if (frappe.user_roles.includes('All')) {
	        frm.add_custom_button(__('Create Purchase Invoice'), function () {
	             frappe.db.insert({
                    "doctype": "Purchase Invoice",
                    "supplier": frm.doc.supplier,
                    "company": frm.doc.company,
                    "transaction_date": frm.doc.posting_date,
                    "credit_to": "Cash - T",
                    'items': frm.doc.items.map((item) => {
			            return {
			    	        'item_code' : item.item_code,
				            'item_name' : item.item_name,
				            'rate' : item.rate,
				            'qty':item.qty
			};
		})
        
 
                    }).then(function(doc) {
                    console.log(doc);
                });
	        
	                frm.refresh();
	        }).addClass("btn btn-default ellipsis").css({'color':'white','font-size': '15px','background-color':'purple'});
	   }
		// your code here
	}
});
