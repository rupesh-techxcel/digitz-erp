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
        fields=['name', 'posting_date', 'total_completion_percentage']  # Include the fields you want
    )
    
    # Iterate through progress entries and fetch related proforma_invoice and progressive_sales_invoice
    for entry in progress_entries:
        # Retrieve the related proforma invoice using the 'progress_entry' field
        proforma_invoice = frappe.get_value('Proforma Invoice', {'progress_entry': entry['name']}, 'name')
        entry['proforma_invoice'] = proforma_invoice  # Add proforma_invoice to the result
        
        # Retrieve the related progressive sales invoice and net_total using the 'progress_entry' field
        progressive_sales_invoice, net_total = frappe.get_value('Progressive Sales Invoice', {'progress_entry': entry['name']}, ['name', 'net_total'])
        entry['progressive_sales_invoice'] = progressive_sales_invoice  # Add progressive_sales_invoice to the result
        entry['net_total'] = net_total  # Add net_total to the result
        
    return progress_entries