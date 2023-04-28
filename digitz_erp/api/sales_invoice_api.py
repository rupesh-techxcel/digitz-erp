import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_customer_pending_invoices(customer):

    values = frappe.db.sql("""SELECT customer,name as invoice_no,posting_date,paid_amount,rounded_total as invoice_amount,rounded_total-paid_amount as balance_amount FROM `tabSales Invoice` WHERE customer = '{}' AND docstatus =0 AND credit_sale = 1 AND rounded_total != paid_amount""".format(customer),as_dict=1)
    print(values)    
    return {'values': values}

@frappe.whitelist()
def get_allocations_for_invoice(sales_invoice_no, receipt_no):    
    if(receipt_no ==""):        
        return frappe.db.sql("""SELECT sales_invoice,parent,invoice_amount,paying_amount FROM `tabReceipt Allocation` ra inner join `tabSales Invoice` si ON si.name= ra.sales_invoice WHERE ra.sales_invoice = '{0}' AND (ra.docstatus= 1 or ra.docstatus=0) ORDER BY ra.sales_invoice """.format(sales_invoice_no),as_dict=1)    
    else:
        return frappe.db.sql("""SELECT sales_invoice,parent,invoice_amount,paying_amount FROM `tabReceipt Allocation` ra  join `tabSales Invoice` si ON si.name= ra.sales_invoice WHERE ra.sales_invoice = '{0}' AND parent!='{1}' AND (ra.docstatus= 1 or ra.docstatus=0) ORDER BY ra.sales_invoice """.format(sales_invoice_no,receipt_no),as_dict=1)