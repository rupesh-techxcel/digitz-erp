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
@frappe.whitelist()
def get_pending_delivery_notes_for_new_sales_invoice(customer):

    query = """select name as 'Delivery Note', posting_date as 'Date', rounded_total as 'Amount' from `tabDelivery Note` dn where dn.docstatus=1 and dn.customer=%s and dn.name not in (select delivery_note from `tabSales Invoice Delivery Notes` where docstatus<2)"""
    delivery_notes = frappe.db.sql(query,(customer), as_dict = True)
    return delivery_notes

@frappe.whitelist()
def get_delivery_note_items(delivery_notes):
    
    # Assuming delivery_notes is a JSON string of delivery note names
    import json
    delivery_note_list = json.loads(delivery_notes)
    
    # Ensure the delivery_note_list is formatted correctly for the SQL IN clause
    delivery_note_list_tuple = tuple(delivery_note_list)

    
    
    # SQL query using placeholders for tuple
    query = """
    select 
        name as delivery_note_item_reference_no,
        item,
        qty,
        warehouse,
        item_name,
        display_name,
        unit,
        rate,
        base_unit,
        qty_in_base_unit,
        rate_in_base_unit,
        conversion_factor,
        rate_includes_tax,
        gross_amount,
        tax_excluded,
        tax_rate,
        tax_amount,
        discount_percentage,
        discount_amount,
        net_amount 
    from 
        `tabDelivery Note Item` 
    where 
        parent in %s 
        and parent not in (
            select 
                delivery_note 
            from 
                `tabSales Invoice Delivery Notes` 
            where 
                docstatus < 2
        ) 
        and docstatus = 1
    """

    # Executing the query
    items = frappe.db.sql(query, (delivery_note_list_tuple,), as_dict=True)
    
    return items

    

    