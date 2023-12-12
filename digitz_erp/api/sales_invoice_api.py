import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_customer_pending_invoices(customer):

    values = frappe.db.sql("""SELECT customer,name as invoice_no,reference_no,paid_amount,rounded_total as invoice_amount,rounded_total-paid_amount as balance_amount FROM `tabSales Invoice` WHERE customer = '{}' AND (docstatus =0 or docstatus=1) AND credit_sale = 1 AND rounded_total > paid_amount""".format(customer),as_dict=1)      
    
    return {'values': values}

@frappe.whitelist()
def get_allocations_for_invoice(sales_invoice_no, receipt_no):    
    if(receipt_no ==""):        
        return frappe.db.sql("""SELECT sales_invoice,parent,invoice_amount,paying_amount FROM `tabReceipt Allocation` ra inner join `tabSales Invoice` si ON si.name= ra.sales_invoice WHERE ra.sales_invoice = '{0}' AND (ra.docstatus= 1 or ra.docstatus=0) ORDER BY ra.sales_invoice """.format(sales_invoice_no),as_dict=1)    
    else:
        return frappe.db.sql("""SELECT sales_invoice,parent,invoice_amount,paying_amount FROM `tabReceipt Allocation` ra  join `tabSales Invoice` si ON si.name= ra.sales_invoice WHERE ra.sales_invoice = '{0}' AND parent!='{1}' AND (ra.docstatus= 1 or ra.docstatus=0) ORDER BY ra.sales_invoice """.format(sales_invoice_no,receipt_no),as_dict=1)

@frappe.whitelist()
def submit_sales_invoice(docname):    
    doc = frappe.get_doc('Sales Invoice',docname)    
    doc.submit()
    
@frappe.whitelist()
def get_sales_invoices_for_return(customer):
    
    result = frappe.db.sql("""
        SELECT distinct si.name,si.customer,si.posting_date,si.rounded_total FROM `tabSales Invoice Item` sii inner join `tabSales Invoice` si on si.name=sii.parent where sii.qty_returned < sii.qty and  si.customer='{0}' and si.docstatus=1 """.format(customer), as_dict=1)
    
    return result

@frappe.whitelist()
def get_sales_line_items_for_return(sales_invoice):
    
    result = frappe.db.sql("""
                SELECT si.name as si_item_reference, si.item, si.item_name,si.display_name, si.unit,si.base_unit, si.rate, si.qty-si.qty_returned as qty, si.rate_in_base_unit, si.tax, si.tax_rate, rate_includes_tax from `tabSales Invoice Item` si where si.parent ='{0}' and si.qty> si.qty_returned""".format(sales_invoice), as_dict =1
                )
    
    return result
    
