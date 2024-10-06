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