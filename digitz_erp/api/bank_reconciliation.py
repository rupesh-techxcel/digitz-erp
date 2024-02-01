import frappe


@frappe.whitelist()
def create_bank_reconciliation(doc_type, name):
    if doc_type in ["Sales Invoice", "Purchase Invoice", "Sales Return","Purchase Return", "Payment Entry", "Receipt Entry"]:
        doc = frappe.get_doc(doc_type, name)
        if doc.payment_mode == "Bank":
            bank_reconciliation = frappe.new_doc("Bank Reconciliation")
            bank_reconciliation.update({
                "document_type": doc_type,
                "document_name": name,
                "cheque_no": doc.cheque_no,
                "cheque_date": doc.cheque_date,
                "bank_account": doc.bank_account,
            })
            bank_reconciliation.insert(ignore_permissions=True)
            frappe.msgprint(f"Bank Reconciliation created for {doc_type} {name}")


@frappe.whitelist()
def cancel_bank_reconciliation(doc_type, name):
    if doc_type in ["Sales Invoice", "Purchase Invoice","Sales Return","Purchase Return", "Payment Entry", "Receipt Entry"]:
        bank_reconciliation = frappe.get_all("Bank Reconciliation",
                                             filters={"document_type": doc_type, "document_name": name},
                                             fields=["name"])

        if bank_reconciliation:
            frappe.delete_doc("Bank Reconciliation", bank_reconciliation[0]['name'], ignore_permissions=True)
            frappe.msgprint(f"Bank Reconciliation deleted for {doc_type} {name}")
