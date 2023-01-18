
__version__ = '0.0.1'


import frappe


@frappe.whitelist()
def get_deliver_note_items(customer):
    dn_list = frappe.db.sql("""select dni.* from `tabDelivery Note` dn join `tabDelivery Note Item` dni on dni.parent=dn.name where dn.docstatus=1 and (dn.for_sales_invoice is NULL or dn.for_sales_invoice='') and (dn.against_sales_invoice is NULL or dn.against_sales_invoice='' and dn.customer='{}');""".format(customer), as_dict=True)
    for i in range(0, len(dn_list)):
        dn_list[i]["delivery_note"] = dn_list[i]["parent"]
        dn_list[i]["docstatus"] = 0
        dn_list[i]["parenttype"] = ""
        dn_list[i]["parentfield"] = ""
        dn_list[i]["parent"] = ""
        dn_list[i]["owner"] = ""
        dn_list[i]["creation"] = ""
        dn_list[i]["modified"] = ""
        dn_list[i]["modified_by"] = ""
        dn_list[i]["name"] = ""
        dn_list[i]["idx"] = i+1
    return dn_list
