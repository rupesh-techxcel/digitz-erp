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

@frappe.whitelist()
def get_supplier_pending_documents(supplier,reference_type):
    if reference_type == 'Purchase Invoice':
        values = frappe.db.sql("""SELECT supplier,name as invoice_no,supplier_inv_no,paid_amount,rounded_total as invoice_amount,rounded_total-paid_amount as balance_amount FROM `tabPurchase Invoice` WHERE supplier = '{0}' AND docstatus=1 AND credit_purchase = 1 AND rounded_total != paid_amount""".format(supplier),as_dict=1)
        
        return values
        
    elif reference_type == 'Expense Entry':
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
        
        return values    

@frappe.whitelist()
def get_allocations_for_purchase_invoice(purchase_invoice_no, payment_no):
    if(payment_no ==""):
        return frappe.db.sql("""SELECT reference_name,parent,total_amount,paying_amount FROM `tabPayment Allocation` ra inner join `tabPurchase Invoice` si ON si.name= ra.reference_name WHERE ra.reference_type='Purchase Invoice' and ra.reference_name = '{0}' AND ra.docstatus= 1 ORDER BY ra.reference_name """.format(purchase_invoice_no),as_dict=1)
    else:
        # Note that the parent!{0} means it fetches the allocations for the invoice not in the current payment entry but from the other existing payment entries
        return frappe.db.sql("""SELECT reference_name,parent,total_amount,paying_amount FROM `tabPayment Allocation` ra  join `tabPurchase Invoice` si ON si.name= ra.reference_name WHERE ra.reference_type= 'Purchase Invoice' and ra.reference_name = '{0}' AND parent!='{1}' AND ra.docstatus= 1 ORDER BY ra.purchase_invoice """.format(purchase_invoice_no,payment_no),as_dict=1)

def get_allocations_for_expense(expense_doc_no, payment_no):
    if(payment_no ==""):
        return frappe.db.sql("""SELECT purchase_invoice,parent,invoice_amount,paying_amount FROM `tabPayment Allocation` ra inner join `tabPurchase Invoice` si ON si.name= ra.purchase_invoice WHERE ra.purchase_invoice = '{0}' AND (ra.docstatus= 1 or ra.docstatus=0) ORDER BY ra.purchase_invoice """.format(expense_doc_no),as_dict=1)
    else:
        return frappe.db.sql("""SELECT purchase_invoice,parent,invoice_amount,paying_amount FROM `tabPayment Allocation` ra  join `tabPurchase Invoice` si ON si.name= ra.purchase_invoice WHERE ra.purchase_invoice = '{0}' AND parent!='{1}' AND (ra.docstatus= 1 or ra.docstatus=0) ORDER BY ra.purchase_invoice """.format(expense_doc_no,payment_no),as_dict=1)
