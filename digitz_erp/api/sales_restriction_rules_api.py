import frappe

@frappe.whitelist()
def do_not_allow_multiple_doctype_creation(sales_order):
    result = {
        'exists_in_delivery_note': False,
        'exists_in_sales_invoice': False
    }

    # Check in Delivery Note (excluding cancelled documents)
    if frappe.db.exists('Delivery Note', {
        'sales_order': sales_order,
        'docstatus': ['!=', 2]  # Exclude cancelled documents
    }):
        result['exists_in_delivery_note'] = True

    # Check in Sales Invoice (excluding cancelled documents)
    if frappe.db.exists('Sales Invoice', {
        'sales_order': sales_order,
        'docstatus': ['!=', 2]  # Exclude cancelled documents
    }):
        result['exists_in_sales_invoice'] = True

    return result
    
    
    