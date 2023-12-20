import frappe

@frappe.whitelist()
def do_dolphin_postings_job():
    print("hello from dolphin print job")
    
    

    