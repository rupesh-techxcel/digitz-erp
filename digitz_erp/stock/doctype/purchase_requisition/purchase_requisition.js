// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Requisition", {
    setup(frm) {
        frm.trigger('get_default_company_and_warehouse');
    },
	refresh(frm) {
        if(!frm.is_new() && frm.doc.docstatus==1){
            // if(frm.doc.material_request_type == "Stock Transfer"){
            //     frm.add_custom_button(__("Stock Transfer"),()=>{
            //         console.log("Stock Transfer");
            //     },__("Action"));   
            // }
            if(frm.doc.material_request_type == "Purchase"){
                frm.add_custom_button(__("Purchase Order"),()=>{
                    console.log("Purchase");
                    console.log(frm.doc.items)
                    frappe.new_doc("Purchase Order", {}, po =>{
                        po.items = [];
                        po.warehouse = frm.doc.set_warehouse;
                        frm.doc.items.forEach(item => {

                            let po_item = frappe.model.add_child(po, 'items');
                            po_item.item = item.item_code;
                            po_item.qty = item.qty;
                            po_item.warehouse = frm.doc.set_warehouse

                             // Fetch additional fields from the Item master
                            frappe.db.get_value('Item', item.item_code, ['item_name', 'standard_buying_price','base_unit'], (r) => {
                                if (r) {
                                    po_item.item_code = item.item_code;
                                    po_item.item_name = r.item_name;
                                    po_item.display_name = r.item_name;
                                    po_item.qty = item.qty;
                                    // po_item.rate = r.standard_buying_price;
                                    // po_item.warehouse = "Default Warehouse";
                                    // po_item.unit = r.base_unit;  // Assuming this is the default unit
                                    // po_item.base_unit = r.base_unit;  // Assuming this is the default unit
                                    // po_item.rate_in_base_unit = po_item.rate;
                                    // po_item.conversion_factor = 1;
                                    // po_item.tax = "UAE VAT - 5%";
                                    // po_item.tax_rate = 5;
                                    
                                    // These fields might be calculated automatically by the system
                                    // po_item.gross_amount = po_item.qty * po_item.rate;
                                    // po_item.tax_amount = 0;  // This might be calculated based on tax settings
                                    // po_item.net_amount = po_item.gross_amount + po_item.tax_amount;
                                    
                                    // Fields that might need additional logic or data sources
                                    // po_item.rate_includes_tax = 0;
                                    // po_item.tax_excluded = 0;
                                    // po_item.discount_percentage = "0";
                                    // po_item.discount_amount = 0;
                                    // po_item.rate_excluded_tax = po_item.rate;
                                    // po_item.qty_in_base_unit = null;
                                    // po_item.unit_conversion_details = "NaN CAN @ NaN\nNaN CRTN @ NaN\n";
                                    // po_item.base_unit = "CAN";
                                }
                            });

                            frm.refresh_fields("items");
                        });
                    })
                },__("Action"));   
            }
            if(frm.doc.material_request_type == "Stock Transfer"){
                frm.add_custom_button(__("Stock Transfer"),()=>{
                    console.log("Stock Transfer");
                    console.log(frm.doc.items)
                    frappe.new_doc("Stock Transfer", {}, so =>{
                        so.items = [];
                        so.source_warehouse = frm.doc.set_from_warehouse;
                        so.target_warehouse = frm.doc.set_warehouse;
                        frm.doc.items.forEach(item => {

                            let so_item = frappe.model.add_child(so, 'items');
                            so_item.item = item.item_code;
                            so_item.qty = item.qty;
                            so.source_warehouse = frm.doc.set_from_warehouse;
                            so.target_warehouse = frm.doc.set_warehouse;

                             // Fetch additional fields from the Item master
                            frappe.db.get_value('Item', item.item_code, ['item_name', 'standard_buying_price','base_unit'], (r) => {
                                if (r) {
                                    so_item.item_code = item.item_code;
                                    so_item.item_name = r.item_name;
                                    so_item.display_name = r.item_name;
                                    so_item.qty = item.qty;
                                    so_item.rate = r.standard_buying_price;
                                    so_item.net_amount = so_item.rate * so_item.qty;
                                }
                            });

                            frm.refresh_fields("items");
                        });
                    })
                },__("Action"));   
            }
        }

        frm.set_query("warehouse", "items", function (doc) {
			return {
				filters: { company: doc.company },
			};
		});
        frm.set_query("set_warehouse",function(doc){
            return {
                filters:{company: doc.company},
            }
        })
	},
    get_default_company_and_warehouse(frm) {

		var default_company = ""

		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				'doctype': 'Global Settings',
				'fieldname': 'default_company'
			},
			callback: (r) => {

				default_company = r.message.default_company
				
                frm.set_value("company",default_company)
				
				frappe.call(
                {
                    method: 'frappe.client.get_value',
                    args: {
                        'doctype': 'Company',
                        'filters': { 'company_name': default_company },
                        'fieldname': ['default_advance_received_account']
                    },
                    callback: (r2) => {
                        frm.doc.advance_account = r2.message.default_advance_received_account
                        console.log(r2)

                    }
                }
				)
			}
		})

	},
});



frappe.ui.form.on("Purchase Requisition Item", {
    item_code(frm,cdt,cdn){
        row = frappe.get_doc(cdt,cdn);
        item = frappe.get_doc("Item", row.item_code);
    }
})
