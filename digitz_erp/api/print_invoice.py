import frappe

@frappe.whitelist(allow_guest=True)
def response(message, data, status_code):
    '''method to generates responses of an API
       args:
            message : response message string
            data : json object of the data
            status_code : status of the request'''
    frappe.clear_messages()
    frappe.local.response["message"] = message
    frappe.local.response["data"] = data
    frappe.local.response["http_status_code"] = status_code
    return

@frappe.whitelist(allow_guest=True)
def get_new_prints():
    '''API to get Invoices'''
    try:
        invoice_list = frappe.db.get_all('Sales Invoice', filters= {'print_in_progress': 1}, fields=['name', 'customer_name', 'pdf_url'])
        if invoice_list:
            return response('successfully get invoices', invoice_list, 200)
        else:
            return response('No Pending invoices', [], 400)
    except Exception as exception:
        frappe.log_error(frappe.get_traceback())
        return response(exception, {}, False, 400)

@frappe.whitelist(allow_guest=True)
def mark_print_done(invoice_no):
    '''API to get Invoices'''
    try:
        if frappe.db.exists('Sales Invoice', invoice_no):
            frappe.db.set_value('Sales Invoice', invoice_no, 'print_in_progress', 0)
            frappe.db.set_value('Sales Invoice', invoice_no, 'pdf_url', '')
            frappe.db.commit()
            return response('successfully updated invoice', {}, 200)
        else:
            return response('No invoices found!', {}, 400)
    except Exception as exception:
        frappe.log_error(frappe.get_traceback())
        return response(exception, {}, False, 400)
