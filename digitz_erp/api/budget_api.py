import frappe

@frappe.whitelist()
def item_query():
    
    print("from item_query")
    """Custom query to fetch Items."""
    return frappe.db.sql("""
        SELECT name AS value, item_name AS label
        FROM `tabItem`
        WHERE is_sales_item = 1
    """, as_dict=True)

@frappe.whitelist()
def item_group_query(*args, **kwargs):
    print("from item group query")
    
    """Custom query to fetch Item Groups."""
    data = frappe.db.sql("""
        SELECT item_group_name AS value, item_group_name AS label
        FROM `tabItem Group`        
    """, as_dict=True)
    
    return data
    
