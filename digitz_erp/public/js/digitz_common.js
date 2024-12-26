let general_ledgers = function (frm) {
    frappe.call({
        method: "digitz_erp.api.accounts_api.get_gl_postings",
        args: {
            voucher: frm.doc.doctype,
            voucher_no: frm.doc.name
        },
        callback: function (response) {
            let gl_postings = response.message.gl_postings;
            let totalDebit = parseFloat(response.message.total_debit).toFixed(2);
            let totalCredit = parseFloat(response.message.total_credit).toFixed(2);

            // Generate HTML content for the popup
            let htmlContent = '<div style="max-height: 680px; overflow-y: auto;">' +
                              '<table class="table table-bordered" style="width: 100%;">' +
                              '<thead>' +
                              '<tr>' +
                              '<th style="width: 15%;">Account</th>' +
                              '<th style="width: 25%;">Remarks</th>' +
                              '<th style="width: 10%;">Debit Amount</th>' +
                              '<th style="width: 10%;">Credit Amount</th>' +
                              '<th style="width: 10%;">Party</th>' +
                              '<th style="width: 10%;">Against Account</th>' +
                              '<th style="width: 10%;">Project</th>' +
                              '<th style="width: 10%;">Cost Center</th>' +
                              '</tr>' +
                              '</thead>' +
                              '<tbody>';

            gl_postings.forEach(function (gl_posting) {
                let remarksText = gl_posting.remarks || '';
                let debitAmount = parseFloat(gl_posting.debit_amount).toFixed(2);
                let creditAmount = parseFloat(gl_posting.credit_amount).toFixed(2);

                htmlContent += '<tr>' +
                               `<td>${gl_posting.account}</td>` +
                               `<td>${remarksText}</td>` +
                               `<td style="text-align: right;">${debitAmount}</td>` +
                               `<td style="text-align: right;">${creditAmount}</td>` +
                               `<td>${gl_posting.party}</td>` +
                               `<td>${gl_posting.against_account}</td>` +
                               `<td>${gl_posting.project}</td>` +
                               `<td>${gl_posting.cost_center}</td>` +
                               '</tr>';
            });

            // Add totals row
            htmlContent += '<tr>' +
                           '<td style="font-weight: bold;">Total</td>' +
                           '<td></td>' +
                           `<td style="text-align: right; font-weight: bold;">${totalDebit}</td>` +
                           `<td style="text-align: right; font-weight: bold;">${totalCredit}</td>` +
                           '<td colspan="5"></td>' +
                           '</tr>';

            htmlContent += '</tbody></table></div>';

            // Create and show the dialog
            let d = new frappe.ui.Dialog({
                title: 'General Ledgers',
                fields: [{
                    fieldtype: 'HTML',
                    fieldname: 'general_ledgers_html',
                    options: htmlContent
                }],
                primary_action_label: 'Close',
                primary_action: function () {
                    d.hide();
                }
            });

            // Set custom width for the dialog
            d.$wrapper.find('.modal-dialog').css('max-width', '90%'); 

            d.show();
        }
    });
};


let stock_ledgers = function (frm) {
    frappe.call({
        method: "digitz_erp.api.accounts_api.get_stock_ledgers",
        args: {
			voucher: frm.doc.doctype,
            voucher_no: frm.doc.name
        },
        callback: function (response) {
            let stock_ledgers_data = response.message;

            // Generate HTML content for the popup
            let htmlContent = '<div style="max-height: 400px; overflow-y: auto;">' +
                              '<table class="table table-bordered" style="width: 100%;">' +
                              '<thead>' +
                              '<tr>' +
                              '<th style="width: 10%;">Item Code</th>' +
							  '<th style="width: 20%;">Item Name</th>' +
                              '<th style="width: 15%;">Warehouse</th>' +
                              '<th style="width: 10%;">Qty In</th>' +
                              '<th style="width: 10%;">Qty Out</th>' +
                              '<th style="width: 15%;">Valuation Rate</th>' +
                              '<th style="width: 15%;">Balance Qty</th>' +
                              '<th style="width: 15%;">Balance Value</th>' +
                              '</tr>' +
                              '</thead>' +
                              '<tbody>';

            // Loop through the data and create rows
            stock_ledgers_data.forEach(function (ledger) {
                htmlContent += '<tr>' +
                               `<td><a href="/app/item/${ledger.item}" target="_blank">${ledger.item}</a></td>` +
							   `<td>${ledger.item_name}</td>` +
                               `<td>${ledger.warehouse}</td>` +
                               `<td>${ledger.qty_in}</td>` +
                               `<td>${ledger.qty_out}</td>` +
                               `<td>${ledger.valuation_rate}</td>` +
                               `<td>${ledger.balance_qty}</td>` +
                               `<td>${ledger.balance_value}</td>` +
                               '</tr>';
            });

            htmlContent += '</tbody></table></div>';

            // Create and show the dialog
            let d = new frappe.ui.Dialog({
                title: 'Stock Ledgers',
                fields: [{
                    fieldtype: 'HTML',
                    fieldname: 'stock_ledgers_html',
                    options: htmlContent
                }],
                primary_action_label: 'Close',
                primary_action: function () {
                    d.hide();
                }
            });

            // Set custom width for the dialog
            d.$wrapper.find('.modal-dialog').css('max-width', '85%'); // or any specific width like 800px

            d.show();
        }
    });
};

// Export the function to make it reusable
// export { general_ledgers };
// export { stock_ledgers };