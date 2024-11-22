frappe.ui.form.on("Receipt Reconciliation", {
    // Triggered when the form is refreshed
    refresh(frm) {
        // Remove the "Add Row" button for the 'invoices' child table
        frm.fields_dict['invoices'].grid.cannot_add_rows = true;
        frm.refresh_field('invoices'); // Refresh to apply changes

        // Remove the "Add Row" button for the 'receipts' child table
        frm.fields_dict['receipts'].grid.cannot_add_rows = true;        
        frm.refresh_field('receipts'); // Refresh to apply changes
    },

    edit_posting_date_and_time(frm) {
        if (frm.doc.edit_posting_date_and_time == 1) {
            frm.set_df_property("posting_date", "read_only", 0);
            frm.set_df_property("posting_time", "read_only", 0);
        } else {
            frm.set_df_property("posting_date", "read_only", 1);
            frm.set_df_property("posting_time", "read_only", 1);
        }
    },

    // Triggered when the customer field is changed
    customer(frm) {
        frm.events.get_pending_invoices_and_receipts(frm);  // Call the method when the customer is changed
    },

    // Function to get pending invoices and receipts for the selected customer
    get_pending_invoices_and_receipts: function(frm) {
        console.log("Fetching pending invoices and receipts...");
        
        const selected_customer = frm.doc.customer;
        const invoice_method = "digitz_erp.api.receipt_entry_api.get_customer_pending_documents";
        const receipt_method = "digitz_erp.api.receipt_entry_api.get_receipts_unallocated";

        if (selected_customer) {
            // Sales Invoice Call
            frappe.call({
                method: invoice_method,
                args: { customer: selected_customer, reference_type: "Sales Invoice", receipt_no: "", only_unpaid: 1 }
            }).then((salesInvoiceRes) => {
                frm.clear_table('invoices'); // Clear the table before inserting

                const salesInvoices = salesInvoiceRes.message || [];
                salesInvoices.forEach((invoice) => {
                    let row = frm.add_child('invoices');
                    row.reference_type = invoice.reference_type || "";
                    row.invoice_no = invoice.reference_name || "";
                    row.invoice_date = invoice.posting_date || "";
                    row.invoice_amount = invoice.invoice_amount || 0;
                });

                frm.refresh_field('invoices');
            }).catch(error => {
                console.error("Error fetching invoices:", error);
                frappe.msgprint(__("There was an error fetching the pending invoices."));
            });

            // Unallocated Receipts Call
            frappe.call({
                method: receipt_method,
                args: { customer: selected_customer },
                callback: (r) => {
                    frm.clear_table('receipts'); // Clear the table before inserting
                    if (r.message && r.message.length > 0) {
                        r.message.forEach((receipt) => {
                            let row = frm.add_child('receipts');
                            row.receipt_no = receipt.receipt_no || "";
                            row.reference_type = receipt.reference_type || "";
                            row.receipt_date = receipt.receipt_date || "";
                            row.receipt_amount = receipt.receipt_amount || 0;
                        });

                        frm.refresh_field('receipts');
                    } else {
                        console.log("No unallocated receipts found.");
                    }
                },
                error: (error) => {
                    console.error("Error fetching receipts:", error);
                    frappe.msgprint(__("There was an error fetching unallocated receipts."));
                }
            });
        }
    },  
auto_allocate(frm) {
    frm.events.allocate_receipts_to_invoices(frm,false);
},
allocate(frm) {
    frm.events.allocate_receipts_to_invoices(frm,true);
},
// Function to allocate receipts to invoices
// No receipt will be partially allocated. For example, if Receipt No. 101 has an amount of 1000, it must be fully allocated across invoices, or it will remain unallocated.

//This method deals with 'tabReceipt Detalis' table entries and not 'tabReceipt Allocation` table. So when updating whatever exists in the `tabReceipt Allocation` for the customer and reference_type, in the receipt, will be moved to 'tabReceipt Previous Allocation` table

allocate_receipts_to_invoices: function (frm, selected_rows = false) {

    let receipts = selected_rows ? frm.doc.receipts.filter(receipt => receipt.__checked) : frm.doc.receipts || [];
    let invoices = selected_rows ? frm.doc.invoices.filter(invoice => invoice.__checked) : frm.doc.invoices || [];

    // Check if manual allocation is requested but no rows are selected
    if (selected_rows && (receipts.length === 0 || invoices.length === 0)) {
        frappe.msgprint(__("Please select both receipts and invoices for manual allocation."));
        return;  // Stop the allocation process
    }

    let allocation_occurred = false; // Flag to track if any allocation happens

    // Process each receipt one by one
    for (let receipt of receipts) {
        let receipt_amount = receipt.receipt_amount;
        console.log("Processing Receipt:", receipt.receipt_no, "with Amount:", receipt_amount);

        // Calculate the total unallocated amount of invoices
        let total_unallocated = 0;
        invoices.forEach(invoice => {
            let invoice_unallocated = invoice.invoice_amount - (invoice.allocated_amount || 0);
            if (invoice_unallocated > 0) {
                total_unallocated += invoice_unallocated;
            }
        });

        console.log("Total due:", total_unallocated);

        // Check if there are sufficient invoices to fully allocate the receipt amount
        if (receipt_amount > 0 && total_unallocated >= receipt_amount) {
            let remaining_receipt_amount = receipt_amount;

            console.log("Inside condition - sufficient invoices for full allocation");

            for (let invoice of invoices) {
                
                let invoice_amount_unallocated = invoice.invoice_amount - (invoice.allocated_amount || 0);

                // Considering two conditions
                // 1. reamaining_recept_amount is bigger than remaining unallocated_amount in the invoice, in that case allocate the full unallocated invoice amount 
                // 2. Else (means remaining receipt amount is less than unallocated_invoice_amount) then allocate only remaining_receipt_amount

                if (invoice_amount_unallocated > 0 && remaining_receipt_amount > 0) {

                    // If receipt_amount holds more value than invoice unallocated amount, then allocate the full invoice_amount_unallocated
                    if (remaining_receipt_amount >= invoice_amount_unallocated) {
                        // Fully allocate to the invoice
                        invoice.allocated_amount = (invoice.allocated_amount || 0)+ invoice_amount_unallocated;
                        remaining_receipt_amount -= invoice_amount_unallocated;
                        invoice.receipt_no = receipt.receipt_no
                        invoice.receipt_original_reference_type = receipt.reference_type
                        allocation_occurred = true;
                        console.log(`Allocated full ${invoice_amount_unallocated} to Invoice: ${invoice.invoice_no}`);
                    } else {

                        //Remainging receipt amount is less than unallocated invoice amount
                        //Only remaining receipt_amount can be allocated to the invoice
                        // Partially allocate the remaining amount to this invoice
                        invoice.allocated_amount = (invoice.allocated_amount || 0) + remaining_receipt_amount;
                        console.log(`Allocated partial ${remaining_receipt_amount} to Invoice: ${invoice.invoice_no}`);
                        remaining_receipt_amount = 0;  // Fully allocated, stop further allocation
                        allocation_occurred = true;
                        break;
                    }
                }
            }
        } else {
            // Break the process if the receipt can't be fully allocated due to insufficient invoices
            console.log(`Breaking process: Receipt: ${receipt.receipt_no} cannot be fully allocated due to insufficient invoices.`);
            frappe.msgprint(__("Receipt " + receipt.receipt_no + " cannot be fully allocated due to insufficient invoice amounts."));
            break;
        }
    }

    // Refresh fields to show updated allocations
    frm.refresh_field('invoices');
    frm.refresh_field('receipts');

    // Show messages based on allocation status
    if (allocation_occurred) {
        frappe.msgprint(__("Receipts have been successfully allocated to invoices."));
    } else {
        frappe.msgprint(__("No allocations were made due to insufficient invoices."));
    }
},
clear_allocations: function(frm) {
    // Check if there are any invoices to clear allocations from
    if (frm.doc.invoices.length === 0) {
        frappe.msgprint(__('No invoices found to clear allocations.'));
        return;
    }

    let any_allocation = false; // Flag to track if any allocations exist

    // Iterate through the invoices child table and reset allocated amounts
    frm.doc.invoices.forEach((invoice) => {
        if (invoice.allocated_amount > 0) {
            invoice.allocated_amount = 0; // Reset allocated amount to zero
            any_allocation = true; // Set flag to true if any allocation is cleared
        }
    });

    // Check if any allocations were cleared
    if (!any_allocation) {
        frappe.msgprint(__('No invoice allocations exist to be cleared.'));
        return;
    }

    // Optionally, clear any related flags or other fields as needed
    // frm.doc.receipts.forEach((receipt) => {
    //     receipt.allocated = false; // Example flag reset
    // });

    // Refresh the child table to reflect changes
    frm.refresh_field('invoices');
    frappe.msgprint(__('Allocations have been cleared successfully.'));
}


});
