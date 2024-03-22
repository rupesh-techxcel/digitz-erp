import frappe

@frappe.whitelist()
def do_not_allow_multiple_doctype_creation(sales_order):
    result = {
        'exists_in_delivery_note': False,
        'exists_in_sales_invoice': False
    }

    # Check in Delivery Note
    if frappe.db.exists('Delivery Note Sales Orders', {'sales_order': sales_order}):
        result['exists_in_delivery_note'] = True

    # Check in Sales Invoice
    if frappe.db.exists('Sales Invoice', {'sales_order': sales_order}):
        result['exists_in_sales_invoice'] = True

    return result
    
    
    