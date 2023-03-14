# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
class PaymentEntry(Document):
	pass



@frappe.whitelist()
def create_dr_supplier_entry(doc):
	doc = json.loads(doc)
	payment_entry = doc.get("payment_entry_details")
	pur_invoice_lst = []
	for idx,row in enumerate(payment_entry):
		sup = row.get("supplier")

		pur_invoice = frappe.db.sql("""SELECT name,gross_total,supplier FROM `tabPurchase Invoice` WHERE supplier = '{}' AND docstatus = 0 """.format(sup),as_dict=1)

		for row in pur_invoice:
			pur_invoice_lst.append(row)


	return pur_invoice_lst