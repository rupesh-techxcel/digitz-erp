import frappe
from datetime import datetime
from frappe.utils import getdate


@frappe.whitelist()
def check_invoices_for_purchase_order(purchase_order):
    
    pi_for_po = frappe.db.exists("Purchase Invoice",{"purchase_order":purchase_order})
    
    if(pi_for_po):        
        return True    
    else:
        print("return False")
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

        for po_item_dict in purchase_order_items:
            po_item_name = po_item_dict['name']
            po_item = frappe.get_doc("Purchase Order Item", po_item_name)
            
            if po_item.qty_purchased and po_item.qty_purchased > 0:
                purchased_any = True
                if po_item.qty_purchased < po_item.qty:
                    at_least_one_partial_purchase = True
                    
        if not purchased_any:
            frappe.db.set_value("Purchase Order", purchase_order_name, "order_status", "Pending")
        elif at_least_one_partial_purchase:
            frappe.db.set_value("Purchase Order", purchase_order_name, "order_status", "Partial")
        else:
            frappe.db.set_value("Purchase Order", purchase_order_name, "order_status", "Completed")

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