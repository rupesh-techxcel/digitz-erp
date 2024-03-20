import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_quotation_data(quotation_no):	
    
    return frappe.db.get_value("Quotation", quotation_no,["name","customer_name", "customer_address","reference_no","posting_date", "credit_sale", "tax_total","net_total", "rounded_total"], as_dict=1)

@frappe.whitelist()
def get_quotation_test():	    
    return "Test Success"

def get_quotation_items_data(quotation_no):	
    
    return frappe.db.sql("select item, display_name,qty,unit,rate,tax_rate, tax_amount,net_amount from `tabQuotation Item` where parent=" + quotation_no, ignore_user_permission=True)

@frappe.whitelist()
def get_sales_invoice_exists(qtn_no):    
   return frappe.db.exists('Sales Invoice', {'quotation': qtn_no})

@frappe.whitelist()
def get_sales_order_exists(qtn_no):    
   return frappe.db.exists('Sales Order', {'quotation': qtn_no})

@frappe.whitelist()
def get_delivery_note_exists(qtn_no):    
   return frappe.db.exists('Delivery Note', {'quotation': qtn_no})

# For quotation we dont allow multiple documents created for a single quotation. So checking existance of the reference in any of the documents is good enough
@frappe.whitelist()
def check_references_created(quotation_name):

    sales_order_exists_for_quotation = frappe.db.exists("Sales Order", {"quotation": quotation_name})

    if sales_order_exists_for_quotation:
        frappe.throw("Sales Order already exist for the quotation and cannot create additional references.")

    delivery_note_exists_for_quotation = frappe.db.exists("Delivery Note", {"quotation": quotation_name})

    if(delivery_note_exists_for_quotation):
        frappe.throw("Delivery Note already exist for the quotation and cannot create additional references")

    sales_invoice_exists_for_quotation = frappe.db.exists("Sales Invoice", {"quotation": quotation_name})

    if(sales_invoice_exists_for_quotation):
        frappe.throw("Sales Invoice already exist for the quotation and cannot create additional references.")