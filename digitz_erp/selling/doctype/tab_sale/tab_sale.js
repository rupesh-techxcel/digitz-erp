// Copyright (c) 2023, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tab Sale", {
    onload: function (frm, cdt, cdn) {
        frm.set_query("unit", "items", function () {
            const d = locals[cdt][cdn]
            console.log(d)
            console.log(d.items)
            d.items.map((data, index) => {
                return {
                    query: "digitz_erp.custom_query.get_item_wise_unit",
                    filters: {
                        "item": data.item
                    }
                };
            })
        });
    }
});
frappe.ui.form.on("TabSaleInvoice", {


});
