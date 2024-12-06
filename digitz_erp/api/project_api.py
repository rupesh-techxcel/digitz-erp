import frappe

@frappe.whitelist()
def check_project_for_so(so_id):
    pro_for_so = frappe.db.exists("Project", {"sales_order": so_id})
        
    if pro_for_so:
        # Retrieve the Project document
        # project = frappe.get_doc("Project", pro_for_so)

        # Check if the Project is not cancelled
        # if project.docstatus != 2:  # In Frappe, docstatus 2 means cancelled
        #     return {
        #         'is_exits': True,
        #         'project_name':project_name
        #     }
        # else:
            #print("Invoice is cancelled.")
            # return {
            #     'is_exits': False,
            #     'project_name':project_name
            # }
        return {
                'is_exists': True,
                'project_name':""
            }
    else:
        #print("No Project found for this Purchase Order.")
        so = frappe.get_doc("Sales Order", so_id)
        quotation = frappe.get_doc("Quotation", so.quotation)
        project_name = ""
        if(quotation and quotation.custom_estimation_id):
            estimation = frappe.get_doc("Estimation", quotation.custom_estimation_id)
            project_name = estimation.project_name or ""
        return {
                'is_exists': False,
                'project_name':project_name
        }
        
@frappe.whitelist()
def get_progress_entries_by_project(project_name):
    """
    Fetch all progress entries where the project value matches the given project_name,
    along with the related proforma_invoice from the Proforma Invoice doctype and 
    progressive_sales_invoice from the Progressive Sales Invoice doctype.

    :param project_name: The name of the project to filter progress entries.
    :return: A list of dictionaries containing progress details (percentage, date, remarks, proforma_invoice, progressive_sales_invoice, net_total).
    """
    progress_entries = frappe.get_all(
        'Progress Entry',
        filters={'project': project_name},
        fields=['name', 'posting_date', 'total_completion_percentage', 'net_total']  # Include the fields you want
    )
    
    # Iterate through progress entries and fetch related proforma_invoice and progressive_sales_invoice
    for entry in progress_entries:
        # Retrieve the related proforma invoice using the 'progress_entry' field
        proforma_invoice = frappe.get_value('Proforma Invoice', {'progress_entry': entry['name']}, 'name')
        entry['proforma_invoice'] = proforma_invoice if proforma_invoice else None  # Add proforma_invoice to the result
        
        # Retrieve the related progressive sales invoice using the 'progress_entry' field
        progressive_sales_invoice = frappe.get_value('Progressive Sales Invoice', {'progress_entry': entry['name']}, 'name')
        entry['progressive_sales_invoice'] = progressive_sales_invoice if progressive_sales_invoice else None  # Add progressive_sales_invoice to the result

    print(progress_entries)
    return progress_entries

@frappe.whitelist()
def update_progress_entries_for_project(project_name):
    """
    Fetch progress entries for the given project and update the project's child table.
    """
    # Fetch the project document
    project_doc = frappe.get_doc("Project", project_name)

    # Clear the existing child table
    project_doc.set('project_stage_table', [])

    # Fetch progress entries related to the project
    progress_entries = frappe.get_all(
        'Progress Entry',
        filters={'project': project_name},
        fields=['name', 'posting_date', 'total_completion_percentage', 'net_total']  # Include the fields you want
    )

    progress_any = False
    # Iterate through progress entries and fetch related details
    for entry in progress_entries:
        # Retrieve the related Proforma Invoice
        proforma_invoice = frappe.get_value('Proforma Invoice', {'progress_entry': entry['name']}, 'name')

        # Retrieve the related Progressive Sales Invoice
        progressive_sales_invoice = frappe.get_value('Progressive Sales Invoice', {'progress_entry': entry['name']}, 'name')

        # Add the progress entry to the child table
        project_doc.append('project_stage_table', {
            'progress_entry': entry['name'],
            'proforma_invoice': proforma_invoice,
            'sales_invoice': progressive_sales_invoice,
            'posting_date': entry['posting_date'],
            'percentage_of_completion': entry['total_completion_percentage'],
            'net_total': entry['net_total']
        })
        progress_any = True
    
    if progress_any:
        frappe.msgprint("Progress entries successfully updated in the project.", alert=True)

    # Save the updated project document
    project_doc.save()

    return {"status": "success", "message": "Project stage table updated successfully."}


@frappe.whitelist()
def check_proforma_invoice(progress_entry):
    # Check if a Proforma Invoice already exists for this Progress Entry
    proforma_invoices = frappe.get_all('Proforma Invoice', filters={'progress_entry': progress_entry}, limit=1)

    if proforma_invoices:
        return True  # Proforma Invoice exists
    else:
        return False  # No Proforma Invoice exists
    
@frappe.whitelist()
def check_progressive_invoice(progress_entry):
    # Check if a Proforma Invoice already exists for this Progress Entry
    proforma_invoices = frappe.get_all('Progressive Sales Invoice', filters={'progress_entry': progress_entry}, limit=1)

    if proforma_invoices:
        return True  # Proforma Invoice exists
    else:
        return False  # No Proforma Invoice exists

@frappe.whitelist()
def get_last_progress_entry(project_name):
    # Query to get the last progress entry for the project, ordered by creation date
    last_progress_entry = frappe.db.get_value(
        'Progress Entry',  # Replace with the actual Progress Entry doctype name
        {'project': project_name},  # Filter by project name
        'name',  # Field to retrieve (the name of the entry)
        order_by='creation desc'  # Order by creation date in descending order
    )
    
    # Return the name of the last progress entry, or None if no entries found
    return last_progress_entry

@frappe.whitelist()
def get_sales_order_for_project(project_name):
    # Check if the project exists and fetch the linked sales order
    project = frappe.get_doc("Project", project_name)
    if project.sales_order:
        return {
            "status": "success",
            "sales_order": project.sales_order
        }
    else:
        return {
            "status": "failed",
            "message": "No Sales Order linked to the specified project."
        }

@frappe.whitelist()
def get_wip_closing_balance(project_name=None):
    # Fetch all accounts with account_type = 'Work In Progress'
    wip_accounts = frappe.get_all('Account', filters={'account_type': 'Work In Progress'}, fields=['name'])
    wip_account_names = [acc['name'] for acc in wip_accounts]

    if not wip_account_names:
        return 0  # No WIP accounts

    # Sum up debit and credit from GL Entry for these accounts and filter by project if provided
    query = """
        SELECT 
            SUM(debit_amount) AS total_debit, 
            SUM(credit_amount) AS total_credit
        FROM `tabGL Posting`
        WHERE account IN (%s)
    """ % ', '.join(['%s'] * len(wip_account_names))

    if project_name:
        query += " AND project = %s"
        values = tuple(wip_account_names) + (project_name,)
    else:
        values = tuple(wip_account_names)

    result = frappe.db.sql(query, values, as_dict=True)

    if result:
        total_debit = result[0].get('total_debit', 0) or 0
        total_credit = result[0].get('total_credit', 0) or 0
        closing_balance = total_debit - total_credit
        return closing_balance

    return 0

@frappe.whitelist()
def get_sales_order_value_for_project(project_name):
    # Check if the project exists and fetch the linked sales order
    project = frappe.get_doc("Project", project_name)
    if project.sales_order:
        # Fetch the Sales Order document
        sales_order = frappe.get_doc("Sales Order", project.sales_order)
        # Return only the rounded_total value
        return sales_order.rounded_total
    else:
        return 0  # Return 0 if no sales order is linked

@frappe.whitelist()
def get_billed_amount_for_project(project_name):
    # Fetch all Sales Invoices linked to the project
    sales_invoices = frappe.get_all(
        "Sales Invoice",
        filters={"project": project_name},
        fields=["rounded_total"]
    )

    # Fetch all Progressive Sales Invoices linked to the project
    progressive_sales_invoices = frappe.get_all(
        "Progressive Sales Invoice",
        filters={"project": project_name},
        fields=["rounded_total"]
    )

    # Sum up the rounded_total values from both Sales Invoices and Progressive Sales Invoices
    total = sum(invoice.rounded_total for invoice in sales_invoices) + \
            sum(invoice.rounded_total for invoice in progressive_sales_invoices)

    # Return the total
    return total
