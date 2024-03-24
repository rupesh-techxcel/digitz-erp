import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_customer_pending_documents(customer, reference_type, receipt_no):
    base_query = """
        SELECT
            customer,
            '{reference_type}' as reference_type,
            name as reference_name,
            CONCAT(COALESCE(reference_no, ''), ' ', DATE_FORMAT(posting_date, '%Y-%m-%d')) as reference_no,
            posting_date,
            paid_amount,
            rounded_total as invoice_amount,
            rounded_total - paid_amount as balance_amount
        FROM
            `tab{document_type}`
        WHERE
            customer = %s
            AND docstatus = 1
            AND {credit_condition} = 1
            AND rounded_total > paid_amount
    """

    queries = []
    if reference_type in ['Sales Invoice', 'All']:
        queries.append(base_query.format(reference_type='Sales Invoice', document_type='Sales Invoice', credit_condition='credit_sale'))
    if reference_type in ['Sales Return', 'All']:
        queries.append(base_query.format(reference_type='Sales Return', document_type='Sales Return', credit_condition='credit_sale'))
    if reference_type in ['Credit Note', 'All']:
        queries.append(base_query.replace('rounded_total', 'grand_total').format(reference_type='Credit Note', document_type='Credit Note', credit_condition='on_credit'))

    documents_query = " UNION ALL ".join(queries)
    documents_values = frappe.db.sql(documents_query, (customer,), as_dict=1)

    # Handling receipt allocation
    receipt_allocation_values = []
    if receipt_no:
        receipt_allocation_query = """
            SELECT
                ra.customer,
                ra.name as reference_name,
                ra.reference_type,
                ra.reference_no,
                ra.posting_date,
                ra.paid_amount,
                ra.invoice_amount,
                ra.balance_amount
            FROM
                `tabReceipt Allocation` ra
            WHERE
                ra.customer = %s
                AND ra.parent = %s
                AND (ra.docstatus = 0 or ra.docstatus = 1)
                AND ra.reference_type IN (%s)
        """
        reference_types = ['Sales Invoice', 'Sales Return', 'Credit Note'] if reference_type == 'All' else [reference_type]
        receipt_allocation_values = frappe.db.sql(receipt_allocation_query, (customer, receipt_no, tuple(reference_types)), as_dict=1)

    if receipt_allocation_values:
        documents_values = [doc for doc in documents_values if doc['reference_name'] not in {ra['reference_name'] for ra in receipt_allocation_values}]
        combined_values = documents_values + receipt_allocation_values
        return combined_values

    return documents_values

# Get all supplier other payment allocations which is still pending, to reconcile with the payment entry allocations to refresh the balances and pending of each documents. This calls in the stage 1 (as per the comment in the payment entry) of the loading of pending payments.
# Eg: Suppose the purchase invoice has total amount 1000 and 500 alocated in a payment entry. To create a new payment entry it requires to check the existing payment entires (other than the current payment entry) to get the actual balance of the invoice ie, 500 in the example. Here also only pending allocations are considering because if it is fully paid , in the initial call (with get_supplier_pending_documents) it only fetch pending documents and comparing only those documents
@frappe.whitelist()
def get_all_customer_pending_receipt_allocations_with_other_receipts(customer, reference_type, receipt_no):

    if reference_type == 'Sales Invoice':
        values = frappe.db.sql("""SELECT distinct ra.reference_name,ra.parent as receipt_no,si.rounded_total as invoice_amount,ra.paying_amount FROM `tabReceipt Allocation` ra inner join `tabSales Invoice` si ON si.name= ra.reference_name and ra.reference_type='Sales Invoice' WHERE ra.customer = '{0}' AND ra.parent!='{1}' AND si.docstatus=1 AND (ra.docstatus= 1 or ra.docstatus=0) AND ((si.paid_amount<si.rounded_total) or si.name in (select distinct reference_name from `tabReceipt Allocation` where reference_type='Sales Invoice' and parent='{1}')) ORDER BY ra.reference_name """.format(customer, receipt_no),as_dict=1)
        return {'values': values}

    elif reference_type == 'Sales Return':
        values = frappe.db.sql("""SELECT distinct ra.reference_name,ra.parent as receipt_no,sr.rounded_total as invoice_amount,ra.paying_amount FROM `tabReceipt Allocation` ra inner join `tabSales Return` sr ON sr.name= ra.reference_name and ra.reference_type='Sales Return' WHERE ra.customer = '{0}' AND ra.parent!='{1}' AND sr.docstatus=1 AND (ra.docstatus= 1 or ra.docstatus=0) AND ((sr.paid_amount<sr.rounded_total) or sr.name in (select distinct reference_name from `tabReceipt Allocation` where reference_type='Sales Return' and parent='{1}')) ORDER BY ra.reference_name """.format(customer, receipt_no),as_dict=1)
        return {'values': values}

    elif reference_type == 'Credit Note':
        values = frappe.db.sql("""SELECT distinct ra.reference_name,ra.parent as receipt_no,cn.grand_total as invoice_amount,ra.paying_amount FROM `tabReceipt Allocation` ra inner join `tabCredit Note` cn ON cn.name= ra.reference_name and ra.reference_type='Credit Note' WHERE ra.customer = '{0}' AND ra.parent!='{1}' AND cn.docstatus=1 AND (ra.docstatus= 1 or ra.docstatus=0) AND (cn.name in (select distinct reference_name from `tabReceipt Allocation` where reference_type='Credit Note' and parent='{1}')) ORDER BY ra.reference_name """.format(customer, receipt_no),as_dict=1)
        return {'values': values}


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

@frappe.whitelist()
def get_allocations_for_sales_invoice(sales_invoice_no, receipt_no):
    if(receipt_no ==""):
        return frappe.db.sql("""SELECT ra.reference_name,ra.parent as receipt_no,si.rounded_total as invoice_amount,ra.paying_amount FROM `tabReceipt Allocation` ra inner join `tabSales Invoice` si ON si.name= ra.reference_name AND ra.reference_type='Sales Invoice' WHERE ra.reference_name = '{0}' AND (ra.docstatus= 1 or ra.docstatus = 0) AND si.docstatus=1 ORDER BY ra.reference_name """.format(sales_invoice_no),as_dict=1)
    else:
        # Note that the parent!{0} means it fetches the allocations for the invoice not in the current payment entry but from the other existing payment entries

        return frappe.db.sql("""SELECT ra.reference_name,ra.parent as receipt_no,si.rounded_total as invoice_amount,ra.paying_amount FROM `tabReceipt Allocation` ra inner join `tabSales Invoice` si ON si.name= ra.reference_name AND ra.reference_type='Sales Invoice' WHERE ra.reference_name = '{0}' AND ra.parent!='{1}' AND (ra.docstatus= 1 or ra.docstatus = 0) AND si.docstatus=1 ORDER BY ra.reference_name """.format(sales_invoice_no, receipt_no),as_dict=1)

@frappe.whitelist()
def get_allocations_for_sales_return(sales_invoice_no, receipt_no):
    if(receipt_no ==""):
        return frappe.db.sql("""SELECT ra.reference_name,ra.parent as receipt_no,sr.rounded_total as invoice_amount,ra.paying_amount FROM `tabReceipt Allocation` ra inner join `tabSales Return` sr ON sr.name= ra.reference_name AND ra.reference_type='Sales Return' WHERE ra.reference_name = '{0}' AND (ra.docstatus= 1 or ra.docstatus = 0) AND sr.docstatus=1 ORDER BY ra.reference_name """.format(sales_invoice_no),as_dict=1)
    else:
        return frappe.db.sql("""SELECT ra.reference_name,ra.parent as receipt_no,sr.rounded_total as invoice_amount,ra.paying_amount FROM `tabReceipt Allocation` ra inner join `tabSales Return` sr ON sr.name= ra.reference_name AND ra.reference_type='Sales Return' WHERE ra.reference_name = '{0}' AND ra.parent!='{1}' AND (ra.docstatus= 1 or ra.docstatus = 0) AND sr.docstatus=1 ORDER BY ra.reference_name """.format(sales_invoice_no, receipt_no),as_dict=1)

@frappe.whitelist()
def get_allocations_for_credit_note(credit_note_no, receipt_no):
    if(receipt_no ==""):
        return frappe.db.sql("""SELECT ra.reference_name,ra.parent as receipt_no,cn.grand_total as invoice_amount,ra.paying_amount FROM `tabReceipt Allocation` ra inner join `tabCredit Note` cn ON cn.name= ra.reference_name AND ra.reference_type='Credit Note' WHERE ra.reference_name = '{0}' AND (ra.docstatus= 1 or ra.docstatus = 0) AND cn.docstatus=1 ORDER BY ra.reference_name """.format(credit_note_no),as_dict=1)
    else:
        return frappe.db.sql("""SELECT ra.reference_name,ra.parent as receipt_no,cn.grand_total as invoice_amount,ra.paying_amount FROM `tabReceipt Allocation` ra inner join `tabCredit Note` cn ON cn.name= ra.reference_name AND ra.reference_type='Credit Note' WHERE ra.reference_name = '{0}' AND ra.parent!='{1}' AND (ra.docstatus= 1 or ra.docstatus = 0) AND cn.docstatus=1 ORDER BY ra.reference_name """.format(credit_note_no, receipt_no),as_dict=1)
