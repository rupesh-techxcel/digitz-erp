import frappe

@frappe.whitelist()
def sales_invoice_exists_for_delivery_note(delivery_note):
    frappe.db.exists('Sales Invoice Delivery Notes', {'delivery_note': delivery_note})
    
@frappe.whitelist()
def get_sales_invoice_status_for_delivery_note(delivery_note):
    
   if(frappe.db.exists('Sales Invoice Delivery Notes', {'delivery_note': delivery_note})):    
       sales_invoice = frappe.db.get_value('Sales Invoice Delivery Notes', {'delivery_note':delivery_note},['parent'])
       return frappe.db.get_value('Sales Invoice',sales_invoice, ['docstatus'])
   else:
       frappe.throw("Mismatched workflow logic.")
    

    