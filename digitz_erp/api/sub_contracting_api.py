import frappe
from frappe.model.document import Document
from digitz_erp.api.items_api import get_item_valuation_rate

@frappe.whitelist()
def check_pending_items_for_stock_entry(material_issue):
    material_issue_doc = frappe.get_doc("Material Issue", material_issue)
    for item in material_issue_doc.items:
        if item.qty_finished < item.qty:
                return True  # Pending items found
    return False  # No pending items

@frappe.whitelist()
def check_pending_items_for_material_issue(sub_contracting_order):
    sub_contracting_order_doc = frappe.get_doc("Sub Contracting Order", sub_contracting_order)
    for item in sub_contracting_order_doc.items:
        if item.qty > item.qty_issued:
                return True  # Pending items found
    return False  # No pending items

@frappe.whitelist()
def create_material_issue(sub_contracting_order):
    
    if not sub_contracting_order:
        frappe.throw("Sub Contracting Order is required.")

    # Fetch the Sub Contracting Order document
    sco = frappe.get_doc("Sub Contracting Order", sub_contracting_order)

    # Check for items with qty > qty_issued (handling null values for qty_issued)
    items_to_issue = []
    for item in sco.items:
        if item.qty > (item.qty_issued or 0):  # Handle null values for qty_issued
            qty_to_issue = item.qty - (item.qty_issued or 0)  # Default to 0 if qty_issued is null
            
            # Fetch the rate using get_item_valuation_rate
            rate = get_item_valuation_rate(
                item.source_item,
                sco.posting_date,
                sco.posting_time
            )

            items_to_issue.append({
                "item": item.source_item,
                "item_name": item.source_item_name,
                "unit": item.source_item_unit,
                "base_unit": item.source_item_unit,
                "qty": qty_to_issue,
                "qty_in_base_unit": qty_to_issue,
                "qty_in_the_order": item.qty,
                "conversion_factor": 1,
                "sub_contracting_order_item": item.name,
                "rate": rate,  # Include the fetched rate
                "warehouse":sco.material_issue_warehouse
            })

    # Exit silently if no items require issuance
    if not items_to_issue:
        return None

    # Get the default work-in-progress account
    company = frappe.get_doc("Company", sco.company)
    default_wip_account = company.default_work_in_progress_account

    if not default_wip_account:
        frappe.throw("Default Work In Progress Account is not set in the Company settings.")

    # Create the Material Issue document (without inserting)
    material_issue = frappe.new_doc("Material Issue")
    material_issue.update({
        "items": items_to_issue,
        "remarks": f"Generated from Sub Contracting Order {sub_contracting_order}",
        "warehouse": sco.material_issue_warehouse,
        "company": sco.company,
        "project": sco.project,
        "purpose": "Sub Contracting",
        "sub_contracting_order": sub_contracting_order,
        "work_in_progress_account": default_wip_account,
    })

    # Return the document as JSON for UI population
    return material_issue.as_dict()


@frappe.whitelist()
def create_stock_entry(material_issue):
    # Fetch the Material Issue document
    mi_doc = frappe.get_doc('Material Issue', material_issue)

    sub_contracting_order = mi_doc.sub_contracting_order
    sc_doc = frappe.get_doc('Sub Contracting Order', sub_contracting_order)

    # Create a Stock Entry for returning the material
    stock_entry = frappe.new_doc('Stock Entry')
    stock_entry.purpose = 'Sub Contracting Material Receipt'
    stock_entry.sub_contracting_order = sub_contracting_order
    stock_entry.material_issue = material_issue
    stock_entry.warehouse = sc_doc.material_return_warehouse
    stock_entry.company = mi_doc.company
    stock_entry.project = mi_doc.project
    stock_entry.remarks = f"Stock Entry for Sub Contracting Order {sc_doc.name} and Material Issue {mi_doc.name}"

    # Loop through the items in the Material Issue
    for item in mi_doc.items:
        
        
        # Fetch the corresponding Sub Contracting Order Item using sub_contracting_order_item field
        subcontracting_item = frappe.get_doc('Sub Contracting Order Item', item.sub_contracting_order_item)


        qty_for_stock_entry = item.qty - (item.qty_finished or 0)
        
        print("qty_for_stock_entry")
        print(qty_for_stock_entry)

        # Check if qty_returned is less than qty_issued in the sub_contracting_order_item
        # Means if there is no qty available to return (or fully returned need not consider this)
        # But make sure that the qty returning is only up to the material issued from
        # Material Issue document passed in
        if qty_for_stock_entry > 0:

            stock_entry_item = {
                'item': subcontracting_item.target_item,
                'item_name': subcontracting_item.target_item_name,
                'qty': qty_for_stock_entry,
                'qty_issued':item.qty,
                'qty_in_the_order': subcontracting_item.qty,
                'rate': item.rate,
                'uom': subcontracting_item.target_item_unit,
                'warehouse':sc_doc.material_return_warehouse,
                'material_issue_item': item.name,
                'sub_contracting_order_item': item.sub_contracting_order_item                
            }

            # Append the item to Stock Entry
            stock_entry.append('items', stock_entry_item)

    # Insert the Stock Entry document and return its dictionary representation
    # stock_entry.insert()
    return stock_entry.as_dict()
