// Copyright (c) 2024, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on("Project", {
    name1(frm) {
        frm.set_query("proforma_invoice", "project_stage_table", function (doc, cdt, cdn) {
            var d = locals[cdt][cdn]

            return {
                "filters": {
                    "project": frm.doc.name1
                }
            }
        })
    },
    refresh(frm) {
        localStorage.setItem("current_project", frm.doc.name)

        frm.set_query('advance_entry', () => {
            return {
                filters: {
                    'customer': frm.doc.customer,
                    'custom_project': frm.doc.name,
                    'custom_advance_payment': 1
                }
            }
        });
        frm.set_query('sales_order', () => {
            return {
                filters: {
                    'customer': frm.doc.customer,
                    // 'custom_project': frm.doc.name,
                }
            }
        });
        frm.set_query("proforma_invoice", "project_stage_table", function (doc, cdt, cdn) {
            var d = locals[cdt][cdn]

            return {
                "filters": {
                    "project": frm.doc.name1
                }
            }
        })
        frm.set_query("sales_invoice", "project_stage_table", function (doc, cdt, cdn) {
            var d = locals[cdt][cdn]

            return {
                "filters": {
                    "custom_project": frm.doc.name1
                }
            }
        })
        // $(frm.fields_dict.advance_entry.input).on("click", function(){
        // 	var customer = localStorage.setItem('prev_customer',frm.doc.customer);
        // 	var project = localStorage.setItem('prev_project',frm.doc.name);
        // })
        var customer = localStorage.setItem('prev_customer', frm.doc.customer);
        var project = localStorage.setItem('prev_project', frm.doc.name);
        var sales_order_id = localStorage.setItem('sales_order_id', frm.doc.sales_order);

        if (!frm.is_new()) {
            frm.add_custom_button(__('Create Progressive Invoice'), function () {
                // frappe.call({
                //     method: "digitz_services.digitz_services.whitelist_methods.",
                //     args: {
                //         quotation_id: frm.doc.name,
                //     },
                //     callback: function(response){ 
                //         if(response.message){
                //              // Store the data in localStorage to pass it to the new Sales Order form
                //              localStorage.setItem('sales_order_data', JSON.stringify(response.message));
                //              console.log("done")
                //              // Redirect to the new Quotation form
                //              frappe.set_route('Form', 'Sales Order', 'new-sales-order-mqkhkpotmg')
                //         }
                //     }
                // })
                localStorage.setItem("project_id", frm.doc.name);
                frappe.set_route("Form", "Progressive Invoice", "new-progressive-invoice-tzqymbxqvm");
            });

            frm.add_custom_button(__('Show Created Progressive Invoice'), function () {
                // Redirect to BOQ list view with filters applied
                frappe.set_route('List', 'Progressive Invoice', { 'project': frm.doc.name });
            });
        }

        // Ensure the script runs after the form is refreshed
        frm.fields_dict['project_stage_table'].grid.wrapper.on('focus', '.grid-row', function (e) {
            // Get the clicked row
            var $row = $(e.currentTarget);
            var doc = frm.fields_dict['project_stage_table'].grid.get_row($row.data('idx') - 1).doc;
            console.log("doc", doc)


            // Listen for clicks on the proforma_invoice link field
            $row.find('[data-fieldname="proforma_invoice"]').on('focus', function () {
                var stage_name = doc.project_stage_defination;
                var percentage_of_completion = doc.percentage_of_completion
                var project_name = frm.doc.name1;
                var customer_name = frm.doc.customer;

                // if(!stage_name){
                // 	frappe.msgprint({
                // 		title: __('Notification'),
                // 		indicator: 'orange',
                // 		message: __('Please Enter Stage Defination / Name')
                // 	});
                // 	return false;
                // }
                //show_alert with indicator


                console.log("clicked", stage_name, project_name)
                // Store values in localStorage or handle them as needed
                localStorage.setItem('prev_stage_name', stage_name);
                localStorage.setItem('prev_project_name', project_name);
                localStorage.setItem('customer_name', customer_name);
                localStorage.setItem('percentage_of_completion', percentage_of_completion);
                localStorage.setItem('project_stage_defination', stage_name);
                localStorage.setItem('project_amount', frm.doc.project_amount);
                // if(localStorage.getItem("prev_stage_name")){
                // 	print_msg()
                // }
                // localStorage.setItem('project_amount', frm.doc.project_amount)
                // localStorage.setItem("advance_entry_id",frm.doc.advance_entry)
                // localStorage.setItem("sales_order_id",frm.doc.sales_order)


                // Optionally, you can also use frappe.msgprint to show the values for debugging
                // frappe.msgprint('Stage Name: ' + stage_name + '<br>Project Name: ' + project_name);
            });

            $row.find('[data-fieldname="sales_invoice"]').on('focus', function () {
                var proforma_invoice = doc.proforma_invoice;

                localStorage.setItem("proforma_invoice", proforma_invoice);

            });
        })


    },
    setup(frm) {
        let data = localStorage.getItem('project_data');
        if (data) {
            data = JSON.parse(data);
            console.log("project_data", data)
            // Set the fields with the retrieved data
            frm.set_value('customer', data.customer);
            frm.set_value('sales_order', data.sales_order);
            frm.set_value("project_amount", data.project_amount);


            frm.refresh_field();

            // Clear the data from localStorage
            localStorage.removeItem('project_data');
            console.log("removed data", localStorage.getItem('project_data'))
        }
    },
    onload: function (frm) {
        // Check if customer name exists in localStorage
        var customer = localStorage.getItem('customer');

        if (customer) {
            // Set the customer field with the retrieved customer name
            frm.set_value('customer', customer);

            // Clear the stored customer name from localStorage
            localStorage.removeItem('customer');

        }

        frm.fields_dict['stage'].grid.get_field('project_stage').get_query = function (doc, cdt, cdn) {
            var child = locals[cdt][cdn];
            return {
                filters: {
                    'project': frm.doc.name1 // Change these filters as per your requirement
                }
            };
        };

    },
    // advance_entry(frm){
    // 	console.log("sdfjsldf  jk")
    // }
    retentation_percentage(frm) {
        let percentage = parseFloat(frm.doc.retentation_percentage);
        if (isNaN(percentage) || percentage < 0) {
            frm.set_value("retentation_amt", 0)
            frm.set_value("amount_after_retentation", 0)
            frappe.msgprint('Please enter a valid retention percentage.');
            return;
        }


        frappe.call({
            method: "digitz_erp.project.doctype.project.project.calculate_rest_amt",
            args: {
                sales_order_id: frm.doc.sales_order,
                retentation_percentage: percentage
            },
            callback: function (response) {
                if (response.message) {
                    console.log("retentation % and more", response)
                    let data = response.message
                    frm.set_value("retentation_amt",Math.round(data.retentation_amt)/100)
                    frm.set_value("amount_after_retentation", Math.round(data.amount_after_retentation)/100)
                }
            }
        })
    }
});




function print_msg() {
    frappe.show_alert({
        message: __('Please Enter Stage Name'),
        indicator: 'red'
    }, 2);
}
