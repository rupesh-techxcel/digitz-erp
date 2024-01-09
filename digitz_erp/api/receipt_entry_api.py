import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_customer_pending_documents(customer, reference_type, receipt_no):


    print("customer")
    print(customer)

    print("reference_type")    
    print(reference_type)
    
    print("receipt_no")
    print(receipt_no)
    
    if reference_type == 'Sales Invoice':
   
        # Sales Invoice Query , only consider committed sales invoices but for payment allocations with draft and committed statuses.
        
        # Get all pending receipts for the customer
        documents_query = """
            SELECT
                customer,
                'Sales Invoice' as reference_type,
                (CASE WHEN reference_no IS NOT NULL THEN CONCAT(name, ', Ref:', reference_no) ELSE reference_no END) as reference_name, 
                posting_date as date,               
                paid_amount,
                rounded_total as invoice_amount,
                rounded_total - paid_amount as balance_amount
            FROM
                `tabSales Invoice`
            WHERE
                customer = '{0}'
                AND docstatus = 1 
                AND credit_sale = 1
                AND rounded_total > paid_amount
        """.format(customer)

        # Additional Query for Receipt Allocation (if receipt_no is not None)
        receipt_allocation_values = []
        if receipt_no != "":
             # receipt_allocation_query to include the existing allocations for this receipt, irrespective of qty is pending
            receipt_allocation_query = """
                SELECT
                    si.customer,
                    (case when reference_no is not null then si.name + ' , ' + reference_no else si.name  end) as reference_name,  
                    'Sales Invoice' as reference_type,                  
                    si.posting_date as date,                    
                    si.paid_amount,
                    si.rounded_total as invoice_amount,
                    si.rounded_total - si.paid_amount as balance_amount
                FROM
                    `tabSales Invoice` si
                JOIN
                    `tabReceipt Allocation` ra ON si.name = ra.reference_name and ra.reference_type='Sales Invoice'
                WHERE
                    si.customer = '{0}'
                    AND si.docstatus = 1
                    AND si.credit_sale = 1                   
                    AND ra.parent = '{1}' 
                    AND (ra.docstatus = 0 or ra.docstatus = 1)
            """.format(customer, receipt_no)

            receipt_allocation_values = frappe.db.sql(receipt_allocation_query, as_dict=1)
            print("receipt allocation values")
            print(receipt_allocation_values)

        documents_values = frappe.db.sql(documents_query, as_dict=1)
        print("documents_values")
        print(documents_values)
               
        if receipt_allocation_values !=[]:   
            #  Avoid duplicates before combine
            documents_values = [invoice for invoice in documents_values if invoice['reference_name'] not in [ra['reference_name'] for ra in receipt_allocation_values]]

            # Combine Results
            combined_values = documents_values + receipt_allocation_values
            return combined_values
        else:
            return documents_values
        
# Get all supplier other payment allocations which is still pending, to reconcile with the payment entry allocations to refresh the balances and pending of each documents. This calls in the stage 1 (as per the comment in the payment entry) of the loading of pending payments.
# Eg: Suppose the purchase invoice has total amount 1000 and 500 alocated in a payment entry. To create a new payment entry it requires to check the existing payment entires (other than the current payment entry) to get the actual balance of the invoice ie, 500 in the example. Here also only pending allocations are considering because if it is fully paid , in the initial call (with get_supplier_pending_documents) it only fetch pending documents and comparing only those documents
@frappe.whitelist()
def get_all_customer_pending_receipt_allocations_with_other_receipts(customer, reference_type, receipt_no):

    if reference_type == 'Sales Invoice':
        values = frappe.db.sql("""SELECT distinct ra.reference_name,ra.parent as receipt_no,si.rounded_total as invoice_amount,ra.paying_amount FROM `tabReceipt Allocation` ra inner join `tabSales Invoice` si ON si.name= ra.reference_name and ra.reference_type='Sales Invoice' WHERE ra.customer = '{0}' AND ra.parent!='{1}' AND si.docstatus=1 AND (ra.docstatus= 1 or ra.docstatus=0) AND ((si.paid_amount<si.rounded_total) or si.name in (select distinct reference_name from `tabReceipt Allocation` where reference_type='Sales Invoice' and parent='{1}')) ORDER BY ra.reference_name """.format(customer, receipt_no),as_dict=1)            
        
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