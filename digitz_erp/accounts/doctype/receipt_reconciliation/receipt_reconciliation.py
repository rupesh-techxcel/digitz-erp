# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.receipt_entry_api import get_allocations_for_sales_invoice,get_allocations_for_progressive_sales_invoice


class ReceiptReconciliation(Document):

	def on_submit(self):
		self.adjust_receipts_based_on_reconciliation()
		self.update_sales_invoices()
		self.update_progressive_invoices()

	def on_cancel(self):
		self.revert_invoices_on_cancellation()

	def adjust_receipts_based_on_reconciliation(self):
		for invoice in self.invoices:
			if invoice.allocated_amount > 0:
				receipt_no = invoice.receipt_no
				invoice_type = invoice.invoice_type
				customer = self.customer
				receipt_original_reference_type = invoice.receipt_original_reference_type

				# Process only 'Sales Order' records, skip 'On Account' as there are no rows in Receipt Allocation for it
				if receipt_original_reference_type == "Sales Order":
					
					# Fetch the corresponding receipt allocation from `tabReceipt Allocation`
					receipt_allocations = frappe.db.get_all(
						"Receipt Allocation", 
						filters={
							'parent': receipt_no, 
							'customer': customer, 
							'reference_type': receipt_original_reference_type
						}, 
						fields=['name', 'parent_field']
					)

					# Iterate over the fetched receipt allocations and update the parent_field
					for receipt_allocation in receipt_allocations:
						if receipt_allocation.get('parent_field') == 'receipt_allocation':
							# Update the parent_field to 'previous_receipt_allocations'
							frappe.db.set_value(
								"Receipt Allocation", 
								receipt_allocation.get('name'), 
								'parent_field', 
								'previous_receipt_allocations'
							)
							frappe.db.commit()

					frappe.msgprint(f"Receipt allocations for {receipt_no} have been updated.",alert=True)

					# Insert new record for 'Sales Order' into `Receipt Allocation`
					new_receipt_allocation = frappe.get_doc({
						"doctype": "Receipt Allocation",
						"parent": receipt_no,
						"customer": customer,
						"total_amount": invoice.invoice_amount,
						"paying_amount": invoice.allocated_amount,
						"reference_type": invoice.reference_type,
						"reference_name": invoice.invoice_no,  # Assuming invoice_no represents the document number
						"parent_field": "receipt_allocation",
						"owner": frappe.session.user,  # Current user as owner
						"docstatus": 1  # Mark as submitted
					})

					# Insert and submit the new document
					new_receipt_allocation.insert(ignore_permissions=True)
					frappe.db.commit()

					frappe.msgprint(f"New receipt allocation for {receipt_no} has been created.", alert=True)

					# Additional update for `tabReceipt Details`
					# Fetch the corresponding receipt detail record
					receipt_details = frappe.db.get_all(
						"Receipt Details",
						filters={
							'parent': receipt_no,
							'customer': customer,
							'reference_type': receipt_original_reference_type  # Match original reference type
						},
						fields=['name']
					)

					# Update the found record's reference_type and previous_reference_type
					for detail in receipt_details:
						frappe.db.set_value(
							"Receipt Details",
							detail.get('name'),
							{
								'reference_type': invoice.reference_type,
								'previous_reference_type': receipt_original_reference_type
							}
						)
						frappe.db.commit()

					frappe.msgprint(f"Receipt details for {receipt_no} have been updated.", alert=True)

	def reverse_adjustments_on_cancellation(self):
		
		for invoice in self.invoices:
			if invoice.allocated_amount > 0:
				receipt_no = invoice.receipt_no
				customer = self.customer
				receipt_original_reference_type = invoice.receipt_original_reference_type

				# Process only 'Sales Order' records
				if receipt_original_reference_type == "Sales Order":
					
					# Fetch the receipt allocations that were inserted (parent_field = 'receipt_allocation')
					receipt_allocations_to_delete = frappe.db.get_all(
						"Receipt Allocation", 
						filters={
							'parent': receipt_no,
							'customer': customer,
							'reference_name': invoice.invoice_no,  # Assuming invoice_no represents the document number
							'parent_field': 'receipt_allocation'
						},
						fields=['name']
					)

					# Delete the newly created receipt allocation records
					for receipt_allocation in receipt_allocations_to_delete:
						frappe.delete_doc("Receipt Allocation", receipt_allocation.get('name'))
					
					# Revert the updated receipt allocations (parent_field = 'previous_receipt_allocations')
					receipt_allocations_to_revert = frappe.db.get_all(
						"Receipt Allocation", 
						filters={
							'parent': receipt_no, 
							'customer': customer, 
							'reference_type': receipt_original_reference_type,
							'parent_field': 'previous_receipt_allocations'
						},
						fields=['name']
					)

					# Update 'parent_field' back to 'receipt_allocation'
					for receipt_allocation in receipt_allocations_to_revert:
						frappe.db.set_value(
							"Receipt Allocation", 
							receipt_allocation.get('name'), 
							'parent_field', 
							'receipt_allocation'
						)

					frappe.db.commit()
					frappe.msgprint(f"Reversed receipt allocations for {receipt_no}.")

					# New: Fetch the receipt details that were updated
					receipt_details_to_update = frappe.db.get_all(
						"Receipt Details",
						filters={
							'parent': receipt_no,
							'customer': customer,
							'reference_type': invoice.reference_type  # Match the current reference type
						},
						fields=['name']
					)

					# Update the found record's reference_type and previous_reference_type
					for detail in receipt_details_to_update:
						frappe.db.set_value(
							"Receipt Details",
							detail.get('name'),
							{
								'reference_type': invoice.receipt_original_reference_type,
								'previous_reference_type': invoice.reference_type  # Store current reference as previous
							}
						)
					frappe.db.commit()

					frappe.msgprint(f"Receipt details for {receipt_no} have been reverted.", alert=True)

	def update_sales_invoices(self):
		
		for invoice in self.invoices:

			if invoice.allocated_amount > 0:

				allocations = get_allocations_for_sales_invoice(invoice.invoice_no, invoice.receipt_no)
		
	def update_sales_invoices(self):
		
		invoices = self.invoices

		if(invoices):
			for invoice in invoices:

				if invoice.reference_type != "Sales Invoice":
					continue

				if(invoice.allocated_amount>0):

					receipt_no = invoice.receipt_no
					if self.is_new():
						receipt_no = ""

					previous_paid_amount = 0
					allocations_exists = get_allocations_for_sales_invoice(invoice.invoice_no, receipt_no)

					for existing_allocation in allocations_exists:
						previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount

					invoice_total = previous_paid_amount + invoice.allocated_amount

					frappe.db.set_value("Sales Invoice", invoice.invoice_no, {'paid_amount': invoice_total})

					invoice_amount = frappe.db.get_value("Sales Invoice", invoice.invoice_no,["rounded_total"])
					if(round(invoice_amount,2) > round(invoice_total,2)):
						frappe.db.set_value("Sales Invoice", allocation.reference_name, {'payment_status': "Partial"})
					elif round(invoice_amount,2) == round(invoice_total,2):
						frappe.db.set_value("Sales Invoice", allocation.reference_name, {'payment_status': "Paid"})
		
	def update_progressive_invoices(self):
		
		invoices = self.invoices

		if(invoices):
			for invoice in invoices:

				if invoice.reference_type != "Progressive Sales Invoice":
					continue

				if(invoice.allocated_amount>0):

					receipt_no = invoice.receipt_no
					if self.is_new():
						receipt_no = ""

					previous_paid_amount = 0
					allocations_exists = get_allocations_for_progressive_sales_invoice(invoice.invoice_no, receipt_no)

					for existing_allocation in allocations_exists:
						previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount

					invoice_total = previous_paid_amount + invoice.allocated_amount

					frappe.db.set_value("Progressive Sales Invoice", invoice.invoice_no, {'paid_amount': invoice_total})

					invoice_amount = frappe.db.get_value("Progressive Sales Invoice", invoice.invoice_no,["rounded_total"])
					if(round(invoice_amount,2) > round(invoice_total,2)):
						frappe.db.set_value("Progressive Sales Invoice", allocation.reference_name, {'payment_status': "Partial"})
					elif round(invoice_amount,2) == round(invoice_total,2):
						frappe.db.set_value("Progressive Sales Invoice", allocation.reference_name, {'payment_status': "Paid"})
		
	def revert_invoices_on_cancellation(self):
		
		invoices = self.invoices
		if(invoices):
			for invoice in invoices:
				if(invoice.allocated_amount>0):
		
					receipt_no = invoice.receipt_no
					
					previous_paid_amount = 0
					allocations_exists = get_allocations_for_sales_invoice(invoice.invoice_no, receipt_no) if invoice.reference_type =="Sales Invoice" else get_allocations_for_progressive_sales_invoice(invoice.invoice_no, receipt_no)
		
					for existing_allocation in allocations_exists:
						previous_paid_amount = previous_paid_amount +  existing_allocation.paying_amount

					total_paid_Amount = previous_paid_amount
					if invoice.reference_type == "Sales Invoice":
						frappe.db.set_value("Sales Invoice", invoice.invoice_no, {'paid_amount': total_paid_Amount})
					else :
						frappe.db.set_value("Progressive Sales Invoice", invoice.invoice_no, {'paid_amount': total_paid_Amount})
