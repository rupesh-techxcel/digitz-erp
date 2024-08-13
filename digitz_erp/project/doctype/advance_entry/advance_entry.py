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
            gl_posting_1.remarks = "Debit Amount Added !"

            gl_posting_1.save()

            
            gl_posting_2 = frappe.new_doc("GL Posting")

            gl_posting_2.voucher_type = "Advance Entry"
            gl_posting_2.voucher_no = self.name
            gl_posting_2.posting_date = self.posting_date
            gl_posting_2.posting_time = self.posting_time
            gl_posting_2.account = default_advance_account
            gl_posting_2.credit_amount = self.net_total
            gl_posting_2.remarks = "Credit Amount Added !"

            gl_posting_2.save()

            # frappe.msgprint("GL Posting's created successfully !")
        else:
            frappe.throw("Error: Please Set The Default Advance Account In Company Settings.")






        # # Fetch the company and accounts
        # # company = frappe.get_doc('Company', self.company)
        # # default_advance_account = company.default_advance_received_account
        # default_advance_account = self.advance_account

        # # Determine the Debit and Credit accounts based on payment type
        # # if self.payment_type == 'Cash':
        # #     payment_account = company.default_cash_account
        # # elif self.payment_type == 'Bank':
        # #     payment_account = company.default_bank_account
        # # else:
        # #     payment_account = self.payment_account

        # # Create a new Journal Entry document
        # journal_entry = frappe.new_doc("Journal Entry")
        # # journal_entry.voucher_type = 'Journal Entry'
        # # journal_entry.company = self.company
        # journal_entry.posting_date = self.posting_date
        # journal_entry.posting_time = self.posting_time

        

        # # Add Journal Entry accounts
        # # Credit the default advance received account
        # journal_entry.append("journal_entry_details", {
        #     "account": default_advance_account,
        #     "narration":"credit amt added",
        #     # "credit_in_account_currency": self.net_total,
        #     "credit": self.net_total,
        #     # "is_advance": "Yes"
        # })

        # # Debit the payment account
        # journal_entry.append("journal_entry_details", {
        #     "account": self.payment_account,
        #     "narration":"debit amt added",
        #     # "debit_in_account_currency": self.net_total,
        #     "debit": self.net_total
        # })

        # journal_entry.remarks = "Created From The Advance Entry"

        # # for row in journal_entry.journal_entry_details:
        # #     total_debit += row.debit
        # #     total_credit += row.credit

        # journal_entry.total_credit = self.net_total
        # journal_entry.total_debit = self.net_total
        

        # # Save and submit the Journal Entry
        # journal_entry.insert()
        # frappe.db.commit()
        # journal_entry.submit()

        #  # Check if the Journal Entry is submitted
        # if journal_entry.docstatus == 1:
        #     # Update the balance in the default advance account
        #     customer_advances = frappe.get_doc('Account', default_advance_account)
        #     customer_advances.balance += self.net_total
        #     customer_advances.save()

        # frappe.msgprint("Journal Entry created successfully with ID: {}".format(journal_entry.name))
