// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Receipt Entry', {

	refresh:function(frm){
		create_custom_buttons(frm)

		frm.set_query("warehouse", function() {
			return {
				"filters": {
					"disabled": 0
				}
			};
		});

		    frm.fields_dict['receipt_entry_details'].grid.get_field('account').get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    is_group: 0  // Set filters to only show accounts where is_group is false
                }
            };
        };

		// Allocations are mean for readonly purpose and not for user inputs. So make it hidden first and show it on demand
		frm.doc.show_allocations = false;
		frm.trigger("show_allocations");
	},
	setup: function(frm){
		frm.add_fetch('payment_mode', 'account', 'account')
	},
	show_allocations:function(frm)
	{
		console.log("show allocations")
		console.log(frm.doc.show_allocations)
		frm.set_df_property("receipt_allocation", 'hidden', !frm.doc.show_allocations);
		frm.refresh_field("receipt_allocation");
	},
	edit_posting_date_and_time(frm) {

		if (frm.doc.edit_posting_date_and_time == 1) {
			frm.set_df_property("posting_date", "read_only", 0);
			frm.set_df_property("posting_time", "read_only", 0);
		}
		else {
			frm.set_df_property("posting_date", "read_only", 1);
			frm.set_df_property("posting_time", "read_only", 1);
		}
	},
	get_default_company_and_warehouse(frm) {
		var default_company = ""

		frm.trigger("get_user_warehouse")

		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				'doctype': 'Global Settings',
				'fieldname': 'default_company'
			},
			callback: (r) => {

				default_company = r.message.default_company
				frm.doc.company = r.message.default_company
				frm.refresh_field("company");
				frappe.call(
					{
						method: 'frappe.client.get_value',
						args: {
							'doctype': 'Company',
							'filters': { 'company_name': default_company },
							'fieldname': ['default_warehouse']
						},
						callback: (r2) => {

							if (typeof window.warehouse !== 'undefined') {
								// The value is assigned to window.warehouse
								// You can use it here
								frm.doc.warehouse = window.warehouse;
							}
							else
							{
								frm.doc.warehouse = r2.message.default_warehouse;
							}

							console.log(frm.doc.warehouse);
							//frm.doc.rate_includes_tax = r2.message.rate_includes_tax;
							frm.refresh_field("warehouse");
						}
					}

				)
			}
		});
	},
	get_user_warehouse(frm)
	{
		frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'User Warehouse',
                filters: {
                    user: frappe.session.user
                },
                fieldname: 'warehouse'
            },
            callback: function(response) {
				if (response && response.message && response.message.warehouse) {
					window.warehouse = response.message.warehouse;
					// Do something with warehouseValue
				}
			}
		});
	},
	refresh_allocations_may_be_removed(frm)
	{
		var allocations = frm.doc.receipt_allocation || [];
		for(var i = 0; i < allocations.length; i++)
		{

			var receipts = frm.doc.receipt_entry_details;

			var allocation_found =false;

			for(var j = 0; j < receipts.length; j++)
			{
				if(receipts[j].customer == allocations[i].customer && allocations[i].allocated_amount>0)
				{
					allocation_found = true;
				}
			}

			if( !allocation_found)
			{
				cur_frm.get_field('receipt_allocation').grid.grid_rows[i].remove();
			}

		}
		cur_frm.refresh()
	},
	before_save(frm)
	{
		frm.trigger("clean_allocations");
		frm.trigger("calculate_total_and_set_fields");
	},
	calculate_total_and_set_fields(frm)
	{
		var receipt_detail = frm.doc.receipt_entry_details;

		var total =0;
		var total_allocated = 0;

		for (var i = 0; i< receipt_detail.length; i++) {

			total = total + receipt_detail[i].amount;
			if (!isNaN(receipt_detail[i].allocated_amount)) {
				total_allocated = total_allocated + receipt_detail[i].allocated_amount;
			}
			console.log("total")
			console.log(total)
			console.log("total_allocated")
			console.log(total_allocated)
		}

		frm.doc.amount = total;
		frm.doc.allocated_amount = total_allocated;

		frm.refresh_field("amount");
		frm.refresh_field("allocated_amount");
	},
	amount(frm)
	{
		frm.trigger("calculate_total_and_set_fields");
	},
	clean_allocations(frm)
	{
		var allocations = cur_frm.doc.receipt_allocation;

		var allocations_to_remove = []

		if(allocations != undefined)
		{
			for (var i = allocations.length - 1; i >= 0; i--)
			{
				var allocation = allocations[i];

				var receipts = cur_frm.doc.receipt_entry_details;

				if(receipts != undefined)
				{
					var receipt_exists = false;
					for (var j = 0; j< receipts.length;  j++) {

						if(receipts[j].customer == allocation.customer && receipts[j].allocated_amount != undefined && receipts[j].allocated_amount>0 )
						{
							receipt_exists= true
						}
					}

					if(!receipt_exists)
					{
						allocations_to_remove.push(allocation)

					}
				}
				else
				{
					allocations_to_remove.push(allocation)

				}
			}

			if(allocations_to_remove.length > 0)
			{
				for(i=0; i< allocations_to_remove.length; i++)
				{
					cur_frm.doc.receipt_allocation = cur_frm.doc.receipt_allocation.filter(
						function (row){
							return row.customer != allocations_to_remove[i].customer
						}
					)

					cur_frm.refresh_field("receipt_allocation");
				}

			}
		}
	}
}
);
frappe.ui.form.on("Receipt Entry", "onload", function (frm) {

	if(frm.doc.__islocal)
	{
		frm.trigger("get_default_company_and_warehouse");
		//For receipt entry one blank row is intially added and couldn't find the reason of it. It is not happening with other doctypes. So removing the same.
		// frm.doc.receipt_entry_details.splice(0,1)				
	}

	if (frm.is_new())
	{
		frm.clear_table("receipt_entry_details");
	}
}

	
);

 frappe.ui.form.on("Receipt Entry Detail", {
	 reference_type(frm, cdt, cdn){
		 var child = locals[cdt][cdn];
		 if (frm.doc.default_cost_center) {
			 frappe.model.set_value(cdt, cdn, 'cost_center', frm.doc.default_cost_center);
		}
	 },

  	receipt_type: function(frm, cdt, cdn) {

  	var row = locals[cdt][cdn];
	if(row.receipt_type == "Customer")
	{

		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				'doctype': 'Global Settings',
				'fieldname': 'default_company'
			},
			callback: (r) => {

		 		frappe.db.get_value("Company", r.message.default_company, "default_receivable_account").then((r) => {
	 			var default_receivable_account = r.message.default_receivable_account;
	 			frappe.model.set_value(cdt, cdn, 'account', default_receivable_account)});
			}
		})
	}
},
receipt_entry_details_add:function(frm,cdt,cdn)
{
	frappe.call({
		method: 'frappe.client.get_value',
		args: {
			'doctype': 'Global Settings',
			'fieldname': 'default_company'
		},
		callback: (r) => {

			 frappe.db.get_value("Company", r.message.default_company, "default_receivable_account").then((r) => {
			 var default_receivable_account = r.message.default_receivable_account;
			 frappe.model.set_value(cdt, cdn, 'account', default_receivable_account)});
			frm.refresh_field("receipt_entry_details")
		}
	});

	var row = locals[cdt][cdn];
	row.receipt_type = "Customer"
	row.reference_type = "Sales Invoice"
	row.reference_no = frm.doc.reference_no
	row.reference_date = frm.doc.reference_date
	frm.refresh_field("receipt_entry_details")
},
receipt_entry_details_remove: function(frm,cdt,cdn)
{
	frm.trigger("clean_allocations");
	frm.trigger("calculate_total_and_set_fields");
},

customer: function(frm,cdt,cdn){



},
amount: function(frm,cdt,cdn)
{
	frm.trigger("calculate_total_and_set_fields");
},

allocations: function(frm, cdt, cdn)
{
	const row = locals[cdt][cdn];
	let child_table_control	;

	if(row.receipt_type != "Customer" || (!row.reference_type) ||  row.reference_type == "" ||  (!row.customer))
	{
		frappe.throw("Invalid criteria for allocations.")
	}

	const selected_customer = row.customer
	const selected_reference_type = row.reference_type

	console.log("selected customer")
	console.log(selected_customer)
	console.log("selected reference_type")
	console.log(selected_reference_type)

	//Allocations are restricted with only one per supplier. So verify that there is no other
	//row exists with allocation for the selected_supplier

	const receipt_entries = cur_frm.doc.receipt_entry_details;

	// Checking for allocations exists for the supplier in a different row
	if(receipt_entries != undefined)
	{
		for (var i = receipt_entries.length - 1; i >= 0; i--) {

			var receipt = receipt_entries[i];

			if(receipt.supplier == selected_customer && typeof(receipt.reference_type) != undefined &&  receipt.reference_type==selected_reference_type && receipt.allocated_amount>0
				 && receipt.name !=cdn )
			{
				// Create the message string
				var message = "Allocation exists for the {0} and {1} at line no {2}".format(selected_customer, selected_reference_type, i);

				// Display the message using frappe.msgprint
				frappe.msgprint(message);
				return;
			}
		}
	}

	let allocations_exists_in_other_receipts;

	// Fetch the customer invoices at the stage on which the document was not yet saved

	client_method =  "digitz_erp.api.receipt_entry_api.get_all_customer_pending_receipt_allocations_with_other_receipts"

	frappe.call({

		method: client_method,
		async:false,
		args: {
			customer: selected_customer,
			reference_type: selected_reference_type,
			receipt_no: cur_frm.doc.__islocal ? "" : frm.doc.name
		},
		callback:(r) => {
			allocations_exists_in_other_receipts = r.message.values
			console.log("allocations_exists_in_other_receipts")
			console.log(allocations_exists_in_other_receipts)
		}});


	let pending_invoices_data
	//Fetch all supplier pending invoices and invoices already allocated in this payment_entry
	
	client_method = "digitz_erp.api.receipt_entry_api.get_customer_pending_documents";
	
	frappe.call({
		method: client_method,
		args: {
			customer: selected_customer,
			reference_type: selected_reference_type,
			receipt_no: cur_frm.doc.__islocal ? "" : frm.doc.name
		},
		callback:(r) => {

			pending_invoices_data = r.message;
			
			child_table_control = frappe.ui.form.make_control({
				df: {
					fieldname: "receipt_allocation",
					fieldtype: "Table",
					cannot_add_rows:true,
					fields: [
						{
							fieldtype: 'Data',
							fieldname: 'reference_type',
							label: 'Reference Type',
							in_place_edit: false,
							in_list_view: false,
							read_only:true,
							hidden: true
						},
						{
							fieldtype: "Link",
							fieldname: "reference_name",
							label: "Reference Name",
							in_place_edit: false,
							in_list_view: true,
							// width: "40%",
							read_only:true
						},
						{
							fieldtype: "Link",
							fieldname: "reference_no",
							label: "Reference No & Date",
							in_place_edit: false,
							in_list_view: true,
							// width: "40%",
							read_only:true
						},
						{
							fieldtype: "Currency",
							fieldname: "invoice_amount",
							label: "Invoice Amount",
							in_place_edit: false,
							in_list_view: true,
							read_only:true
						},
						{
							fieldtype: "Currency",
							fieldname: "balance_amount",
							label: "Balance Amount",
							in_place_edit: false,
							in_list_view: true,
							read_only:true
						},
						{
							fieldtype: "Currency",
							fieldname: "paying_amount",
							label: "Paying Amount",
							in_place_edit: true,
							in_list_view: true
						}
					],
				},
				parent: dialog.get_field("sales").$wrapper,
				render_input: true,
			});
			


			//Stage 1.
			//Intiially set the paid_amount as zero and balance_amount as invoice amount
			//Iterate through the allocations for the particular invoice
			//During the iteeration assign the paid amount and balance amount based on the allocation
			//Note that the allocations fetched does not include current document allocation

			console.log("pending_invoices_data")
			console.log(pending_invoices_data)

			console.log("allocations_exists_in_other_payments")
			console.log(allocations_exists_in_other_receipts)

			for (var idx1= pending_invoices_data.length - 1; idx1>=0; idx1--)
			{
				// console.log("value of j")
				// console.log(j)

				pending_invoices_data[idx1].paid_amount = 0;
				pending_invoices_data[idx1].balance_amount =  pending_invoices_data[idx1].invoice_amount;
				// pending_invoices_data[j].posting_date = frappe.format(pending_invoices_data[j].posting_date, { fieldtype: 'Date' })

				for (var idx2 = allocations_exists_in_other_receipts.length - 1; idx2>=0; idx2--)
				{
					// console.log("pending_invoices_data[j].reference_name")
					// console.log(pending_invoices_data[j].reference_name)

					// console.log("allocations_exists_in_other_payments[i].reference_name")
					// console.log(allocations_exists_in_other_payments[i].reference_name)

					if(pending_invoices_data[idx1].reference_name == allocations_exists_in_other_receipts[idx2].reference_name)
					{
						//Update teh paid amount
						pending_invoices_data[idx1].paid_amount  = pending_invoices_data[idx1].paid_amount  + allocations_exists_in_other_receipts[idx2].paying_amount;
						// console.log("allocations_exists_in_other_payments[i].paying_amount");
						// console.log(allocations_exists_in_other_payments[i].paying_amount);
						// console.log("new paid_amount")
						// console.log(pending_invoices_data[j].paid_amount)
						//First set balance amount as invoice_amount - paid amount
						pending_invoices_data[idx1].balance_amount = pending_invoices_data[idx1].balance_amount - allocations_exists_in_other_receipts[idx2].paying_amount;
						// console.log("pending_invoices_data[j].balance_amount")
						// console.log(pending_invoices_data[j].balance_amount)

						// console.log("inner loop i")
						// console.log(i)
					}
				}
			}

			console.log("pending_invoices_data after the loop")
			console.log(pending_invoices_data)

			var pending_invoices_with_value = []

			for (var idx1= pending_invoices_data.length - 1; idx1>=0; idx1--)
			{
				 if(pending_invoices_data[idx1].balance_amount >0)
				 {
					pending_invoices_with_value.push(pending_invoices_data[idx1]);
				 }
			}

			// if(pending_invoices_data.length> pending_invoices_with_value.length)
			// {
			// 	frappe.msgprint("Allocations without balance amount has been removed")
			// }


			//Stage 2.
			// Get the values input from the allocations table in the current document
			// Adjust the paid amount based on the paying amount
			var allocations = cur_frm.doc.receipt_allocation;
			console.log(allocations)

			if(allocations)
			{
				for (var idx2 = allocations.length - 1; idx2 >= 0; idx2--) {

					var allocation = allocations[idx2];
					console.log("allocation")
					console.log(allocation)

					// Note that for expenses, allocation.reference_type is 'Expense Entry Details' and not 'Expense Entry'
					if((allocation.reference_type == "Sales Invoice" && selected_reference_type!="Sales Invoice") || (allocation.reference_type == "Sales Return" && selected_reference_type!="Sales Return") || (allocation.reference_type == "Credit Note" && selected_reference_type!="Credit Note"))
					{
						console.log("hitted continue")
						continue;
					}

					for (var idx1= pending_invoices_with_value.length - 1; idx1>=0; idx1--)
					{
						if( allocation.reference_name == pending_invoices_with_value[idx1].reference_name)
						{
							if(allocation.paying_amount>0)
							{
								pending_invoices_with_value[idx1].paying_amount = allocation.paying_amount;

								if(pending_invoices_with_value[idx1].paid_amount + pending_invoices_with_value[idx1].paying_amount > pending_invoices_with_value[idx1].invoice_amount)
								{
									var difference = (pending_invoices_with_value[idx1].paid_amount + pending_invoices_with_value[idx1].paying_amount) - pending_invoices_with_value[idx1].invoice_amount

									pending_invoices_with_value[idx1].paying_amount = pending_invoices_with_value[idx1].paying_amount - difference

									frappe.msgprint("Excess allocation found. Allocation changed for " + allocation.purchase_invoice);
								}

							}
						}
					}

				}
			}

			child_table_control.df.data = pending_invoices_with_value;
			child_table_control.refresh();
		}
	});

	var dialog = new frappe.ui.Dialog({
		title: "Receipt Allocation",
		width: '100%',
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "sales",
				label: "Receipt Allocation",
				options: '<div id="child-table-wrapper"></div>',
			},
		],
		primary_action: function() {

			var child_table_data_updated = child_table_control.get_value();
			var index = 0 ;
			var invoice_no;

			console.log("child_table_data_updated")
			console.log(child_table_data_updated)

			//Check for excess allocation
			child_table_data_updated.forEach(element => {

				index = index + 1;

				// invoice_no = element.invoice_no

				if(element.paying_amount> element.balance_amount)
				{
					frappe.throw("Wrong input at line number " + index +". Paying amount cannot be more than the balance amount")
				}
			});

			//Existing allocation
			var child_table_data = cur_frm.doc.receipt_allocation;

			console.log("child_table_data")
			console.log(child_table_data)

			console.log("selected customer")
			console.log(selected_customer)
			console.log("selected reference_type")
			console.log(selected_reference_type)

			// //Clean allocations
			// if (child_table_data !== undefined) {
			// 	cur_frm.doc.receipt_allocation = cur_frm.doc.receipt_allocation.filter(row =>
			// 		!(row.customer === selected_customer && row.reference_type === selected_reference_type)
			// 	);
			
			// 	cur_frm.refresh_field("receipt_allocation");
			// }
			
			if (child_table_data !== undefined) {
				// Find indexes of rows that match the condition to be removed
				let indexesToRemove = [];
				for (let i = 0; i < cur_frm.doc.receipt_allocation.length; i++) {
					let row = cur_frm.doc.receipt_allocation[i];
					if (row.customer === selected_customer && row.reference_type === selected_reference_type) {
						indexesToRemove.push(i);
					}
				}
			
				// Remove rows in reverse order to avoid index shift issues
				for (let i = indexesToRemove.length - 1; i >= 0; i--) {
					cur_frm.doc.receipt_allocation.splice(indexesToRemove[i], 1);
				}
			
				cur_frm.refresh_field("receipt_allocation");
			}

			var totalPay = 0;

			child_table_data_updated.forEach(element => {

				console.log("element")

				console.log(element)

				if(element.paying_amount>0)
				{
					var row_allocation = frappe.model.get_new_doc('Payment Allocation');
					row_allocation.customer = element.customer

					row_allocation.reference_type = element.reference_type
					row_allocation.reference_name =  element.reference_name
					row_allocation.total_amount = element.invoice_amount

					console.log("element.reference_type")
					console.log(element.reference_type)

					console.log("element.reference_name")
					console.log(element.reference_name)

					// row.paid_amount = row.invoice_amount- element.balance_amount + element.paying_amount

					// Again update the balance amount to include the current paying amouunt in thet balance amount
					// row.balance_amount = row.invoice_amount - row.paid_amount + row.paying_amount

					// row.balance_amount = element.balance_amount
					row_allocation.paying_amount = element.paying_amount
					row_allocation.paid_amount = element.paid_amount
					row_allocation.balance_amount = element.balance_amount
					totalPay = totalPay + element.paying_amount
					row_allocation.receipt_entry_detail = frm.doc.receipt_entry_details[row.idx]

					cur_frm.add_child('receipt_allocation', row_allocation);

					cur_frm.refresh_field('receipt_allocation');

					console.log("row_allocation")
					console.log(row_allocation)

				}
			}

			);

			frappe.model.set_value(cdt, cdn, 'amount', totalPay);
			frappe.model.set_value(cdt, cdn, 'allocated_amount', totalPay);

			frm.trigger("calculate_total_and_set_fields");

			cur_frm.refresh_field('receipt_allocation');

			dialog.hide();
		},

	});
	dialog.$wrapper.find('.modal-dialog').css("max-width", "90%").css("width", "90%");

	dialog.show();
},
}
)
let create_custom_buttons = function(frm){
	if (frappe.user.has_role('Management')) {
		if(!frm.is_new() && (frm.doc.docstatus == 1)){
		frm.add_custom_button('General Ledgers',() =>{
				general_ledgers(frm)
		}, 'Postings');
		}
	}
}

let general_ledgers = function (frm) {
    frappe.call({
        method: "digitz_erp.api.accounts_api.get_gl_postings",
        args: {
			voucher:frm.doc.doctype,
            voucher_no: frm.doc.name
        },
        callback: function (response) {
            let gl_postings = response.message;

            // Generate HTML content for the popup
            let htmlContent = '<div style="max-height: 400px; overflow-y: auto;">' +
                              '<table class="table table-bordered" style="width: 100%;">' +
                              '<thead>' +
                              '<tr>' +
                              '<th style="width: 20%;">Account</th>' +
                              '<th style="width: 15%;">Debit Amount</th>' +
                              '<th style="width: 15%;">Credit Amount</th>' +
                              '<th style="width: 25%;">Against Account</th>' +
                              '<th style="width: 25%;">Remarks</th>' +
                              '</tr>' +
                              '</thead>' +
                              '<tbody>';

							  gl_postings.forEach(function (gl_posting) {
								// Handling null values for remarks
								let remarksText = gl_posting.remarks || '';  // Replace '' with a default text if you want to show something other than an empty string

								// Ensure debit_amount and credit_amount are treated as floats and format them
								let debitAmount = parseFloat(gl_posting.debit_amount).toFixed(2);
								let creditAmount = parseFloat(gl_posting.credit_amount).toFixed(2);

								htmlContent += '<tr>' +
											   `<td>${gl_posting.account}</td>` +
											   `<td style="text-align: right;">${debitAmount}</td>` +
											   `<td style="text-align: right;">${creditAmount}</td>` +
											   `<td>${gl_posting.against_account}</td>` +
											   `<td>${remarksText}</td>` +
											   '</tr>';
							});

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
            d.$wrapper.find('.modal-dialog').css('max-width', '72%'); // or any specific width like 800px

            d.show();
        }
    });
};


frappe.ui.form.on("Receipt Entry",{
    refresh: function(frm){
        let prev_customer = localStorage.getItem('prev_customer')
        let prev_project = localStorage.getItem('prev_project')
        
        if(prev_customer && prev_project){
            console.log("Receipt Entry With Custom Data.")
			frm.set_df_property("advance_section_break","hidden",0);
            frm.set_value('project', prev_project);
            frm.set_value('customer', prev_customer);
            frm.set_value('advance_payment',1)
        }
		localStorage.removeItem('prev_customer');
		localStorage.removeItem('prev_project');

    }
})