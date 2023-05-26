import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_all_supplier_payment_allocations(supplier):
    
    values = frappe.db.sql("""SELECT purchase_invoice,parent,invoice_amount,paying_amount FROM `tabPayment Allocation` ra left outer join `tabPurchase Invoice` si ON si.name= ra.purchase_invoice WHERE ra.supplier = '{}' AND (ra.docstatus= 1 or ra.docstatus=0) AND (si.paid_amount IS NULL OR si.paid_amount!=si.rounded_total) ORDER BY ra.purchase_invoice """.format(supplier),as_dict=1)
    
    return {'values': values}

@frappe.whitelist()
def get_all_supplier_payment_allocations_except_selected(supplier, payment_no):
   
    
    values = frappe.db.sql("""SELECT purchase_invoice,parent,invoice_amount,paying_amount FROM `tabPayment Allocation` ra left outer join `tabPurchase Invoice` si ON si.name= ra.purchase_invoice WHERE ra.supplier = '{0}' AND parent!='{1}' AND (ra.docstatus= 1 or ra.docstatus=0) AND (si.paid_amount IS NULL OR si.paid_amount!=si.rounded_total) ORDER BY ra.purchase_invoice """.format(supplier,payment_no),as_dict=1)    
    
    return {'values': values}