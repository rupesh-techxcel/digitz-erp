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


