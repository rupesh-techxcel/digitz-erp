import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_all_customer_receipt_allocations(customer):

    print(customer)
    
    values = frappe.db.sql("""SELECT sales_invoice,parent,invoice_amount,paying_amount FROM `tabReceipt Allocation` ra left outer join `tabSales Invoice` si ON si.name= ra.sales_invoice WHERE ra.customer = '{}' AND (ra.docstatus= 1 or ra.docstatus=0) AND (si.paid_amount IS NULL OR si.paid_amount!=si.rounded_total) ORDER BY ra.sales_invoice """.format(customer),as_dict=1)    
    
    print("values")
    print(values)
    
    return {'values': values}

@frappe.whitelist()
def get_all_customer_receipt_allocations_except_selected(customer, receipt_no):
   
    
    values = frappe.db.sql("""SELECT sales_invoice,parent,invoice_amount,paying_amount FROM `tabReceipt Allocation` ra left outer join `tabSales Invoice` si ON si.name= ra.sales_invoice WHERE ra.customer = '{0}' AND parent!='{1}' AND (ra.docstatus= 1 or ra.docstatus=0) AND (si.paid_amount IS NULL OR si.paid_amount!=si.rounded_total) ORDER BY ra.sales_invoice """.format(customer,receipt_no),as_dict=1)    
    
    return {'values': values}