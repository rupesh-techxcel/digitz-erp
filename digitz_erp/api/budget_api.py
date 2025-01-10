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

@frappe.whitelist()
def get_items_from_estimate(project):
    if not project:
        frappe.throw("Project parameter is required")

    query = """
        SELECT            
            teiml.sub_item AS 'Item',
            SUM(teiml.quantity) AS 'Quantity',
            SUM(teiml.amount) / SUM(teiml.quantity) AS 'Rate',
            SUM(teiml.amount) AS 'Amount'
        FROM
            `tabEstimation Item Material And Labour` AS teiml
        INNER JOIN
            `tabEstimate` AS e ON e.name = teiml.parent
        WHERE
            teiml.type = 'Material'
            AND e.project_short_name = %s 
            AND e.docstatus = 1
            AND teiml.docstatus = 1
        GROUP BY
            teiml.sub_item
    """
    items = frappe.db.sql(query, project, as_dict=True)

    # Return an empty list if no items are found
    if not items:
        return []

    return items




