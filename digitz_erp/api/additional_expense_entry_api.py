import frappe
from frappe.utils import *

@frappe.whitelist()

def get_purchase_invoice_items(selected_invoices):
    
    if isinstance(selected_invoices, str):
        selected_invoices = frappe.parse_json(selected_invoices)
        
    items = []
    for invoice in selected_invoices:
        invoice_items = frappe.get_all('Purchase Invoice Item',
                                    filters={'parent': invoice},
                                    fields=['name','item','item_name','parent','qty','gross_amount', 'net_amount'])
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

@frappe.whitelist()
def get_purchase_invoice(name):        
    return frappe.get_doc("Purchase Invoice", name)

@frappe.whitelist()
def get_sales_invoice(name):    
    return frappe.get_doc("Sales Invoice", name)  