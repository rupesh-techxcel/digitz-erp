# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type

class AdditionalExpenseEntry(Document):
	pass

@frappe.whitelist()
def get_purchase_invoice_items(selected_invoices):
    if isinstance(selected_invoices, str):
        selected_invoices = frappe.parse_json(selected_invoices)
    items = []
    for invoice in selected_invoices:
        invoice_items = frappe.get_all('Purchase Invoice Item',
                                       filters={'parent': invoice},
                                       fields=['item', 'qty', 'net_amount'])
        items.extend(invoice_items)

    return items

@frappe.whitelist()
def get_sales_invoice_items(selected_invoices):
    if isinstance(selected_invoices, str):
        selected_invoices = frappe.parse_json(selected_invoices)
    items = []
    for invoice in selected_invoices:
        invoice_items = frappe.get_all('Sales Invoice Item',
                                       filters={'parent': invoice},
                                       fields=['item', 'qty', 'net_amount'])
        items.extend(invoice_items)

    return items
