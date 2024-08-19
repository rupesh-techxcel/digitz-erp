# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AdvanceEntry(Document):
    def on_submit(self):

        project = frappe.get_doc("Project", self.project)

        project.advance_entry = self.name
        project.advance_amount = self.net_total
        project.save()

        default_advance_account = self.advance_account
        company = frappe.get_doc('Company', self.company)
        if(default_advance_account):
            # Determine the Debit and Credit accounts based on payment type
            payment_account = self.payment_account

            gl_posting_1 = frappe.new_doc("GL Posting")

            gl_posting_1.voucher_type = "Advance Entry"
            gl_posting_1.voucher_no = self.name
            gl_posting_1.posting_date = self.posting_date
            gl_posting_1.posting_time = self.posting_time
            gl_posting_1.account = payment_account
            gl_posting_1.debit_amount = self.net_total
            gl_posting_1.remarks = f"Advance received from {self.customer_name} for the project {self.project}"
          
            gl_posting_1.save()
            
            gl_posting_2 = frappe.new_doc("GL Posting")

            gl_posting_2.voucher_type = "Advance Entry"
            gl_posting_2.voucher_no = self.name
            gl_posting_2.posting_date = self.posting_date
            gl_posting_2.posting_time = self.posting_time
            gl_posting_2.account = default_advance_account
            gl_posting_2.credit_amount = self.net_total
            gl_posting_1.remarks = f"Advance received from {self.customer_name} for the project {self.project}"

            gl_posting_2.save()

            # frappe.msgprint("GL Posting's created successfully !")
        else:
            frappe.throw("Error: Please Set The Default Advance Account In Company Settings.")

