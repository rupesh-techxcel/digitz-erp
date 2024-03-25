import frappe
from frappe.utils import get_datetime


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
        SELECT distinct si.name,si.customer,si.posting_date,si.rounded_total FROM `tabSales Invoice Item` sii inner join `tabSales Invoice` si on si.name=sii.parent where sii.qty_returned_in_base_unit < sii.qty_in_base_unit and  si.customer='{0}' and si.docstatus=1 """.format(customer), as_dict=1)
    
    return result

@frappe.whitelist()
def get_sales_line_items_for_return(sales_invoice):
    
    result = frappe.db.sql("""
                SELECT si.name as si_item_reference, si.item, si.item_name,si.display_name, si.unit,si.base_unit, si.rate * si.conversion_factor as rate, (si.qty_in_base_unit-si.qty_returned_in_base_unit)/si.conversion_factor as qty,si.qty_in_base_unit,si.conversion_factor, si.rate_in_base_unit, si.tax, si.tax_rate, rate_includes_tax from `tabSales Invoice Item` si where si.parent ='{0}' and si.qty_in_base_unit> si.qty_returned_in_base_unit order by si.parent,idx""".format(sales_invoice), as_dict =1
                )
    
    return result

@frappe.whitelist()
def get_pending_invoices_for_customer(customer):
    result = frappe.db.sql("""SELECT si.name as 'sales_invoice', si.posting_date as date, si.rounded_total as amount,si.paid_amount, si.rounded_total-si.paid_amount as balance_amount where si.customer='%s' and si.docstatus=1 and si.paid_amount< si.rounded_total""" .format(customer))
    return result


    
