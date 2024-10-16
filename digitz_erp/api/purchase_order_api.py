import frappe
from datetime import datetime
from frappe.utils import getdate


@frappe.whitelist()
def check_invoices_for_purchase_order(purchase_order):
    
    pi_for_po = frappe.db.exists("Purchase Invoice", {"purchase_order": purchase_order})

    if pi_for_po:
        # Retrieve the Purchase Invoice document
        purchase_invoice = frappe.get_doc("Purchase Invoice", pi_for_po)

        # Check if the Purchase Invoice is not cancelled
        if purchase_invoice.docstatus != 2:  # In Frappe, docstatus 2 means cancelled
            return True
        else:
            #print("Invoice is cancelled.")
            return False
    else:
        #print("No Purchase Invoice found for this Purchase Order.")
        return False

# Before calling the below method it is supposed that the purchase order qty_purchased fiel 
# is already updated from purchase 
@frappe.whitelist()
def check_and_update_purchase_order_status(purchase_order_name):
    sql_query = """
    SELECT `name` FROM `tabPurchase Order Item`
    WHERE `parent` = %s
    """
    try:
        purchase_order_items = frappe.db.sql(sql_query, purchase_order_name, as_dict=True)
        
        purchased_any = False
        at_least_one_partial_purchase = False
        excess_allocation = False

        for po_item_dict in purchase_order_items:
            po_item_name = po_item_dict['name']
            po_item = frappe.get_doc("Purchase Order Item", po_item_name)
            
            if po_item.qty_purchased_in_base_unit and po_item.qty_purchased_in_base_unit > 0:
                purchased_any = True
                if po_item.qty_purchased_in_base_unit < po_item.qty_in_base_unit:
                    at_least_one_partial_purchase = True
                
                # Check for excess allocation
                if po_item.qty_purchased_in_base_unit > po_item.qty_in_base_unit:
                    excess_allocation = True                
                    
        if not purchased_any:
            frappe.db.set_value("Purchase Order", purchase_order_name, "order_status", "Pending")
        elif at_least_one_partial_purchase:
            frappe.db.set_value("Purchase Order", purchase_order_name, "order_status", "Partial")
        else:
            frappe.db.set_value("Purchase Order", purchase_order_name, "order_status", "Completed")
            
        if excess_allocation:
            frappe.msgprint(f"Warning: Purchase Order {purchase_order_name} contains one or more items with excess allocation.")
            #print("message shown and continues...")

    except Exception:
        raise  # This will re-raise the last exception


    
@frappe.whitelist()
def get_purchase_order_due_dates():

    data = []

    # Calculate the start and end dates for the current year
    
    current_year = datetime.now().year
    year_start_date = datetime(current_year, 1, 1)
    year_end_date = datetime(current_year, 12, 31)

    # Example query to fetch relevant data from Purchase Order with due dates in the current year
    purchase_orders = frappe.get_all(
        "Purchase Order",
        filters={
            "docstatus": 1,  # Filter for submitted Purchase Orders
            "due_date": [">=", year_start_date, "<=", year_end_date]
        },
        fields=["name", "due_date"],
    )

    for po in purchase_orders:
        data.append({
            "name": po.name,
            "due_date": getdate(po.due_date).strftime('%Y-%m-%d')  # Format the date as needed
        })

    return data

@frappe.whitelist()
def create_purchase_order_from_material_request(material_request):
    material_request_doc = frappe.get_doc("Material Request", material_request)

    # Create new Purchase Order document
    po = frappe.new_doc("Purchase Order")

    # Set basic fields from Material Request
    po.project = material_request_doc.project
    po.warehouse = material_request_doc.target_warehouse
    po.company = material_request_doc.company
    po.due_date = material_request_doc.schedule_date
    po.material_request = material_request_doc.name

    # Add items where approved_quantity > 0
    for item in material_request_doc.items:
        if item.approved_quantity > 0:
            po_item = po.append("items", {})
            po_item.item = item.item
            po_item.item_name = item.item_name
            po_item.display_name = item.description            
            po_item.qty = item.approved_quantity
            po_item.unit = item.unit
            po_item.warehouse = item.target_warehouse
            po_item.mr_item_reference = item.name

    # Return the unsaved document (as a dict) to the client
    return po.as_dict()
