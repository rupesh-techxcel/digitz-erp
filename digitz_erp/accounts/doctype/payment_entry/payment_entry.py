# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class PaymentEntry(Document):
	pass



@frappe.whitelist()
def create_dr_supplier_entry(doc,supplier):
	pur_invoice = frappe.db.sql("""SELECT name,gross_total,supplier,rounded_total,paid_amount FROM `tabPurchase Invoice` WHERE supplier = '{}' AND docstatus = 1 AND rounded_total != paid_amount""".format(supplier),as_dict=1)

	new_doc = frappe.new_doc('Payment entry Details')
	for data in pur_invoice:
		print(data.get('rounded_total'),'--',data.get('paid_amount'))
		balance_amount = data.get('rounded_total') if data.get('paid_amount') == 0 else data.get('rounded_total') - data.get('paid_amount')

		new_doc.append("payment_allocation",{
					"paid_amount":data.get('gross_total'),
					"purchase":data.get('name'),
					"invoice_ammount":data.get('rounded_total'),
					"balance_ammount":balance_amount
					})
		new_doc.save()
	return new_doc.name



@frappe.whitelist()
def update_payment(child_table_data):
	data = json.loads(child_table_data)
	for allocation in data:
		print(allocation)
		doc = frappe.get_doc("Purchase Invoice", allocation.get('purchase'))
		paid_amount = doc.paid_amount + allocation.get('pay') or 0
		doc.paid_amount = paid_amount

		balance_amt = doc.rounded_total - doc.paid_amount
		doc.balance_ammount = balance_amt

		doc.save()



	
