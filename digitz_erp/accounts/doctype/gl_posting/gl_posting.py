# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class GLPosting(Document):
	pass

@frappe.whitelist()
def get_party_balance(party_type, party):
	if frappe.db.exists(party_type, party):
		if party_type == 'Customer':
			balance = get_voucher_balance('Sales Invoice', party)
		if party_type == 'Supplier':
			balance = get_voucher_balance('Purchase Invoice', party)
		return balance
	else:
		frappe.throw("{0} : {1} does not exist".format(party_type, party))

@frappe.whitelist()
def get_voucher_balance(voucher_type, party):
	balance = 0
	if voucher_type == "Sales Invoice":
		data =  frappe.db.sql("""
			SELECT
				SUM(si.rounded_total - IFNULL(si.paid_amount, 0)) AS balance_amount
			FROM
				`tabSales Invoice` si
			WHERE
				si.customer = '{0}' AND
				si.docstatus = 1
		""".format(party), as_dict=True)
		if data:
			if data[0].get('balance_amount'):
				balance = data[0].get('balance_amount')

	if voucher_type == "Purchase Invoice":
		data =  frappe.db.sql("""
			SELECT
				SUM(pi.rounded_total - IFNULL(pi.paid_amount, 0)) AS balance_amount
			FROM
				`tabPurchase Invoice` pi
			WHERE
				pi.supplier = '{0}' AND
				pi.docstatus = 1
		""".format(party), as_dict=True)
		if data:
			if data[0].get('balance_amount'):
				balance = data[0].get('balance_amount')
	return balance
