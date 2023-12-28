// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Entry', {

	refresh:function(frm){

		frm.fields_dict['payment_entry_details'].grid.get_field('account').get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    is_group: 0  // Set filters to only show accounts where is_group is false
                }
            };
		}
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
		frm.set_df_property('payment_allocation', 'hidden', !frm.doc.show_allocations);
		cur_frm.refresh_field('payment_allocation');
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
		var allocations = frm.doc.payment_allocation || [];
		for(var i = 0; i < allocations.length; i++)
		{

			var payments = frm.doc.payment_entry_details;

			var allocation_found =false;

			for(var j = 0; j < payments.length; j++)
			{
				if(payments[j].supplier == allocations[i].supplier && allocations[i].allocated_amount>0)
				{
					allocation_found = true;
				}
			}

			if( !allocation_found)
			{
				cur_frm.get_field('payment_allocation').grid.grid_rows[i].remove();
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
		var payment_detail = frm.doc.payment_entry_details;

		var total =0;
		var total_allocated = 0;

		for (var i = 0; i< payment_detail.length; i++) {

			total = total + payment_detail[i].amount;
			total_allocated = total_allocated + payment_detail[i].allocated_amount;
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
		var allocations = cur_frm.doc.payment_allocation;

		console.log("allocations before clean")
		console.log(allocations)

		var allocations_to_remove = []

		if(allocations != undefined)
		{
			for (var i = allocations.length - 1; i >= 0; i--)
			{
				var allocation = allocations[i];

				var payments = cur_frm.doc.payment_entry_details;

				if(payments != undefined)
				{
					var payment_exists = false;
					for (var j = 0; j< payments.length;  j++) {

						if(payments[j].supplier == allocation.supplier && payments[j].allocated_amount != undefined && payments[j].allocated_amount>0 )
						{
							payment_exists= true
						}
					}

					if(!payment_exists)
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
					cur_frm.doc.payment_allocation = cur_frm.doc.payment_allocation.filter(
						function (row){
							return row.supplier != allocations_to_remove[i].supplier
						}
					)

					cur_frm.refresh_field("payment_allocation");
				}
			}

			console.log("allocations after clean")
			console.log(allocations)
			console.log(allocations_to_remove)
		}
	}
}
);

frappe.ui.form.on("Payment Entry", "onload", function (frm) {

	if(frm.doc.__islocal)
		frm.trigger("get_default_company_and_warehouse");
	
	}
);

frappe.ui.form.on("Payment Entry Detail", {

payment_type: function(frm, cdt, cdn) {

  	var row = locals[cdt][cdn];
	if(row.payment_type == "Supplier")
	{	

		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				'doctype': 'Global Settings',
				'fieldname': 'default_company'
			},
			callback: (r) => {

		 		frappe.db.get_value("Company", r.message.default_company, "default_payable_account").then((r) => {
	 			var default_payable_account = r.message.default_payable_account;
	 			frappe.model.set_value(cdt, cdn, 'account', default_payable_account)});
				frm.refresh_field("payment_entry_details")
			}
		})
	}
},
payment_entry_details_add:function(frm,cdt,cdn)
{	
	frappe.call({
		method: 'frappe.client.get_value',
		args: {
			'doctype': 'Global Settings',
			'fieldname': 'default_company'
		},
		callback: (r) => {

			 frappe.db.get_value("Company", r.message.default_company, "default_payable_account").then((r) => {
			 var default_payable_account = r.message.default_payable_account;
			 frappe.model.set_value(cdt, cdn, 'account', default_payable_account)});
			frm.refresh_field("payment_entry_details")
		}
	});

	var row = locals[cdt][cdn];
	row.payment_type = "Supplier"
	row.reference_type = "Purchase Invoice"
	row.reference_no = frm.doc.reference_no	
	row.reference_date = frm.doc.reference_date	
},
payment_entry_details_remove: function(frm,cdt,cdn)
{
	frm.trigger("clean_allocations");
	frm.trigger("calculate_total_and_set_fields");
},
amount: function(frm,cdt,cdn)
{
	frm.trigger("calculate_total_and_set_fields");
},
// payment_type: function(frm,cdt,cdn)
// {
// 	var row = locals[cdt][cdn];
// 	if(row.payment_type != "Supplier")
// 	{
// 		row.supplier = ""
		
// 		frm.set_df_property('payment_entry_details', 'hidden', !frm.doc.show_allocations);
// 		frappe.model.set_df_property('[Payment Entry Detail]', row.name, '[supplier]', 'read_only', 1);
// 		frm.refresh_field("payment_entry_details")
// 	}
// },
allocations: function(frm, cdt, cdn)
{
	const row = locals[cdt][cdn];
	let child_table_control	;
	
	if(row.payment_type != "Supplier" || (!row.reference_type) ||  row.reference_type == "" ||  (!row.supplier))
	{
		frappe.throw("Invalid criteria for allocations.")
	}

	const selected_supplier = row.supplier
	const selected_reference_type = row.reference_type

	//Allocations are restricted with only one per supplier. So verify that there is no other
	//row exists with allocation for the selected_supplier

	const payment_entries = cur_frm.doc.payment_entry_details;

	// Checking for allocations exists for the supplier in a different row
	if(payment_entries != undefined)
	{
		for (var i = payment_entries.length - 1; i >= 0; i--) {

			var payment = payment_entries[i];

			if(payment.supplier == selected_supplier && typeof(payment.reference_type) != undefined &&  payment.reference_type==selected_reference_type && payment.allocated_amount>0
				 && payment.name !=cdn )
			{
				// Create the message string
				var message = "Allocation exists for the {0} and {1} at line no {2}".format(selected_supplier, selected_reference_type, i);

				// Display the message using frappe.msgprint
				frappe.msgprint(message);
				return;
			}
		}
	}

	let allocations_exists_in_other_payments;

	// Fetch the supplier invoices at the stage on which the document was not yet saved

	frappe.call({

		method: "digitz_erp.api.payment_entry_api.get_all_supplier_pending_payment_allocations_with_other_payments",
		async:false,
		args: {
			supplier: selected_supplier,
			reference_type: selected_reference_type,
			payment_no: cur_frm.doc.__islocal ? "" : frm.doc.name
		},
		callback:(r) => {
			allocations_exists_in_other_payments = r.message.values	
			console.log("allocations_exists_in_other_payments")	
			console.log(allocations_exists_in_other_payments)
		}});	

	let pending_invoices_data	
	//Fetch all supplier pending invoices and invoices already allocated in this payment_entry
	frappe.call({
		method: "digitz_erp.api.payment_entry_api.get_supplier_pending_documents",
		args: {
			supplier: selected_supplier,
			reference_type: selected_reference_type,
			payment_no: cur_frm.doc.__islocal ? "" : frm.doc.name
		},
		callback:(r) => {

			pending_invoices_data = r.message;
			console.log("pending invoices data")

			if(selected_reference_type == "Purchase Invoice")
			{
				child_table_control = frappe.ui.form.make_control({
					df: {
						fieldname: "payment_allocation",
						fieldtype: "Table",
						cannot_add_rows:true,
						fields: [
							{
								fieldtype: 'Select',
								fieldname: 'reference_type',
								label: 'Reference Type',
								options: 'Purchase Invoice\n Expense Entry',
								in_place_edit: false,
								in_list_view: true,
								read_only:true
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
							// {
							// 	fieldtype: "Date",
							// 	fieldname: "date",
							// 	label: "Date",							
							// 	in_place_edit: false,
							// 	in_list_view: true,
							// 	// width: "40%",
							// 	read_only:true
							// },
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
					parent: dialog.get_field("purchase").$wrapper,
					render_input: true,
				});
			}
			else if (selected_reference_type=="Expense Entry")
			{
				console.log("here")
				child_table_control = frappe.ui.form.make_control({
					df: {
						fieldname: "payment_allocation",
						fieldtype: "Table",
						cannot_add_rows:true,
						fields: [
							{
								fieldtype: 'Select',
								fieldname: 'reference_type',
								label: 'Reference Type',
								options: 'Purchase Invoice\n Expense Entry',
								in_place_edit: false,
								in_list_view: true,
								read_only:true
							},
							// {
							// 	fieldtype: "Link",
							// 	fieldname: "reference_name",
							// 	label: "Reference Name",							
							// 	in_place_edit: false,
							// 	in_list_view: true,
							// 	// width: "40%",
							// 	read_only:true
							// },
							{
								fieldtype: "Link",
								fieldname: "document_no",
								label: "Document No",							
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
					parent: dialog.get_field("purchase").$wrapper,
					render_input: true,
				});	
			}
			
			//Stage 1.
			//Intiially set the paid_amount as zero and balance_amount as invoice amount
			//Iterate through the allocations for the particular invoice
			//During the iteeration assign the paid amount and balance amount based on the allocation
			//Note that the allocations fetched does not include current document allocation
			
			// console.log("pending_invoices_data")
			// console.log(pending_invoices_data)

			console.log("allocations_exists_in_other_payments")
			console.log(allocations_exists_in_other_payments)

			for (var idx1= pending_invoices_data.length - 1; idx1>=0; idx1--)
			{	
				// console.log("value of j")
				// console.log(j)

				pending_invoices_data[idx1].paid_amount = 0;
				pending_invoices_data[idx1].balance_amount =  pending_invoices_data[idx1].invoice_amount;
				// pending_invoices_data[j].posting_date = frappe.format(pending_invoices_data[j].posting_date, { fieldtype: 'Date' })

				for (var idx2 = allocations_exists_in_other_payments.length - 1; idx2>=0; idx2--)
				{
					// console.log("pending_invoices_data[j].reference_name")
					// console.log(pending_invoices_data[j].reference_name)

					// console.log("allocations_exists_in_other_payments[i].reference_name")
					// console.log(allocations_exists_in_other_payments[i].reference_name)

					if(pending_invoices_data[idx1].reference_name == allocations_exists_in_other_payments[idx2].reference_name)
					{
						//Update teh paid amount
						pending_invoices_data[idx1].paid_amount  = pending_invoices_data[idx1].paid_amount  + allocations_exists_in_other_payments[idx2].paying_amount;
						// console.log("allocations_exists_in_other_payments[i].paying_amount");
						// console.log(allocations_exists_in_other_payments[i].paying_amount);
						// console.log("new paid_amount")
						// console.log(pending_invoices_data[j].paid_amount)
						//First set balance amount as invoice_amount - paid amount
						pending_invoices_data[idx1].balance_amount = pending_invoices_data[idx1].balance_amount - allocations_exists_in_other_payments[idx2].paying_amount;
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
			var allocations = cur_frm.doc.payment_allocation;
			console.log(allocations)
		
			if(allocations)
			{
				for (var idx2 = allocations.length - 1; idx2 >= 0; idx2--) {

					var allocation = allocations[idx2];
					console.log("allocation")
					console.log(allocation)

					// Note that for expenses, allocation.reference_type is 'Expense Entry Details' and not 'Expense Entry'
					if((allocation.reference_type=="Expense Entry Details" && selected_reference_type!="Expense Entry")  || (allocation.reference_type == "Purchase Invoice" && selected_reference_type!="Purchase Invoice"))
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
		title: "Payment Allocation",
		width: '100%',
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "purchase",
				label: "Payment Allocation",
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
			var child_table_data = cur_frm.doc.payment_allocation;

			console.log("child_table_data")
			console.log(child_table_data)

			//Clean allocations
			if(child_table_data != undefined)
			{
				cur_frm.doc.payment_allocation = cur_frm.doc.payment_allocation.filter(
					function (row){
						return row.supplier != selected_supplier
					}
				)

				cur_frm.refresh_field("payment_allocation");
			}

			var totalPay = 0;

			child_table_data_updated.forEach(element => {

				console.log("element")

				console.log(element)

				if(element.paying_amount>0)
				{
					var row_allocation = frappe.model.get_new_doc('Payment Allocation');
					row_allocation.supplier = element.supplier
					//Issue fix for the dynamic link mismatch 
					// Change reference type to 'Expense Entry Details' for Expense Entry since the actual doctype for the dynamic link is 'Expense Entry Details' and not 'Expense Entry'. 
					if(element.reference_type == "Expense Entry")
					{
						row_allocation.reference_type = "Expense Entry Details"
					}
					else
					{
						row_allocation.reference_type = element.reference_type
					}
					
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
					row_allocation.payment_entry_detail = frm.doc.payment_entry_details[row.idx]

					cur_frm.add_child('payment_allocation', row_allocation);

					cur_frm.refresh_field('payment_allocation');

					console.log("row_allocation")
					console.log(row_allocation)

				}
			}

			);

			frappe.model.set_value(cdt, cdn, 'amount', totalPay);
			frappe.model.set_value(cdt, cdn, 'allocated_amount', totalPay);

			frm.trigger("calculate_total_and_set_fields");

			cur_frm.refresh_field('payment_allocation');

			dialog.hide();
		},

	});
	dialog.$wrapper.find('.modal-dialog').css("max-width", "90%").css("width", "90%");

	dialog.show();
},
}
)
