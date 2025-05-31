import frappe
from frappe import _  # Ensure to import _ for translation if you're using it
from digitz_erp.accounts.doctype.gl_posting.gl_posting import get_party_balance
from frappe.utils import nowdate, nowtime

@frappe.whitelist()
def check_quotation_for_boq(boq_id):
    
    qot_for_boq = frappe.db.exists("Quotation", {"boq": boq_id})

    if qot_for_boq:
        # Retrieve the Quotation document
        # quotation = frappe.get_doc("Quotation", qot_for_boq)

        # Check if the Quotation is not cancelled
        # if quotation.docstatus != 2:  # In Frappe, docstatus 2 means cancelled
        return True
    else:
        return False
    
@frappe.whitelist()
def check_sales_order_for_boq(boq_id):
    
    sales_order_for_boq = frappe.db.exists("Sales Order", {"boq": boq_id})

    if sales_order_for_boq:       
        return True
    else:
        return False
    
@frappe.whitelist()
def check_boq_execution_for_boq(boq_id):
    boq_e = frappe.db.exists("BOQ Execution", {"boq": boq_id})

    if boq_e:
        # Retrieve the Quotation document
        # quotation = frappe.get_doc("Quotation", qot_for_boq)

        # Check if the Quotation is not cancelled
        # if quotation.docstatus != 2:  # In Frappe, docstatus 2 means cancelled
        return True
    else:
        return False

@frappe.whitelist()
def create_boq_execution_for_boq(boq_id):
    boq_e = frappe.new_doc("BOQ Execution")
    boq_e.boq = boq_id
    frappe.msgprint("The BOQ Execution has been generated successfully.", alert=True)
    return boq_e.as_dict()    


@frappe.whitelist()
def get_available_boqs(lead_from, customer=None, prospect=None):
    filters = {"docstatus": 1}  # Only fetch submitted BOQs (docstatus = 1)

    if lead_from == 'Customer' and customer:
        filters["customer"] = customer
    elif lead_from == 'Prospect' and prospect:
        filters["prospect"] = prospect
    else:
        frappe.throw(_("Invalid lead_from or missing customer/prospect"))

    # Fetch all BOQs matching the filters
    boqs = frappe.get_all("BOQ", filters=filters, fields=["name"])

    # Get all BOQs that are already assigned to an estimate
    assigned_boqs = frappe.get_all("Estimate", fields=["boq"], filters={"boq": ["!=", ""], "docstatus": ["!=", 2]})  # docstatus 2 means cancelled

    # Create a set of assigned BOQs
    assigned_boqs_set = set([boq.boq for boq in assigned_boqs])

    # Filter out BOQs that are assigned to estimates
    available_boqs = [boq for boq in boqs if boq.name not in assigned_boqs_set]

    return available_boqs

@frappe.whitelist()
def create_quotation(boq_id):
    boq_doc = frappe.get_doc("BOQ", boq_id)
    
    # Check if the BOQ is based on prospect and whether a customer exists for the prospect
    customer = None
    
    
      # Create Quotation
    quotation = frappe.new_doc("Quotation")
    quotation.boq = boq_id
    
    if boq_doc.lead_from == "Prospect":
        
        quotation.prospect = boq_doc.prospect
        
        # Check if the customer exists for the given prospect
        if not frappe.db.exists("Customer", {"prospect": boq_doc.prospect}): 
            quotation.prospect = boq_doc.prospect        
            quotation.lead_from = "Prospect"            
        else:            
            # Fetch the customer name based on the prospect
            customer = frappe.db.get_value("Customer", {"prospect": boq_doc.prospect}, "name")
            quotation.lead_from = "Customer"
            quotation.customer = customer

    else:
        customer = boq_doc.customer  
        quotation.lead_from = "Customer"

        # Fetch the customer document
        customer_doc = frappe.get_doc("Customer", customer)

        # Populate customer details in the Quotation
        quotation.customer = customer_doc.name
        quotation.customer_name = customer_doc.customer_name
        quotation.customer_display_name = customer_doc.customer_name

        # Fetch customer balance and other details
        customer_balance = get_party_balance("Customer", customer_doc.name)
        quotation.customer_balance = customer_balance or 0
        quotation.customer_address = customer_doc.full_address or ""
        quotation.tax_id = customer_doc.tax_id or ""
        quotation.salesman = customer_doc.salesman or ""

    # Get global defaults and set company
    global_defaults = frappe.get_doc("Global Settings")
    quotation.company = global_defaults.default_company

    company = frappe.get_doc("Company", quotation.company)
    quotation.warehouse = company.default_warehouse
    quotation.project_name = boq_doc.project_name
    quotation.project_short_name = boq_doc.project_short_name

    # Initialize totals
    gross_total = 0
    tax_total = 0
    net_total = 0

    # Append items from BOQ to Quotation
    for boq_item in boq_doc.boq_items:
        print(boq_item)
        item_doc = frappe.get_doc("Item", boq_item.item)
        print(item_doc)
        print(item_doc.base_unit)
        quotation_item = frappe.new_doc("Quotation Item")

        # Populate item details in the Quotation Item
        quotation_item.item = boq_item.item
        quotation_item.warehouse = company.default_warehouse
        quotation_item.item_name = boq_item.item_name
        quotation_item.display_name = boq_item.description
        quotation_item.item_group = boq_item.item_group
        quotation_item.unit = item_doc.base_unit
        quotation_item.qty = boq_item.quantity
        quotation_item.qty_in_base_unit = boq_item.quantity
        quotation_item.rate = boq_item.rate
        quotation_item.rate_in_base_unit = quotation_item.rate
        quotation_item.rate_excluded_tax = quotation_item.rate
        quotation_item.base_unit = item_doc.base_unit
        quotation_item.boq_item = boq_item.name

        # Tax handling
        quotation_item.tax = company.tax or ""
        quotation_item.tax_rate = 0

        if company.tax:
            tax_doc = frappe.get_doc("Tax", company.tax)
            quotation_item.tax_rate = tax_doc.tax_rate

        # Calculate gross, tax, and net amounts
        quotation_item.gross_amount = quotation_item.qty * quotation_item.rate_excluded_tax
        quotation_item.tax_amount = (quotation_item.gross_amount * quotation_item.tax_rate) / 100
        quotation_item.net_amount = quotation_item.gross_amount + quotation_item.tax_amount

        # Update totals
        gross_total += quotation_item.gross_amount
        tax_total += quotation_item.tax_amount
        net_total += quotation_item.net_amount
        rounded_total = round(net_total)
        

        quotation.append("items", quotation_item)
    
    # Set the total values in the Quotation
    quotation.gross_total = gross_total
    quotation.tax_total = tax_total
    quotation.net_total = net_total
    quotation.rounded_total = rounded_total 
    quotation.total_without_tax = gross_total
    quotation.rounded_total_without_tax = round(gross_total)
    frappe.msgprint(quotation.boq,alert=True)
    frappe.msgprint("The quotation has been initited successfully.", alert=True)
    return quotation.as_dict()

@frappe.whitelist()
def get_boq_details(boq):
    boq_data = frappe.get_doc("BOQ", boq)

    return {
        "project_name": boq_data.project_name,
        "project_short_name": boq_data.project_short_name,
        "use_custom_item_group_description": boq_data.use_custom_item_group_description,
        "item_groups": boq_data.item_groups,  # Ensure this is the correct field name
        "boq_items": boq_data.boq_items  # Ensure this is the correct field name
    }
    
@frappe.whitelist()
def get_boq_items(boq_name):
    """
    Fetch all items from the specified BOQ.
    
    Args:
        boq_name (str): The name of the BOQ.
    
    Returns:
        list: A list of dictionaries containing all BOQ items.
    """
    if not boq_name:
        frappe.throw("BOQ name is required.")
    
    # Fetch all items from the BOQ
    boq_items = frappe.get_all("BOQ Item", 
        filters={"parent": boq_name, "parentfield":"boq_items"},
        fields=["item", "description", "item_group", "item_group_description","quantity","unit"]
    )

    return boq_items if boq_items else []


@frappe.whitelist()
def update_sales_order_based_on_amendmends(boq):
    sales_order = frappe.get_doc("Sales Order",{"boq":boq})
    
    
@frappe.whitelist()
def copy_boq_items_to_original_boq_items(boq):
    boq_doc = frappe.get_doc('BOQ', boq)

    if len(boq_doc.original_boq_items) > 0:
        return  # If original_boq_items is not empty, do nothing

    for item in boq_doc.boq_items:
        new_row = boq_doc.append('original_boq_items', {})
        
        # Copy fields from boq_items to original_boq_items
        new_row.item = item.item
        new_row.description = item.description
        new_row.item_name = item.item_name
        new_row.item_group = item.item_group
        new_row.item_group_description = item.item_group_description
        new_row.quantity = item.quantity
        # new_row.area = item.area if item.area else None
        # new_row.perimeter = item.perimeter if item.perimeter else None
        new_row.unit = item.unit
        new_row.rate = item.rate
        new_row.gross_amount = item.gross_amount

    boq_doc.save(ignore_permissions=True)

    return {"status": "success", "message": "BOQ Items copied to Original BOQ Items."}

@frappe.whitelist()
def fetch_items_from_boq(boq_name):
    boq_doc = frappe.get_doc('BOQ', boq_name)

    items = []

    for item in boq_doc.boq_items:
        items.append({
            'item_code': item.item_code,
            'item_name': item.item_name,
            'description': item.description,
            'item_group': item.item_group,
            'item_group_description': item.item_group_description,
            'quantity': item.quantity,
            'rate': item.rate,
            'amount': item.amount,
            'unit':item.unit,
            'gross_amount': item.gross_amount,
            'net_amount': item.net_amount,
        })

    return items

@frappe.whitelist()
def get_project_for_boq(boq_name):
    """
    Fetch the Project associated with the Sales Order that includes the specified BOQ.
    
    Args:
        boq_name (str): The name or ID of the BOQ.
        
    Returns:
        dict: Project details linked to the Sales Order containing the specified BOQ, or an empty dictionary if no project is found.
    """
    if not boq_name:
        frappe.throw("BOQ name is required.")
    
    # Find the Sales Order that includes this BOQ
    sales_order_name = frappe.db.get_value("Sales Order", {"boq": boq_name}, "name")
    
    if not sales_order_name:
        frappe.msgprint(f"No Sales Order found with BOQ '{boq_name}'")
        return {}

    # Fetch the project associated with the found Sales Order
    project_name = frappe.db.get_value("Project", {"sales_order": sales_order_name}, "name")
    
    if project_name:
        # Optionally, retrieve more details about the project
        project = frappe.get_doc("Project", project_name)
        return {
            "name": project.name,
            "project_name": project.project_name,
            "status": project.status,
            "expected_start_date": project.expected_start_date,
            "expected_end_date": project.expected_end_date
        }
    else:
        frappe.msgprint(f"No Project found for Sales Order '{sales_order_name}' linked to BOQ '{boq_name}'")
        return {}    

@frappe.whitelist()
def start_boq_execution(boq_execution_name):
    """
    Update the status of the BOQ Execution to 'In Process',
    and set the start_date and start_time with current date and time.
    
    Args:
        work_order_name (str): The name of the BOQ Execution document.
    """
    if not boq_execution_name:
        frappe.throw("BOQ Execution name is required.")

    boq_execution = frappe.get_doc("BOQ Execution", boq_execution_name)
    
    if boq_execution.docstatus != 1:
        frappe.throw("Only submitted BOQ Execution documents can start execution.")
    
    if boq_execution.status != "Not Started":
        frappe.throw("Execution can only be started if status is 'Not Started'.")

    # Update the fields
    boq_execution.status = "In Process"   
    boq_execution.save()
    
    if boq_execution.boq:
        boq = frappe.get_doc("BOQ", boq_execution.boq)
        boq.execution_status = "In Process"
        boq.save()        
        frappe.msgprint("The execution status of the corresponding BOQ has also been updated to 'In Process'.", alert=True)

    return "success"

@frappe.whitelist()
def complete_boq_execution(boq_execution_name):
    """
    Update the status of the BOQ Execution to 'In Process',
    and set the start_date and start_time with current date and time.
    
    Args:
        work_order_name (str): The name of the BOQ Execution document.
    """
    if not boq_execution_name:
        frappe.throw("BOQ Execution name is required.")

    boq_execution = frappe.get_doc("BOQ Execution", boq_execution_name)
       
    if boq_execution.status != "In Process":
        frappe.throw("Execution can only be completed if status is 'In Process'.")

    # Update the fields
    boq_execution.status = "Completed"   
    boq_execution.save()
    
    if boq_execution.boq:
        boq = frappe.get_doc("BOQ", boq_execution.boq)
        boq.execution_status = "Completed"
        boq.save()
        frappe.msgprint("The execution status of the corresponding BOQ has also been updated to 'Completed'.", alert=True)

    return "success"

@frappe.whitelist()
def create_work_order(boq_execution_name):
    
    if not boq_execution_name:
        frappe.throw("BOQ Execution name is required.")

    # Fetch the BOQ Execution document
    boq_execution = frappe.get_doc("BOQ Execution", boq_execution_name)

    # Ensure the BOQ Execution is in the correct status
    if boq_execution.status != "In Process":
        frappe.throw("Work Order can only be created if BOQ Execution status is 'In Process'.")

    # Fetch items from boq_execution_items with balance_quantity > 0
    boq_items_with_balance = []
    
    for item in boq_execution.boq_execution_items:
        # Directly get the quantity in work orders from the boq_execution_item
        quantity_in_work_order = item.quantity_in_work_order
        
        # Calculate available balance quantity
        balance_quantity = item.quantity - quantity_in_work_order
        
        # Add item to list if there is a balance quantity
        if balance_quantity > 0:
            boq_items_with_balance.append({
                "doctype": "Work Order Item",  # Specify doctype to support sync with frappe.model.sync
                "item": item.item,
                "description": item.description,
                "quantity": balance_quantity,
                "item_group": item.item_group,
                "item_group_description": item.item_group_description,
                "unit": item.unit
            })
        print("Item:", item.item, "Balance Quantity:", balance_quantity)
    
    # If no items have balance_qty > 0, return a message
    if not boq_items_with_balance:
        frappe.throw("No items with balance quantity greater than zero available to create Work Order.")
 
    # Create a new Work Order using frappe.new_doc
    work_order = frappe.new_doc("Work Order")
    work_order.boq_execution = boq_execution_name  # Assign the BOQ Execution reference
    work_order.status = "Not Started"

    # Append items to work_order_items child table
    for item in boq_items_with_balance:
        work_order.append("work_order_items", item)

    # Return the new Work Order as dictionary without saving
    return work_order.as_dict()

@frappe.whitelist()
def start_work_order(work_order_name):
    """
    Update the status of the BOQ Execution to 'In Process',
    and set the start_date and start_time with current date and time.
    
    Args:
        work_order_name (str): The name of the BOQ Execution document.
    """
    if not work_order_name:
        frappe.throw("Work Order name is required.")

    work_order = frappe.get_doc("Work Order", work_order_name)
    
    if work_order.docstatus != 1:
        frappe.throw("Only submitted Work Order ocuments can start.")
    
    if work_order.status != "Not Started":
        frappe.throw("Execution can only be started if status is 'Not Started'.")

    # Update the fields
    work_order.status = "In Process"
    work_order.start_date = nowdate()
    work_order.start_time = nowtime()
    work_order.save()
    
    update_boq_execution_start_time(work_order.boq_execution)

    # Commit changes to the database
    frappe.db.commit()

    return "success"

@frappe.whitelist()
def update_boq_execution_start_time(boq_execution_name):

    # Check if the BOQ Execution document exists
    if not frappe.db.exists("BOQ Execution", boq_execution_name):
        print(f"BOQ Execution with name {boq_execution_name} does not exist.")
        return {"status": "failed", "message": f"BOQ Execution {boq_execution_name} not found"}

    # Check if there are any related "In Process" Work Orders for this BOQ Execution
    work_order_exists = frappe.db.exists(
        "Work Order",
        {
            "boq_execution": boq_execution_name,
            "docstatus": 1,
            "status": "In Process"
        }
    )

    if not work_order_exists:
        print("No 'In Process' Work Orders found linked to this BOQ Execution.")
        return {"status": "failed", "message": "No 'In Process' Work Orders found linked to the BOQ Execution"}

    try:
        # Fetch all related Work Orders with start_date and start_time set
        related_work_orders = frappe.get_all(
            "Work Order",
            filters={
                "boq_execution": boq_execution_name,
                "docstatus": 1,
                "status": "In Process"
            },
            fields=["start_date", "start_time"]
        )
        
        # Fetch the BOQ Execution document
        boq_execution_doc = frappe.get_doc("BOQ Execution", boq_execution_name)
        print(f"BOQ Execution doc fetched: {boq_execution_doc.name}")
        
        # Find the earliest start_date and start_time
        earliest_start_date = min([wo["start_date"] for wo in related_work_orders if wo["start_date"]])
        earliest_start_time = min(
            [wo["start_time"] for wo in related_work_orders if wo["start_date"] == earliest_start_date]
        )
        
        # Update BOQ Execution with the earliest start date and time
        boq_execution_doc.start_date = earliest_start_date
        boq_execution_doc.start_time = earliest_start_time
        boq_execution_doc.save()
        frappe.db.commit()
        print("Updated BOQ Execution with earliest start date and time.")
        
        return {"status": "success", "message": "BOQ Execution updated successfully"}

    except Exception as e:
        print("Error in update_boq_execution_start_time:", e)
        return {"status": "failed", "message": str(e)}

@frappe.whitelist()
def update_boq_execution_times(work_order_id):
    """
    Fetches the corresponding BOQ Execution for the given Work Order ID,
    and calls methods to update the start and end times.

    Args:
    work_order_id (str): The ID of the Work Order
    """
    print("Starting update_boq_execution_times")

    # Check if the Work Order exists
    if not frappe.db.exists("Work Order", work_order_id):
        print(f"Work Order with ID {work_order_id} does not exist.")
        return {"status": "failed", "message": f"Work Order {work_order_id} not found."}

    try:
        # Fetch the Work Order document
        work_order = frappe.get_doc("Work Order", work_order_id)

        # Check if the Work Order has a linked BOQ Execution
        if not work_order.boq_execution:
            print("No BOQ Execution linked to this Work Order.")
            return {"status": "failed", "message": "No BOQ Execution linked to this Work Order."}

        # Check if the linked BOQ Execution exists
        if not frappe.db.exists("BOQ Execution", work_order.boq_execution):
            print(f"BOQ Execution with name {work_order.boq_execution} does not exist.")
            return {"status": "failed", "message": f"BOQ Execution {work_order.boq_execution} not found."}

        # Fetch the corresponding BOQ Execution document
        boq_execution = frappe.get_doc("BOQ Execution", work_order.boq_execution)
        print(f"Fetched BOQ Execution: {boq_execution.name}")

        # Call methods to update start and end times on the BOQ Execution
        update_boq_execution_start_time(boq_execution.name)
        update_boq_execution_end_time(boq_execution.name)
        
        frappe.msgprint("BOQ Execution start and end times updated successfully.")
        return {"status": "success", "message": "BOQ Execution times updated successfully."}

    except Exception as e:
        print("Error in update_boq_execution_times:", e)
        frappe.log_error(f"Failed to update BOQ Execution times: {str(e)}", "BOQ Execution Update Error")
        return {"status": "failed", "message": "An error occurred while updating BOQ Execution times."}


@frappe.whitelist()
def update_boq_execution_end_time(boq_execution_name):
    print("Starting update_boq_execution_end_time")

    # Check if the BOQ Execution exists
    if not frappe.db.exists("BOQ Execution", boq_execution_name):
        print(f"BOQ Execution with name {boq_execution_name} does not exist.")
        return {"status": "failed", "message": f"BOQ Execution {boq_execution_name} not found."}

    try:
        # Fetch the BOQ Execution document
        boq_execution_doc = frappe.get_doc("BOQ Execution", boq_execution_name)
        print(f"Fetched BOQ Execution: {boq_execution_doc.name}")

        # Fetch all related Work Orders with end_date and end_time set
        related_work_orders = frappe.get_all(
            "Work Order",
            filters={"boq_execution": boq_execution_name, "docstatus": 1, "status": "Completed"},
            fields=["end_date", "end_time"]
        )
        
        print("related_work_orders",related_work_orders)

        # Ensure there are work orders with an end_date to check
        end_dates = [wo['end_date'] for wo in related_work_orders if wo['end_date']]
        if end_dates:
            # Find the latest end_date
            latest_end_date = max(end_dates)
            
            # Collect end_times only for work orders with the latest end_date
            end_times = [wo['end_time'] for wo in related_work_orders if wo['end_date'] == latest_end_date and wo['end_time']]
            if end_times:
                # Find the latest end_time for the latest end_date
                latest_end_time = max(end_times)
            else:
                latest_end_time = None  # Set as needed, if there's no end_time for the latest end_date

            # Update BOQ Execution with the latest end date and time
            boq_execution_doc.end_date = latest_end_date
            boq_execution_doc.end_time = latest_end_time
            boq_execution_doc.save()
            print("Updated BOQ Execution with latest end date and time.")
        else:
            print("No completed Work Orders found with end dates.")

        # Commit the transaction
        frappe.db.commit()
        
        return {"status": "success", "message": "BOQ Execution end date and time updated successfully."}

    except Exception as e:
        print("Error in update_boq_execution_end_time:", e)
        frappe.log_error(f"Failed to update BOQ Execution end time: {str(e)}", "BOQ Execution Update Error")
        return {"status": "failed", "message": "An error occurred while updating BOQ Execution end time."}

@frappe.whitelist()
def complete_work_order(work_order_name):
    # Fetch the Work Order document
    work_order = frappe.get_doc("Work Order", work_order_name)
    
    print("work_order")
    print(work_order)
    
    # Ensure the status is not already "Completed"
    if work_order.status != "Completed":
        # Set status to "Completed"
        work_order.status = "Completed"
        
        print("work order status")
        
        print("Before update boqexecution with quatity produced in work order")
        
        work_order.end_date = nowdate()
        work_order.end_time = nowtime()
        # Save changes to the Work Order
        work_order.save()
        frappe.db.commit()
        
        print("calling update_boq_execution_end_time from complete work order method")
        # Called only after change status
        update_boq_execution_end_time(work_order.boq_execution)
        # Commit changes to the database
        
        
         # Call the update method, after saving.The work order needs to be saved before calling this method because in boq_execution it check for the 'Completed' work orders.
        work_order.update_boq_execution_with_qty_produced_in_wo()

        return {"status": "success"}
    else:
        frappe.throw("Work Order is already completed.")

@frappe.whitelist()
def get_project_employees(project):
    return frappe.get_all("Project Employee", 
                          filters={"parent": project},
                          fields=["employee", "employee_name","per_hour_rate","designation","department"])

@frappe.whitelist()
def get_project_tasks(project):
    return frappe.get_all("Project Task", 
                          filters={"parent": project},
                          fields=["task", "task_name","task_description","expected_start_date","expected_end_date","actual_start_date","actual_end_date"])

    
@frappe.whitelist()
def get_boq_execution_employees(boq_execution_name):
    return frappe.get_all("Project Employee", 
                          filters={"parent": boq_execution_name},
                          fields=["employee", "employee_name","per_hour_rate","designation","department"])

@frappe.whitelist()
def get_boq_execution_tasks(boq_execution_name):
    return frappe.get_all("Project Task", 
                          filters={"parent": boq_execution_name},
                          fields=["task","task_name","task_description","expected_start_date", "expected_end_date","actual_start_date", "actual_end_date"])
    
@frappe.whitelist()
def create_timesheet_entry(work_order):

    work_order_doc = frappe.get_doc("Work Order",work_order)
    if work_order_doc:
        
        time_sheet = frappe.new_doc("Timesheet Entry")
        time_sheet.project = work_order_doc.project        
        time_sheet.work_order = work_order
        if(work_order_doc.boq_execution):
            time_sheet.boq_execution = work_order_doc.boq_execution
        if work_order_doc.boq:
            time_sheet.boq = work_order_doc.boq
        return time_sheet.as_dict()
    else:
        frappe.msgprint("No work_order found with the name %s",work_order)
        
@frappe.whitelist()
def get_project_details(project):
    # Fetch the project document to get the sales_order
    project_doc = frappe.get_doc('Project', project)
    
    if not project_doc.sales_order:
        return {'error': 'No Sales Order linked to the specified project.'}

    # Fetch the Sales Order document to get the BOQ
    sales_order_doc = frappe.get_doc('Sales Order', project_doc.sales_order)
    boq = sales_order_doc.boq  # Assuming 'boq' field holds the BOQ reference

    # Fetch the BOQ Execution associated with the BOQ
    boq_execution = frappe.db.get_value('BOQ Execution', {'boq': boq}, 'name') if boq else None

    # Return the results
    return {        
        'boq': boq,
        'boq_execution': boq_execution
    }

@frappe.whitelist()
def create_material_issue(work_order):

    work_order_doc = frappe.get_doc("Work Order",work_order)
    
    if work_order_doc:
        
        material_issue = frappe.new_doc("Material Issue")
        material_issue.project = work_order_doc.project        
        material_issue.work_order = work_order
        if(work_order_doc.boq_execution):
            material_issue.boq_execution = work_order_doc.boq_execution
        if work_order_doc.boq:
            material_issue.boq = work_order_doc.boq
        return material_issue.as_dict()
    else:
        frappe.msgprint("No work_order found with the name %s",work_order)

@frappe.whitelist()
def create_material_issue_from_project(work_order):

    project_doc = frappe.get_doc('Project', project)
    
    if not project_doc.sales_order:
        return {'error': 'No Sales Order linked to the specified project.'}

    # Fetch the Sales Order document to get the BOQ
    sales_order_doc = frappe.get_doc('Sales Order', project_doc.sales_order)
    boq = sales_order_doc.boq  # Assuming 'boq' field holds the BOQ reference

    # Fetch the BOQ Execution associated with the BOQ
    boq_execution = frappe.db.get_value('BOQ Execution', {'boq': boq}, 'name') if boq else None

    # Return the results
    return {        
        'boq': boq,
        'boq_execution': boq_execution
    }

@frappe.whitelist()
def create_estimate_from_boq(boq_name):
    # Fetch the BOQ document
    boq = frappe.get_doc("BOQ", boq_name)
    
    # Extract relevant fields from the BOQ document
    project_name = boq.project_name
    project_short_name = boq.project_short_name
    lead_from = boq.lead_from
    prospect = boq.prospect
    customer = boq.customer
    use_custom_item_group_description = boq.use_custom_item_group_description  # New field
    item_groups = boq.item_groups  # New field
    
    # Create the Estimate document but don't save it immediately
    estimate = frappe.new_doc("Estimate")
    estimate.boq = boq.name
    estimate.project_name = project_name
    estimate.project_short_name = project_short_name
    estimate.lead_from = lead_from
    estimate.prospect = prospect
    estimate.customer = customer
    estimate.use_custom_item_group_description = use_custom_item_group_description  # Set the custom field
    estimate.item_groups = item_groups  # Set the custom field
    
    # Get relevant child table fields from BOQ (e.g., item group or items)
    for item in boq.get("boq_items"):  # Adjust table name and fields as needed
        estimate.append("estimation_items", {
            "item": item.item,
            "description": item.description,
            "item_name": item.item_name,
            "item_group": item.item_group,
            "item_group_description": item.item_group_description,
            "quantity": item.quantity
        })
    
    return estimate.as_dict()

@frappe.whitelist()
def check_estimate_for_boq(boq_id):
    # Check if an Estimate is linked to this BOQ
    estimate = frappe.get_all("Estimate", filters={"boq": boq_id}, fields=["name"])
    return bool(estimate)

@frappe.whitelist()
def update_project_advance_amount(sales_order):
    try:
        # Step 1: Fetch the project linked to the sales order
        project = frappe.get_value("Project", {"sales_order": sales_order}, "name")
        
        if not project:
            frappe.msgprint(f"No project found linked to Sales Order {sales_order}. Skipping update.")
            return
        
        # Step 2: Check if the project has any progress entries
        progress_entry_exists = frappe.db.exists("Progress Entry", {"project": project})
        
        if progress_entry_exists:
            frappe.msgprint(f"Project {project} already has progress entries. Advance amount will not be updated.")
            return
        
        # Step 3: Fetch total allocated amount from Receipt Allocation
        total_advance = frappe.db.sql("""
            SELECT SUM(allocated_amount) AS total_advance
            FROM `tabReceipt Allocation`
            WHERE reference_type = 'Sales Order' AND reference_name = %s
        """, (sales_order,), as_dict=True)[0].get('total_advance', 0) or 0
        
        # Step 4: Update advance_amount in the project
        frappe.db.set_value("Project", project, "advance_amount", total_advance)
        
        frappe.msgprint(f"Successfully updated advance amount for Project {project}.")
    except Exception as e:
        frappe.log_error(message=str(e), title="Error in update_project_advance_amount")
        frappe.msgprint("An error occurred while updating the advance amount. Please check the error log.")

@frappe.whitelist()
def check_item_in_boq(boq_name, item_code):
    """
    Check if an item exists in the boq_items of a given BOQ.
    
    :param boq_name: Name of the BOQ to search in.
    :param item_code: Item code to check for existence.
    :return: Boolean indicating whether the item exists in the BOQ or not.
    """
    if not boq_name or not item_code:
        frappe.throw("Both BOQ name and Item code are required.")

    # Query the BOQ child table for the item
    exists = frappe.db.exists(
        "BOQ Item",  # Replace with your actual child table name if different
        {
            "parent": boq_name,  # BOQ name (link to parent)
            "item": item_code     # Field in the child table
        }
    )

    return bool(exists)