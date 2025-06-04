import frappe
from datetime import datetime
from frappe.utils import getdate
import csv
from frappe.utils import cint, flt

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
    po.default_cost_center = material_request_doc.default_cost_center
    po.warehouse = material_request_doc.target_warehouse
    po.company = material_request_doc.company
    po.due_date = material_request_doc.schedule_date
    po.material_request = material_request_doc.name
    po.use_dimensions = material_request_doc.use_dimensions
    po.use_dimensions_2 = material_request_doc.use_dimensions_2
   
    # Add items where approved_quantity > 0
    for item in material_request_doc.items:
        
        qty_approved = item.get('qty_approved', 0)
        
        # Ensure qty_purchased_in_base_unit is defined
        qty_purchased_in_base_unit = item.get('qty_purchased_in_base_unit', 0)  # Define or set default
        
        
        qty_approved_in_base_unit = qty_approved * item.conversion_factor  
        
        if qty_approved_in_base_unit > 0 and (qty_approved_in_base_unit - item.qty_purchased_in_base_unit)>0 :
            
            po_item = po.append("items", {})
            po_item.item = item.item
            po_item.item_name = item.item_name
            po_item.display_name = item.display_name  
            qty_approved_in_base_unit = item.qty_approved * item.conversion_factor          
            
            po_item.qty = qty_approved_in_base_unit - item.qty_purchased_in_base_unit
            po_item.width = item.width
            po_item.height = item.height
            po_item.no_of_pieces = item.no_of_pieces
            po_item.length = item.length
            po_item.weight_per_meter = item.weight_per_meter
            po_item.rate_per_kg = item.rate_per_kg
            
            print(po_item.weight_per_meter)
            print(po_item.rate_per_kg)
            
            po_item.unit = item.unit
            po_item.warehouse = item.target_warehouse
            po_item.mr_item_reference = item.name        

    frappe.msgprint("Select supplier for the purchase order and input rates in the line items.", alert=True)

    # Return the unsaved document (as a dict) to the client
    return po.as_dict()

@frappe.whitelist()
def check_pending_items_in_material_request(mr_no):
    
    mr_doc = frappe.get_doc("Material Request", mr_no)

    for item in mr_doc.items:
        
        qty_approved_in_base_unit = item.qty_approved * item.conversion_factor  
        if item.qty_purchased_in_base_unit < qty_approved_in_base_unit:
            return True

    return False

@frappe.whitelist()
def check_pending_items_in_purchase_order(po_no):
    
    mr_doc = frappe.get_doc("Purchase Order", po_no)

    for item in mr_doc.items:
          
        if item.qty_purchased_in_base_unit < item.qty_in_base_unit:
            return True

    return False

@frappe.whitelist()
def create_purchase_receipt_for_purchase_order(purchase_order):
    
    print("create_purchase_receipt_for_purchase_order")
    
    linked_invoices = frappe.db.exists(
        'Purchase Invoice', 
        {'purchase_order': purchase_order}
    )

    # If any invoice is found, raise an error
    if linked_invoices:
        frappe.throw(
            ("Cannot create Purchase Receipt because the Purchase Order {0} has already been used in a Purchase Invoice.").format(purchase_order),
            frappe.ValidationError
    )
    
    purchase_doc = frappe.get_doc("Purchase Order", purchase_order)

    # Create Purchase Receipt
    purchase_receipt = frappe.new_doc("Purchase Receipt")
    purchase_receipt.supplier = purchase_doc.supplier
    purchase_receipt.company = purchase_doc.company
    purchase_receipt.supplier_address = purchase_doc.supplier_address
    purchase_receipt.tax_id = purchase_doc.tax_id
    purchase_receipt.posting_date = purchase_doc.posting_date
    purchase_receipt.posting_time = purchase_doc.posting_time
    purchase_receipt.price_list = purchase_doc.price_list
    purchase_receipt.do_no = purchase_doc.do_no
    purchase_receipt.warehouse = purchase_doc.warehouse
    purchase_receipt.supplier_inv_no = purchase_doc.supplier_inv_no
    purchase_receipt.rate_includes_tax = purchase_doc.rate_includes_tax
    purchase_receipt.credit_purchase = purchase_doc.credit_purchase
    purchase_receipt.default_cost_center = purchase_doc.default_cost_center
    purchase_receipt.project = purchase_doc.project

    purchase_receipt.credit_days = purchase_doc.credit_days
    purchase_receipt.payment_terms = purchase_doc.payment_terms

    purchase_receipt.payment_mode = purchase_doc.payment_mode
    purchase_receipt.payment_account = purchase_doc.payment_account

    #print("check credit options")
    #print(purchase_doc.credit_purchase)
    #print(purchase_doc.payment_mode)
    #print(purchase_doc.payment_account)

    purchase_receipt.remarks = purchase_doc.remarks
    purchase_receipt.reference_no = purchase_doc.reference_no
    purchase_receipt.reference_date = purchase_doc.reference_date
    purchase_receipt.gross_total = purchase_doc.gross_total
    purchase_receipt.total_discount_in_line_items = purchase_doc.total_discount_in_line_items
    purchase_receipt.tax_total = purchase_doc.tax_total
    purchase_receipt.net_total = purchase_doc.net_total
    purchase_receipt.round_off = purchase_doc.round_off
    purchase_receipt.rounded_total = purchase_doc.rounded_total
    purchase_receipt.paid_amount = purchase_doc.paid_amount
    purchase_receipt.terms = purchase_doc.terms
    purchase_receipt.terms_and_conditions = purchase_doc.terms_and_conditions
    #print("purchase_order")
    #print(purchase_order)
    purchase_receipt.purchase_order = purchase_order
    purchase_receipt.use_dimensions = purchase_doc.use_dimensions

    pending_item_exists = False

    # Append items from Purchase Order to Purchase Receipt
    for item in purchase_doc.items:
        
        print("item.qty_in_base_unit")
        print(item.qty_in_base_unit)

        if(item.qty_in_base_unit - item.qty_purchased_in_base_unit>0):
            
            print("item")
            print(item)
            
            pending_item_exists = True
            invoice_item = frappe.new_doc("Purchase Receipt Item")
            invoice_item.item = item.item
            invoice_item.item_name = item.item_name
            invoice_item.display_name = item.display_name
            invoice_item.qty = round((item.qty_in_base_unit - item.qty_purchased_in_base_unit)/ item.conversion_factor,2)
            invoice_item.unit = item.unit
            invoice_item.rate = item.rate_in_base_unit * item.conversion_factor
            invoice_item.base_unit = item.base_unit
            invoice_item.qty_in_base_unit = item.qty_in_base_unit - item.qty_purchased_in_base_unit
            invoice_item.width = item.width
            invoice_item.height = item.height
            invoice_item.no_of_pieces = item.no_of_pieces  
            invoice_item.length = item.length
            invoice_item.weight_per_meter = item.weight_per_meter
            invoice_item.rate_per_kg = item.rate_per_kg
            invoice_item.rate_in_base_unit = item.rate_in_base_unit
            invoice_item.conversion_factor = item.conversion_factor
            invoice_item.rate_includes_tax = item.rate_includes_tax
            invoice_item.rate_excluded_tax = item.rate_excluded_tax
            invoice_item.warehouse = item.warehouse
            invoice_item.gross_amount = item.gross_amount
            invoice_item.tax_excluded = item.tax_excluded
            invoice_item.tax = item.tax
            invoice_item.tax_rate = item.tax_rate
            invoice_item.tax_amount = item.tax_amount
            invoice_item.discount_percentage = item.discount_percentage
            invoice_item.discount_amount = item.discount_amount
            invoice_item.net_amount = item.net_amount
            invoice_item.po_item_reference = item.name
            purchase_receipt.append("items", invoice_item)

    if pending_item_exists:		
        frappe.msgprint("Purchase Receipt generated successfully.", alert=True)
        return purchase_receipt.as_dict()
    else:
        frappe.msgprint("Purchase Receipt cannot be created because there are no pending items in the Purchase Order.")
        return "No Pending Items"

@frappe.whitelist()
def create_purchase_invoice_for_purchase_order(purchase_order):
    
    from frappe.utils import add_days
    
    linked_receipts = frappe.db.exists(
        'Purchase Receipt',
        {'purchase_order': purchase_order}
    )

    # If any Purchase Receipt is found, raise an error
    if linked_receipts:
        frappe.throw(
            ("Cannot create Purchase Invoice because the Purchase Order {0} has already been used in a Purchase Receipt.").format(purchase_order),
            frappe.ValidationError
        )

    purchase_doc = frappe.get_doc("Purchase Order", purchase_order)

    # Create Purchase Invoice
    purchase_invoice = frappe.new_doc("Purchase Invoice")
    purchase_invoice.supplier = purchase_doc.supplier
    purchase_invoice.company = purchase_doc.company
    purchase_invoice.project = purchase_doc.project
    purchase_invoice.default_cost_center = purchase_doc.default_cost_center
    purchase_invoice.supplier_address = purchase_doc.supplier_address
    purchase_invoice.tax_id = purchase_doc.tax_id
    purchase_invoice.posting_date = purchase_doc.posting_date
    purchase_invoice.posting_time = purchase_doc.posting_time
    purchase_invoice.price_list = purchase_doc.price_list
    purchase_invoice.do_no = purchase_doc.do_no
    purchase_invoice.warehouse = purchase_doc.warehouse
    purchase_invoice.supplier_inv_no = purchase_doc.supplier_inv_no
    purchase_invoice.rate_includes_tax = purchase_doc.rate_includes_tax
    purchase_invoice.credit_purchase = purchase_doc.credit_purchase


    purchase_invoice.credit_days = purchase_doc.credit_days
    purchase_invoice.payment_terms = purchase_doc.payment_terms

    purchase_invoice.payment_mode = purchase_doc.payment_mode
    purchase_invoice.payment_account = purchase_doc.payment_account

    #print("check credit options")
    #print(purchase_doc.credit_purchase)
    #print(purchase_doc.payment_mode)
    #print(purchase_doc.payment_account)

    purchase_invoice.remarks = purchase_doc.remarks
    purchase_invoice.reference_no = purchase_doc.reference_no
    purchase_invoice.reference_date = purchase_doc.reference_date
    purchase_invoice.gross_total = purchase_doc.gross_total
    purchase_invoice.total_discount_in_line_items = purchase_doc.total_discount_in_line_items
    purchase_invoice.tax_total = purchase_doc.tax_total
    purchase_invoice.net_total = purchase_doc.net_total
    purchase_invoice.round_off = purchase_doc.round_off
    purchase_invoice.rounded_total = purchase_doc.rounded_total
    purchase_invoice.paid_amount = purchase_doc.paid_amount
    purchase_invoice.terms = purchase_doc.terms
    purchase_invoice.terms_and_conditions = purchase_doc.terms_and_conditions
    #print("purchase_order")
    #print(purchase_order)
    purchase_invoice.purchase_order = purchase_order

    pending_item_exists = False

    # Append items from Purchase Order to Purchase Invoice
    for item in purchase_doc.items:

        if(item.qty_in_base_unit - item.qty_purchased_in_base_unit>0):
            pending_item_exists = True
            invoice_item = frappe.new_doc("Purchase Invoice Item")
            invoice_item.item = item.item
            invoice_item.item_name = item.item_name
            invoice_item.display_name = item.display_name
            invoice_item.qty = round((item.qty_in_base_unit - item.qty_purchased_in_base_unit)/ item.conversion_factor,2)
            invoice_item.unit = item.unit
            invoice_item.rate = item.rate_in_base_unit * item.conversion_factor
            invoice_item.base_unit = item.base_unit
            invoice_item.qty_in_base_unit = item.qty_in_base_unit - item.qty_purchased_in_base_unit
            invoice_item.rate_in_base_unit = item.rate_in_base_unit
            invoice_item.conversion_factor = item.conversion_factor
            invoice_item.rate_includes_tax = item.rate_includes_tax
            invoice_item.rate_excluded_tax = item.rate_excluded_tax
            invoice_item.warehouse = item.warehouse
            invoice_item.gross_amount = item.gross_amount
            invoice_item.tax_excluded = item.tax_excluded
            invoice_item.tax = item.tax
            invoice_item.tax_rate = item.tax_rate
            invoice_item.tax_amount = item.tax_amount
            invoice_item.discount_percentage = item.discount_percentage
            invoice_item.discount_amount = item.discount_amount
            invoice_item.net_amount = item.net_amount
            invoice_item.po_item_reference = item.name
            purchase_invoice.append("items", invoice_item)

     # === Embedded Payment Schedule Logic ===
    purchase_invoice.payment_schedule = []

    if purchase_invoice.credit_purchase:
        posting_date = purchase_invoice.posting_date
        credit_days = purchase_invoice.credit_days or 0
        rounded_total = purchase_invoice.rounded_total or 0

        payment_row = {
            "doctype": "Payment Schedule",
            "date": add_days(posting_date, credit_days) if credit_days else posting_date,
            "payment_mode": "Cash",
            "amount": rounded_total
        }
        purchase_invoice.payment_schedule.append(payment_row)
    else:
        purchase_invoice.payment_schedule = []

    if pending_item_exists:
        # purchase_invoice.insert()
        # frappe.db.commit()
        # frappe.msgprint("Purchase Invoice generated in draft mode", alert=True)
        return purchase_invoice.as_dict()
    else:
        frappe.msgprint("Purchase Invoice cannot be created because there are no pending items in the Purchase Order.")
        return "No Pending Items"

@frappe.whitelist()
def update_item_rate_per_kg(file_url):
    response = {"success": False, "message": "", "data": [], "errors": []}  # Structured response
    try:
        # Read the file content
        content = readfile(file_url)

        # Verify the uploaded file is a CSV file
        if not file_url.endswith('.csv'):
            response["message"] = "The uploaded file must be a CSV file."
            return response

        # Ensure content is a string
        if isinstance(content, bytes):
            content = content.decode('utf-8')  # Decode bytes to string

        # Parse the CSV content
        csv_reader = csv.DictReader(content.splitlines())

        # Verify the header contains required columns
        required_columns = {"item_code", "rate_per_kg"}
        if not required_columns.issubset(csv_reader.fieldnames):
            response["message"] = "The file must contain 'item_code' and 'rate_per_kg' columns."
            return response

        # Process each row and collect the data
        items = []
        errors = []
        for row in csv_reader:
            item_code = row.get("item_code")
            rate_per_kg = flt(row.get("rate_per_kg"))

            if not item_code or rate_per_kg <= 0:
                errors.append(f"Invalid data for item_code: {item_code}, rate_per_kg: {rate_per_kg}")
                continue

            items.append({"item_code": item_code, "rate_per_kg": rate_per_kg})

        response["data"] = items
        response["errors"] = errors

        if errors:
            response["message"] = "Some items have invalid data. See errors for details."
        else:
            response["message"] = "Items processed successfully."
        response["success"] = True

    except Exception as e:
        response["message"] = f"An error occurred: {str(e)}"
        frappe.log_error(message=str(e), title="Error in update_item_rate_per_kg")

    return response


def readfile(file_url):
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    return file_doc.get_content()

@frappe.whitelist()
def services_module_exists():
    exists = frappe.db.exists("Module Def", {"name": 'Digitz Services'})
    return bool(exists)

@frappe.whitelist()
def sub_contracting_order_exists(purchase_order):
    """
    Check if a Sub Contracting Order exists for the given Purchase Order.
    :param purchase_order: The Purchase Order ID to check.
    :return: Boolean value indicating existence.
    """
    if not purchase_order:
        frappe.throw("Purchase Order is required.")

    # Query for Sub Contracting Order linked to the Purchase Order
    exists = frappe.db.exists(
        "Sub Contracting Order",
        {"purchase_order": purchase_order}
    )

    # Return True if exists, else False
    return bool(exists)