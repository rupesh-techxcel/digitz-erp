# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Customer(Document):
	pass

@frappe.whitelist()
def merge_customer(current_customer, merge_customer):
    if not current_customer or not merge_customer:
        frappe.throw(_('Both customers must be specified'))
        
    if(current_customer == merge_customer):
        frappe.throw(_('Select a different customer to merge.'))
    
    # Fetch both customer docs
    current_customer_doc = frappe.get_doc('Customer', current_customer)
    merge_customer_doc = frappe.get_doc('Customer', merge_customer)
    
    # Logic to merge customer details
    # Example: Merge contact info, addresses, etc.
    # You need to customize this based on your requirements
    for fieldname in ['contact_info', 'addresses']:  # Add fields to merge
        if hasattr(merge_customer_doc, fieldname):
            if not hasattr(current_customer_doc, fieldname):
                setattr(current_customer_doc, fieldname, [])
            current_customer_doc.append(fieldname, merge_customer_doc.get(fieldname))
    
    # Save the updated current customer
    current_customer_doc.save()
    
    # Delete the merged customer
    frappe.delete_doc('Customer', merge_customer)
    
    return True
