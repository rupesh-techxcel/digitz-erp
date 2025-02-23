import frappe
from frappe import _

@frappe.whitelist()
def merge_customer(current_customer, merge_customer):
    if not current_customer or not merge_customer:
        frappe.throw(_('Both customers must be specified'))

    # Fetch both customer docs
    current_customer_doc = frappe.get_doc('Customer', current_customer)
    merge_customer_doc = frappe.get_doc('Customer', merge_customer)

    # Start a transaction
    frappe.db.sql('START TRANSACTION')

    try:
        # Tables to update
        tables_to_update = {
            'tabSales Invoice': ['customer', 'customer_name'],
            'tabTab Sales': ['customer', 'customer_name'],
            'tabQuotation': ['customer', 'customer_name'],
            'tabDelivery Note': ['customer', 'customer_name'],
            'tabSales Order': ['customer', 'customer_name'],
            'tabReceipt Entry Detail': ['customer'],
            'tabReceipt Allocation': ['customer'],
            'tabCustomer Item': ['customer'],
        }

        # Update each table
        for table, fields in tables_to_update.items():
            for field in fields:
                
                #print(table)
                
                # Special handling for updating `customer_name` field
                new_value = merge_customer_doc.customer_name if field == 'customer_name' else merge_customer_doc.name
                frappe.db.sql(f"""
                    UPDATE `{table}`
                    SET `{field}` = %s
                    WHERE `{field}` = %s
                """, (new_value, current_customer_doc.name if field == 'customer' else current_customer_doc.customer_name))

        # Update the party column in `tabGL Posting` for party_type='Customer'
        frappe.db.sql("""
            UPDATE `tabGL Posting`
            SET `party` = %s
            WHERE `party` = %s AND `party_type` = 'Customer'
        """, (merge_customer_doc.name, current_customer_doc.name))

        # Delete the current customer
        frappe.delete_doc('Customer', current_customer)

        # Commit the transaction
        frappe.db.sql('COMMIT')

    except Exception as e:
        # Rollback the transaction in case of an error
        frappe.db.sql('ROLLBACK')
        frappe.throw(_('An error occurred while merging the customers: {0}').format(str(e)))

    return True

@frappe.whitelist()
def get_customer_details(customer):
    
    customer_doc = frappe.get_doc('Customer', customer)
    return customer_doc

    

