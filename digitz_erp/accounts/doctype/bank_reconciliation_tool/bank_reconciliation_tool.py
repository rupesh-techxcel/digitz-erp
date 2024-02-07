# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class BankReconciliationTool(Document):
    def on_update(self):
        self.update_bank_reconciliation()

    def update_bank_reconciliation(self):
        child_entries = self.bank_reconciliation_details
        for entry in child_entries:
            parent_doc = frappe.get_doc('Bank Reconciliation', entry.bank_reconciliation)
            parent_doc.status = entry.status
            parent_doc.settlement_date = entry.settlement_date
            parent_doc.save()


@frappe.whitelist()
def get_all_bank_entries():
    bank_reconciliations = frappe.get_all("Bank Reconciliation", fields=["name", "reference_no", "reference_date", "status","settlement_date"])
    entries_list = []
    for bank_reconciliation in bank_reconciliations:
        entry = {
            "name": bank_reconciliation.name,
            "reference_no": bank_reconciliation.reference_no,
            "reference_date": bank_reconciliation.reference_date,
            "status": bank_reconciliation.status,
			"settlement_date": bank_reconciliation.settlement_date
        }
        entries_list.append(entry)
    print(entries_list)
    return entries_list
