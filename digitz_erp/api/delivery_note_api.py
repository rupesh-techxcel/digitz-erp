import frappe

@frappe.whitelist()
def cancel_delivery_note(delivery_note):
    do = frappe.get_doc('Delivery Note',delivery_note)
    do.cancel()


def delivery_note_exists_for_sales_invoice(delivery_note):
    frappe.db.exists('Sales Invoice Delivery Notes', {'delivery_note': delivery_note})
    