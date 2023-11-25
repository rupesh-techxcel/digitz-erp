import frappe
from frappe.utils import get_datetime

# Get supplier documents pending for allocation
@frappe.whitelist()
def get_supplier_pending_documents(supplier,reference_type, payment_no=""):    

    if reference_type == 'Purchase Invoice':
   
        # Purchase Invoice Query , only consider committed purchases and expenses but payment allocations with draft and committed statuses.
        documents_query = """
            SELECT
                supplier,
                'Purchase Invoice' as reference_type,
                name as reference_name,
                posting_date as date,
                supplier_inv_no,
                paid_amount,
                rounded_total as invoice_amount,
                rounded_total - paid_amount as balance_amount
            FROM
                `tabPurchase Invoice`
            WHERE
                supplier = '{0}'
                AND docstatus = 1 
                AND credit_purchase = 1
                AND rounded_total > paid_amount
        """.format(supplier)

        # Additional Query for Payment Allocation (if payment_no is not None)
        payment_allocation_values = []
        if payment_no != "":
            payment_allocation_query = """
                SELECT
                    pi.supplier,
                    pi.name as reference_name,  
                    'Purchase Invoice' as reference_type,                  
                    pi.posting_date as date,
                    pi.supplier_inv_no,
                    pi.paid_amount,
                    pi.rounded_total as invoice_amount,
                    pi.rounded_total - pi.paid_amount as balance_amount
                FROM
                    `tabPurchase Invoice` pi
                JOIN
                    `tabPayment Allocation` pa ON pi.name = pa.reference_name and pa.reference_type='Purchase Invoice'
                WHERE
                    pi.supplier = '{0}'
                    AND pi.docstatus = 1
                    AND pi.credit_purchase = 1                   
                    AND pa.parent = '{1}' 
                    AND (pa.docstatus = 0 or pa.docstatus = 1)
            """.format(supplier, payment_no)

            # Execute Additional Query
            payment_allocation_values = frappe.db.sql(payment_allocation_query, as_dict=1)
            print("payment_allocation_values")
            print(payment_allocation_values)

        # Execute Purchase Invoice Query
        documents_values = frappe.db.sql(documents_query, as_dict=1)
        print("expense values")
        print(documents_values)
        if payment_allocation_values !=[]:        
            documents_values = [invoice for invoice in documents_values if invoice['reference_name'] not in [pa['reference_name'] for pa in payment_allocation_values]]

            # Combine Results
            combined_values = documents_values + payment_allocation_values
            return combined_values

    elif reference_type == 'Expense Entry':
        print("Get documents for expense entry")
        # Purchase Invoice Query
        documents_query = """
            SELECT
                ed.supplier,
                ed.parent as document_no,
                ed.name as reference_name, 
                'Expense Entry' as reference_type,
                ed.expense_date as date,
                ed.supplier_inv_no,
                ed.paid_amount,
                ed.total as invoice_amount,
                ed.total - ed.paid_amount as balance_amount
            FROM
                `tabExpense Entry Details` ed
                INNER JOIN `tabExpense Entry` e on e.name= ed.parent
            WHERE
                supplier = '{0}'
                AND e.docstatus = 1
                AND e.credit_expense = 1
                AND ed.total > ed.paid_amount                
        """.format(supplier)
        
         # Execute Purchase Invoice Query
        documents_values = frappe.db.sql(documents_query, as_dict=1)
        print("expense_values")
        print(documents_values)

        # Additional Query for Payment Allocation (if payment_no is not None)
        payment_allocation_values = []
        if payment_no!="":
            payment_allocation_query = """
                SELECT
                    ed.supplier,
                    ed.parent as document_no,
                    ed.name as reference_name, 
                    'Expense Entry' as reference_type,
                    ed.expense_date as date,
                    ed.supplier_inv_no,
                    ed.paid_amount,
                    ed.total as invoice_amount,
                    ed.total - ed.paid_amount as balance_amount
                FROM
                    `tabExpense Entry Details` ed
                JOIN
                    `tabPayment Allocation` pa ON ed.name = pa.reference_name and pa.reference_type='Expense Entry'
                    WHERE
                        ed.supplier = '{0}'
                        AND ed.docstatus = 1
                        AND ed.credit_expense = 1                   
                        AND pa.parent = '{1}'
                        AND (pa.docstatus = 0 OR pa.docstatus =1)
                """.format(supplier, payment_no)

            # Execute Additional Query
            payment_allocation_values = frappe.db.sql(payment_allocation_query, as_dict=1)
            print("payment_allocation_values")
            print(payment_allocation_values)       
        
        if payment_allocation_values !=[]:   
            documents_values = [invoice for invoice in documents_values if invoice['reference_name'] not in [pa['reference_name'] for pa in payment_allocation_values]]
            # Combine Results
            combined_values = documents_values + payment_allocation_values

            return combined_values
        else:
            return documents_values
        

# Get all supplier other payment allocations which is still pending, to reconcile with the payment entry allocations to refresh the balances and pending of each documents. This calls in the stage 1 (as per the comment in the payment entry) of the loading of pending payments.
# Eg: Suppose the purchase invoice has total amount 1000 and 500 alocated in a payment entry. To create a new payment entry it requires to check the existing payment entires (other than the current payment entry) to get the actual balance of the invoice ie, 500 in the example. Here also only pending allocations are considering because if it is fully paid , in the initial call (with get_supplier_pending_documents) it only fetch pending documents and comparing only those documents
@frappe.whitelist()
def get_all_supplier_pending_payment_allocations_with_other_payments(supplier, reference_type, payment_no):
    
    
    # if payment_no=="":
   
        
    #     if reference_type == 'Purchase Invoice':
    #         values = frappe.db.sql("""SELECT pa.reference_name,pa.parent as payment_no,pi.rounded_total as invoice_amount,pa.paying_amount FROM `tabPayment Allocation` pa inner join `tabPurchase Invoice` pi ON pi.name= pa.reference_name and pa.reference_type='Purchase Invoice' WHERE pa.supplier = '{0}' AND  pi.docstatus=1 AND (pa.docstatus= 1 or pa.docstatus=0) AND (pi.paid_amount<pi.rounded_total) ORDER BY pa.reference_name """.format(supplier),as_dict=1)
    #         return {'values': values}
    #     elif reference_type == "Expense Entry":
    #         values = frappe.db.sql("""SELECT pa.reference_name,pa.parent as  payment_no,ee.total as invoice_amount,pa.paying_amount FROM `tabPayment Allocation` pa inner join  `tabExpense Entry Details` ee ON ee.name= pa.reference_name and pa.reference_type='Expense Entry' WHERE pa.supplier = '{0}' AND ee.docstatus=1 AND (pa.docstatus= 1 or pa.docstatus=0) AND (ee.paid_amount<ee.total) ORDER BY pa.reference_name """.format(supplier),as_dict=1)
    #         return {'values': values}
    # else:
         #     # In case payment_no="" fetching records with paid_amount< rounded_total is fine because it is only required to fetch allocations for pending payments because it is calling against the result of get_supplier_pending_documents. Also in get_supplier_pending_documents if payment_no="" only pending documents are fetching. 
         
        # In case payment_no has value it is not ideal to fetch paid_amount<rounded_total because even for fully paid documents when user click on the allocation button it should show the documents which are already allocated in the payment entry. 
        
        # Both the above conditions are satisfied in the query
        
        # But note that it fetches allocations belongs to other payments only.
        
        if reference_type == 'Purchase Invoice':
            values = frappe.db.sql("""SELECT distinct pa.reference_name,pa.parent as payment_no,pi.rounded_total as invoice_amount,pa.paying_amount FROM `tabPayment Allocation` pa inner join `tabPurchase Invoice` pi ON pi.name= pa.reference_name and pa.reference_type='Purchase Invoice' WHERE pa.supplier = '{0}' AND pa.parent!='{1}' AND pi.docstatus=1 AND (pa.docstatus= 1 or pa.docstatus=0) AND ((pi.paid_amount<pi.rounded_total) or pi.name in (select distinct reference_name from `tabPayment Allocation` where reference_type='Purchase Invoice' and parent='{1}')) ORDER BY pa.reference_name """.format(supplier, payment_no),as_dict=1)            
            
            return {'values': values}
        elif reference_type == "Expense Entry":
            print("values-expenses-allocations")
            values = frappe.db.sql("""SELECT distinct pa.reference_name,pa.parent as  payment_no,ee.total as invoice_amount,pa.paying_amount FROM `tabPayment Allocation` pa inner join  `tabExpense Entry Details` ee ON ee.name= pa.reference_name and pa.reference_type='Expense Entry Details' WHERE pa.supplier = '{0}' AND pa.parent!='{1}' AND (pa.docstatus= 1 or pa.docstatus=0) AND ee.docstatus=1 AND ((ee.paid_amount<ee.total) or ee.name in (select distinct reference_name from `tabPayment Allocation` where reference_type='Expense Entry' and parent='{1}')) ORDER BY pa.reference_name """.format(supplier, payment_no),as_dict=1)
            
            print(values)
            return {'values': values}        
    
@frappe.whitelist()
def get_allocations_for_purchase_invoice(purchase_invoice_no, payment_no):
    if(payment_no ==""):
        return frappe.db.sql("""SELECT pa.reference_name,pa.parent as payment_no,pi.rounded_total as invoice_amount,pa.paying_amount FROM `tabPayment Allocation` pa inner join `tabPurchase Invoice` pi ON pi.name= pa.reference_name AND pa.reference_type='Purchase Invoice' WHERE pa.reference_name = '{0}' AND (pa.docstatus= 1 or pa.docstatus = 0) AND pi.docstatus=1 ORDER BY pa.reference_name """.format(purchase_invoice_no),as_dict=1)
    else:
        # Note that the parent!{0} means it fetches the allocations for the invoice not in the current payment entry but from the other existing payment entries
        
        return frappe.db.sql("""SELECT pa.reference_name,pa.parent as payment_no,pi.rounded_total as invoice_amount,pa.paying_amount FROM `tabPayment Allocation` pa inner join `tabPurchase Invoice` pi ON pi.name= pa.reference_name AND pa.reference_type='Purchase Invoice' WHERE pa.reference_name = '{0}' AND pa.parent!='{1}' AND (pa.docstatus= 1 or pa.docstatus = 0) AND pi.docstatus=1 ORDER BY pa.reference_name """.format(purchase_invoice_no, payment_no),as_dict=1)

@frappe.whitelist()
def get_allocations_for_expense_entry(expense_detail_name, payment_no):
    if(payment_no ==""):
        return frappe.db.sql("""SELECT pa.reference_name,pa.parent as payment_no,ee.total as invoice_amount,pa.paying_amount FROM `tabPayment Allocation` pa inner join `tabExpense Entry Details` ee ON ee.name= pa.reference_name AND pa.reference_type='Expense Entry Details' WHERE pa.reference_name = '{0}' AND (pa.docstatus= 1 or pa.docstatus = 0) AND ee.docstatus=1 ORDER BY pa.reference_name """.format(expense_detail_name),as_dict=1)
    else:
        # Note that the parent!{0} means it fetches the allocations for the invoice not in the current payment entry but from the other existing payment entries
        
        return frappe.db.sql("""SELECT pa.reference_name,pa.parent as payment_no,ee.total as invoice_amount,pa.paying_amount FROM `tabPayment Allocation` pa inner join `tabExpense Entry Details` ee ON ee.name= pa.reference_name AND pa.reference_type='Expense Entry Details' WHERE pa.reference_name = '{0}' AND pa.parent!='{1}' AND (pa.docstatus= 1 or pa.docstatus = 0) AND ee.docstatus =1 ORDER BY pa.reference_name """.format(expense_detail_name, payment_no),as_dict=1)    
    