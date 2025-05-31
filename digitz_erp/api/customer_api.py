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

@frappe.whitelist()
def convert_prospect_to_customer(prospect):
    # Check if the prospect already exists as the prospect field in any customer
    existing_customer = frappe.db.exists("Customer", {"prospect": prospect})
    if existing_customer:
        frappe.throw(f"The prospect {prospect} is already linked to a customer.")
    
    # Get the Prospect document
    prospect_doc = frappe.get_doc("Sales Prospect", prospect)
    
    # Create a new Customer document but do not insert (save) it yet
    customer_doc = frappe.new_doc("Customer")
    
    # Assign relevant fields from the prospect to the customer
    customer_doc.customer_name = prospect_doc.company_name if prospect_doc.company_name else prospect_doc.prospect_name
    
    customer_doc.prospect = prospect
    customer_doc.contact_person = prospect_doc.contact_person
    customer_doc.contact_person_designation = prospect_doc.contact_person_designation
    customer_doc.phone = prospect_doc.phone
    customer_doc.mobile_no = prospect_doc.mobile_no
    customer_doc.email_id = prospect_doc.email_id
    
    customer_doc.address_line_1 = prospect_doc.address_line_1
    customer_doc.address_line_2 = prospect_doc.address_line_2
    customer_doc.emirate = prospect_doc.emirate
    customer_doc.area = prospect_doc.area
    customer_doc.country = prospect_doc.country
    
    customer_doc.full_address = prospect_doc.full_address    
    
    # Return the new customer document to be opened in the UI
    return customer_doc.as_dict()

    

