# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import *
from frappe.utils import *
from datetime import datetime

class PeriodClosingVoucher(Document):
	pass

	def on_submit(self):
		frappe.enqueue(self.insert_gl_records, queue="long")

	def insert_gl_records(self):
		idx = 1
		if(self.total_debit > self.total_credit):
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Period Closing Voucher'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.posting_date
			gl_doc.account = self.closing_account_head
			gl_doc.credit_amount = self.amount
			gl_doc.remarks = self.remarks;
			gl_doc.insert()
		elif(self.total_debit < self.total_credit):
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Period Closing Voucher'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = self.posting_date
			gl_doc.account = self.closing_account_head
			gl_doc.debit_amount = self.amount
			gl_doc.remarks = self.remarks;
			gl_doc.insert()


@frappe.whitelist()
def get_account_balance(account):
    today = datetime.today().date()
    query = """
        SELECT
            SUM(debit_amount) - SUM(credit_amount) AS account_balance
        FROM
            `tabGL Posting`
        WHERE
            posting_date <= %s
            AND account = %s
    """
    data = frappe.db.sql(query, (today, account), as_dict=True)
    account_balance = data[0].get('account_balance') if data and data[0].get('account_balance') else 0
    print(account_balance)
    return account_balance
