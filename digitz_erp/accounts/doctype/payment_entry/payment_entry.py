# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class PaymentEntry(Document):
	def on_submit(self):
		for payment in self.payment_entry_details:
			if payment.get('payment_entry_details'):
				payment_entry_details = frappe.get_doc('Payment entry Details',payment.get('payment_entry_details'))
				for payment_allocation in payment_entry_details.get('payment_allocation'):
					purchase_invoice = frappe.get_doc("Purchase Invoice",payment_allocation.get('purchase'))	
					paid_amount = payment_allocation.get('paid_amount') + payment_allocation.get('pay')
					purchase_invoice.paid_amount = paid_amount
					balance_amount = purchase_invoice.rounded_total - purchase_invoice.paid_amount
					purchase_invoice.balance_ammount = balance_amount
					
					purchase_invoice.save()
				
				payment_entry_details.docstatus  = 1
				payment_entry_details.save(ignore_permissions=True)
				frappe.db.commit()


@frappe.whitelist()
def create_dr_supplier_entry(doc,supplier):
	pur_invoice = frappe.db.sql("""SELECT name,gross_total,supplier,rounded_total,paid_amount FROM `tabPurchase Invoice` WHERE supplier = '{}' AND docstatus = 1 AND rounded_total != paid_amount""".format(supplier),as_dict=1)

	if not pur_invoice:
		return 'No pending invoice'

	new_doc = frappe.new_doc('Payment entry Details')
	for data in pur_invoice:
		balance_amount = data.get('rounded_total') if data.get('paid_amount') == 0 else data.get('rounded_total') - data.get('paid_amount')

		new_doc.append("payment_allocation",{
					"paid_amount":data.get('paid_amount'),
					"purchase":data.get('name'),
					"invoice_ammount":data.get('rounded_total'),
					"balance_ammount":balance_amount
					})
		new_doc.save()
	return new_doc.name

@frappe.whitelist()
def update_payment(child_table_data,supplier):
	child_table_data = json.loads(child_table_data)
	totalPay = 0;

	for allocation in child_table_data:
		if allocation.get("pay")> allocation.get('balance_ammount'):
			frappe.throw(f"Cannot pay more than the balance amount.")

		frappe.db.sql(""" UPDATE `tabPayment Allocation` SET paid_amount = {0},invoice_ammount = {1},balance_ammount = {2},pay = {3} WHERE name = {4} """.format(allocation.get('paid_amount'),allocation.get('invoice_ammount'),allocation.get('balance_ammount'),allocation.get('pay'),allocation.get('name')))

		totalPay += allocation.get('pay');

	return totalPay


@frappe.whitelist()
def check_for_new_record(payment_entry_details,supplier):
	data = frappe.get_doc('Payment entry Details',payment_entry_details)

	new_record_check = frappe.db.sql("""SELECT name,gross_total,supplier,rounded_total,paid_amount FROM `tabPurchase Invoice` WHERE supplier = '{}' AND docstatus = 1 AND rounded_total != paid_amount""".format(supplier),as_dict=1)

	not_matching = []
	for name in new_record_check:
		found_match = False
		for purchase in data.get('payment_allocation'):
			if name.get('name') == purchase.get('purchase'):
				found_match = True
				break
		if not found_match:
			not_matching.append(name)

	if not_matching:
		doc = frappe.get_doc('Payment entry Details',payment_entry_details)
		for new_pi in not_matching:
			balance_amount = new_pi.get('rounded_total') if new_pi.get('paid_amount') == 0 else new_pi.get('rounded_total') - new_pi.get('paid_amount')

			doc.append('payment_allocation',{
						"paid_amount":new_pi.get('gross_total'),
						"purchase":new_pi.get('name'),
						"invoice_ammount":new_pi.get('rounded_total'),
						"balance_ammount":balance_amount
						})
	
			doc.save()



	
