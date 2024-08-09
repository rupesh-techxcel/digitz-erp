# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AdvanceEntry(Document):
    def on_submit(self):
        # Fetch the company and accounts
        # company = frappe.get_doc('Company', self.company)
        # default_advance_account = company.default_advance_received_account
        default_advance_account = self.advance_account

        # Determine the Debit and Credit accounts based on payment type
        # if self.payment_type == 'Cash':
        #     payment_account = company.default_cash_account
        # elif self.payment_type == 'Bank':
        #     payment_account = company.default_bank_account
        # else:
        #     payment_account = self.payment_account

        # Create a new Journal Entry document
        journal_entry = frappe.new_doc("Journal Entry")
        # journal_entry.voucher_type = 'Journal Entry'
        # journal_entry.company = self.company
        journal_entry.posting_date = self.posting_date
        journal_entry.posting_time = self.posting_time

        

        # Add Journal Entry accounts
        # Credit the default advance received account
        journal_entry.append("journal_entry_details", {
            "account": default_advance_account,
            "narration":"credit amt added",
            # "credit_in_account_currency": self.net_total,
            "credit": self.net_total,
            # "is_advance": "Yes"
        })

        # Debit the payment account
        journal_entry.append("journal_entry_details", {
            "account": self.payment_account,
            "narration":"debit amt added",
            # "debit_in_account_currency": self.net_total,
            "debit": self.net_total
        })

        journal_entry.remarks = "Created From The Advance Entry"

        # for row in journal_entry.journal_entry_details:
        #     total_debit += row.debit
        #     total_credit += row.credit

        journal_entry.total_credit = self.net_total
        journal_entry.total_debit = self.net_total
        

        # Save and submit the Journal Entry
        journal_entry.insert()
        frappe.db.commit()
        journal_entry.submit()

         # Check if the Journal Entry is submitted
        if journal_entry.docstatus == 1:
            # Update the balance in the default advance account
            customer_advances = frappe.get_doc('Account', default_advance_account)
            customer_advances.balance += self.net_total
            customer_advances.save()

        frappe.msgprint("Journal Entry created successfully with ID: {}".format(journal_entry.name))
