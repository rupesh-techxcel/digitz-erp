import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_supplier_pending_invoices(supplier,reference_type):
    if reference_type == 'Purchase':
        values = frappe.db.sql("""SELECT supplier,name as invoice_no,supplier_inv_no,paid_amount,rounded_total as invoice_amount,rounded_total-paid_amount as balance_amount,rounded_total-paid_amount as paying_amount FROM `tabPurchase Invoice` WHERE supplier = '{supplier}' AND docstatus=1 AND credit_purchase = 1 AND rounded_total != paid_amount""".format(supplier= supplier),as_dict=1)
    elif reference_type == 'Expense':
        values = frappe.db.sql("""
        SELECT
            ed.supplier,
            ee.name as expense_no,
            ed.total as invoice_amount
            ed.total-paid_amount as balance_amount
        FROM
            `tabExpense Entry Details` ed
        INNER JOIN
            `tabExpense Entry` ee ON ed.parent = ee.name
        WHERE
            ed.supplier = '{supplier}' AND
            ee.credit_expense = 1
            (ee.docstatus = 1)
        """.format(supplier=supplier), as_dict=True)

@frappe.whitelist()
def get_allocations_for_invoice(purchase_invoice_no, payment_no):
    if(payment_no ==""):
        return frappe.db.sql("""SELECT purchase_invoice,parent,invoice_amount,paying_amount FROM `tabPayment Allocation` ra inner join `tabPurchase Invoice` si ON si.name= ra.purchase_invoice WHERE ra.purchase_invoice = '{0}' AND (ra.docstatus= 1 or ra.docstatus=0) ORDER BY ra.purchase_invoice """.format(purchase_invoice_no),as_dict=1)
    else:
        return frappe.db.sql("""SELECT purchase_invoice,parent,invoice_amount,paying_amount FROM `tabPayment Allocation` ra  join `tabPurchase Invoice` si ON si.name= ra.purchase_invoice WHERE ra.purchase_invoice = '{0}' AND parent!='{1}' AND (ra.docstatus= 1 or ra.docstatus=0) ORDER BY ra.purchase_invoice """.format(purchase_invoice_no,payment_no),as_dict=1)
    
@frappe.whitelist()
def check_balance_qty_to_return_for_purchase_invoice(purchase_invoice):
    print("check balance")
    result = frappe.db.sql("""
        SELECT name 
        FROM `tabPurchase Invoice Item` 
        WHERE qty_returned_in_base_unit < qty_in_base_unit
        AND parent = %s AND docstatus=1
    """, (purchase_invoice,))

    return bool(result)  # Return True if records are found, else False

@frappe.whitelist()
def get_purchase_invoices_for_return(supplier):
    
    result = frappe.db.sql("""
        SELECT distinct pi.name,pi.supplier,pi.posting_date,pi.rounded_total FROM `tabPurchase Invoice Item` pii inner join `tabPurchase Invoice` pi on pi.name=pii.parent where pii.qty_returned_in_base_unit < pii.qty_in_base_unit and  pi.supplier='{0}' and pi.docstatus=1 """.format(supplier), as_dict=1)
    
    return result

@frappe.whitelist()
def get_purchase_line_items_for_return(purchase_invoice):
    
    result = frappe.db.sql("""
                SELECT pi.name as pi_item_reference, pi.item, pi.item_name,pi.display_name, pi.unit,pi.base_unit, pi.rate * pi.conversion_factor as rate, (pi.qty_in_base_unit-pi.qty_returned_in_base_unit)/ pi.conversion_factor as qty, pi.rate_in_base_unit, pi.qty_in_base_unit,pi.conversion_factor, pi.tax, pi.tax_rate, rate_includes_tax from `tabPurchase Invoice Item` pi where pi.parent ='{0}' and pi.qty_in_base_unit> pi.qty_returned_in_base_unit order by idx""".format(purchase_invoice), as_dict =1
                )
    
    return result


