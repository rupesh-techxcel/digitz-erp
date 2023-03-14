import frappe

@frappe.whitelist()
def delivery_note_exists_for_sales_invoice(delivery_note):
    frappe.db.exists('Sales Invoice Delivery Notes', {'delivery_note': delivery_note})

    