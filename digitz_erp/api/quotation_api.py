import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_quotation_data(quotation_no):	
    
    return frappe.db.get_get_value("Quotation", quotation_no,["name","customer_name", "customer_address","reference_no","posting_date", "credit_sale"], as_dict=1)
    
    