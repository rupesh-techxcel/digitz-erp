// Copyright (c) 2022, Rupesh P and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Entry', {

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
			}
		})
	}
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
allocations: function(frm, cdt, cdn)
{
	var row = locals[cdt][cdn];
	var child_table_control	;

	var selected_supplier = row.supplier
	var selected_reference_type = row.reference_type

	//Allocations are restricted with only one per supplier. So verify that there is no other
	//row exists with allocation for the selected_supplier

	var payment_entries = cur_frm.doc.payment_entry_details;

	if(payment_entries != undefined)
	{
		for (var i = payment_entries.length - 1; i >= 0; i--) {

			var payment = payment_entries[i];

			if(payment.supplier == selected_supplier && payment.allocated_amount>0
				 && payment.name !=cdn )
			{
				frappe.msgprint("Allocation already exists for the supplier.");
				return;
			}
		}
	}

	var allocations_exist;

	if (cur_frm.doc.__islocal)
	{

        frappe.call({

            method: "digitz_erp.api.payment_entry_api.get_all_supplier_payment_allocations",
            async:false,
            args: {
                supplier: selected_supplier
            },
            callback:(r) => {
                allocations_exist = r.message.values
            }});
	}
	else
	{
		frappe.call({

			method: "digitz_erp.api.payment_entry_api.get_all_supplier_payment_allocations_except_selected",
			async:false,
			args: {
				supplier: selected_supplier,
				payment_no: frm.doc.name
			},
			callback:(r) => {
				allocations_exist = r.message.values
			}});
	}

	var pending_invoices_data;

	frappe.call({
		method: "digitz_erp.api.purchase_invoice_api.get_supplier_pending_invoices",
		args: {
			supplier: selected_supplier,
			reference_type: selected_reference_type
		},
		callback:(r) => {

			pending_invoices_data = r.message.values;

			console.log("pending_invoices_data");
			console.log(pending_invoices_data);

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
							options:"reference_type",
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

			if(selected_reference_type == 'Expense'){
				console.log("Expense");
				for (var j= pending_invoices_data.length - 1; j>=0; j--)
				{
					var expense_no = pending_invoices_data[j].expense_no

					pending_invoices_data[j].reference_type = 'Expense Entry';
					pending_invoices_data[j].reference_name = expense_no;

					pending_invoices_data[j].paid_amount = pending_invoices_data[j].paid_amount;
					pending_invoices_data[j].balance_amount =  pending_invoices_data[j].paid_amount;
					pending_invoices_data[j].invoice_amount =  pending_invoices_data[j].paid_amount;
					pending_invoices_data[j].paying_amount =  pending_invoices_data[j].paid_amount;
				}

				var pending_invoices_with_value = []
				for (var j= pending_invoices_data.length - 1; j>=0; j--)
				{
					pending_invoices_with_value.push(pending_invoices_data[j])
				}
				console.log("pending_invoices_with_value");
				console.log(pending_invoices_with_value);
				child_table_control.df.data = pending_invoices_with_value;
			}

			if(selected_reference_type == 'Purchase'){
				//Stage 1.
				//Intiially set the paid_amount as zero and balance_amount as invoice amount
				//Iterate through the allocations for the particular invoice
				//During the iteeration assign the paid amount and balance amount based on the allocation
				//Note that the allocations fetched does not include current document allocation

				for (var j= pending_invoices_data.length - 1; j>=0; j--)
				{

					var purchase_invoice_no = pending_invoices_data[j].invoice_no

					pending_invoices_data[j].reference_type = 'Purchase Invoice';
					pending_invoices_data[j].reference_name = purchase_invoice_no;

					pending_invoices_data[j].paid_amount = 0;
					pending_invoices_data[j].balance_amount =  pending_invoices_data[j].invoice_amount;
					// pending_invoices_data[j].posting_date = frappe.format(pending_invoices_data[j].posting_date, { fieldtype: 'Date' })

					for (var i = allocations_exist.length - 1; i>=0; i--)
					{
						if(purchase_invoice_no == allocations_exist[i].purchase_invoice)
						{
							//Update teh paid amount
							pending_invoices_data[j].paid_amount  = pending_invoices_data[j].paid_amount  + allocations_exist[i].paying_amount;

							//First set balance amount as invoice_amount - paid amount
							pending_invoices_data[j].balance_amount = pending_invoices_data[j].balance_amount - allocations_exist[i].paying_amount;

						}
					}
				}

				var pending_invoices_with_value = []

				for (var j= pending_invoices_data.length - 1; j>=0; j--)
				{
					if(pending_invoices_data[j].balance_amount >0)
					{
						pending_invoices_with_value.push(pending_invoices_data[j]);
					}
				}

				if(pending_invoices_data.length> pending_invoices_with_value.length)
				{
					frappe.msgprint("Allocations without balance amount has been removed")
				}

				//Stage 2.
				// Get the values input from the allocations table in the current document
				// Adjust the paid amount based on the paying amount
				var allocations = cur_frm.doc.payment_allocation;

				console.log("allocations")
				console.log(allocations)

				if(allocations != undefined)
				{
					for (var i = allocations.length - 1; i >= 0; i--) {

						var allocation = allocations[i];

						for (var j= pending_invoices_with_value.length - 1; j>=0; j--)
						{
							if(allocation.purchase_invoice == pending_invoices_with_value[j].invoice_no)
							{
								if(allocation.paying_amount>0)
								{
									pending_invoices_with_value[j].paying_amount = allocation.paying_amount;

									if(pending_invoices_with_value[j].paid_amount + pending_invoices_with_value[j].paying_amount > pending_invoices_with_value[j].invoice_amount)
									{
										var difference = (pending_invoices_with_value[j].paid_amount + pending_invoices_with_value[j].paying_amount) - pending_invoices_with_value[j].invoice_amount

										pending_invoices_with_value[j].paying_amount = pending_invoices_with_value[j].paying_amount - difference

										frappe.msgprint("Excess allocation found. Allocation changed for " + allocation.purchase_invoice);
									}

								}
							}
						}

					}
				}

				child_table_control.df.data = pending_invoices_with_value;
			}
			child_table_control.refresh();
		}
	});

	var dialog = new frappe.ui.Dialog({
		title: "Invoice Allocation",
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

				invoice_no = element.invoice_no

				if(element.paying_amount> element.balance_amount)
				{
					frappe.throw("Wrong input at line number " + index + ", Invoice No -"+ invoice_no + ". Paying amount cannot be more than the balance amount")
				}
			});

			//Existing allocation
			var child_table_data = cur_frm.doc.payment_allocation;

			console.log("child_table_data")
			console.log(child_table_data)

			// Remove all existging allocation for the customer
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
					row_allocation.reference_type = element.reference_type
					row_allocation.reference_name =  element.reference_name
					row_allocation.total_amount = element.invoice_amount
					// row.paid_amount = row.invoice_amount- element.balance_amount + element.paying_amount

					// Again update the balance amount to include the current paying amouunt in thet balance amount
					// row.balance_amount = row.invoice_amount - row.paid_amount + row.paying_amount

					// row.balance_amount = element.balance_amount
					row_allocation.paying_amount = element.paying_amount
					row_allocation.paid_amount = element.paying_amount
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

			dialog.hide();
		},


	});
	dialog.$wrapper.find('.modal-dialog').css("max-width", "70%").css("width", "70%");

	dialog.show();
},
}
)
