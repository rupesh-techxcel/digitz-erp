# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document


class ProformaInvoiceOLD(Document):
	pass


# @frappe.whitelist()
# def get_net_amount_of_stages(all_proforma_invoice_olds):
# 	net_total_list = []
# 	#print(all_proforma_invoice_olds)
# 	for i in range(0,len(all_proforma_invoice_olds)):
# 		#print(all_proforma_invoice_olds[0])
# 		net_total = frappe.db.get_value('Proforma Invoice', all_proforma_invoice_olds[0], 'net_total')
# 		#print(net_total)
# 		net_total_list.append(net_total)

# 	return net_total_list

@frappe.whitelist()
def get_net_amount_of_stages(all_proforma_invoice_olds):
    all_proforma_invoice_olds = frappe.parse_json(all_proforma_invoice_olds)
    net_total_list = []
    #print(all_proforma_invoice_olds)  # Ensure this prints the expected list of IDs

    for invoice_id in all_proforma_invoice_olds:
        net_total = frappe.db.get_value('Proforma Invoice', invoice_id, 'net_total')
        #print(net_total)
        net_total_list.append(net_total)
        
    return net_total_list



@frappe.whitelist()
def get_items(proforma_id):
    try:
        proforma_doc = frappe.get_doc("Proforma Invoice",proforma_id)

        if(proforma_doc):
            return proforma_doc
        else:
            return ""
    except:
        frappe.throw("Can't Get Data From Proforma Invoice.")