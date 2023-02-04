import frappe

@frappe.whitelist()
def cancel_delivery_note(delivery_note):
    do = frappe.get_doc('Delivery Note',delivery_note)
    do.cancel()

@frappe.whitelist()
def delivery_note_exists_for_sales_invoice(delivery_note):
    frappe.db.exists('Sales Invoice Delivery Notes', {'delivery_note': delivery_note})


@frappe.whitelist()
def get_delivery_notes_for_sales_invoice(sales_invoice):

    delivery_notes = frappe.get_list("Sales Invoice Delivery Notes",{'parent': sales_invoice}, ['delivery_note']})

    index = 0
    maxIndex = 3
    doNos = ""
    
    for delivery_note in delivery_notes:        
        doNos = doNos + delivery_note + "   "
        index= index + 1
        if index == maxIndex:
            break

    return doNos




    