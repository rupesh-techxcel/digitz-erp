import frappe
from datetime import datetime

def init_document_posting_status(document_type, document_name):
    
    posting_status_doc = frappe.new_doc('Document Posting Status')
    posting_status_doc.document_type = document_type
    posting_status_doc.document_name = document_name
    posting_status_doc.postings_start_time = datetime.now()
    posting_status_doc.posting_status = "Pending"
    posting_status_doc.insert()

def reset_document_posting_status_for_recalc_after_submit(document_type, document_name):
    doc_posting_status = frappe.get_doc("Document Posting Status",{'document_type':document_type,'document_name': document_name})
    doc_posting_status.posting_status = "Pending"
    doc_posting_status.stock_recalc_required_after_submit = True
    doc_posting_status.stock_recalc_after_submit_time = None
    doc_posting_status.save()     

def reset_document_posting_status_for_recalc_after_cancel(document_type, document_name):
    doc_posting_status = frappe.get_doc("Document Posting Status",{'document_type':document_type,'document_name': document_name})
    doc_posting_status.posting_status = "Pending"
    doc_posting_status.stock_recalc_required_after_cancel = True
    doc_posting_status.stock_recalc_after_cancel_time = None
    doc_posting_status.save()    

def update_posting_status(document_type,document_name, status, status_value=None):
    print("from API")
    
    doc_name = frappe.get_value("Document Posting Status",{'document_type':document_type,'document_name': document_name},['name'])
    
    if(not doc_name):
        # In case if a record not find, insert one, this is not likely to occur
        init_document_posting_status(document_type, document_name)
        
        doc_name = frappe.get_value("Document Posting Status",{'document_type':document_type,'document_name': document_name},['name'])
    
    # To update current time status_value passing as None
    if not status_value:
        frappe.set_value('Document Posting Status', doc_name, status,datetime.now())
        print("from API Done no status value")
    else:
        frappe.set_value('Document Posting Status', doc_name, status,status_value)
        print("from API Done with status value")
    
    
   


