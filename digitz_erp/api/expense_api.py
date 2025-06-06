import frappe

@frappe.whitelist()
def get_expense_details(expense):
    return frappe.get_value('Expense Head', filters={'name': expense}, 
                            fieldname=['terms'], as_dict=True)

@frappe.whitelist()
def create_expense_heads_from_accounts():
    accounts = frappe.get_all(
        "Account",
        filters={
            "is_group": 0,
            "root_type": "Expense"
        },
        fields=["name"]
    )

    created = []
    skipped_linked = []
    skipped_duplicate = []

    for acc in accounts:
        if account_already_linked(acc.name):
            skipped_linked.append(acc.name)
            continue

        if expense_head_name_exists(acc.name):
            skipped_duplicate.append(acc.name)
            continue

        try:
            expense_head_doc = frappe.new_doc("Expense Head")
            expense_head_doc.expense_type = "Expense"
            expense_head_doc.expense_head = acc.name
            expense_head_doc.account = acc.name
            expense_head_doc.tax = "UAE VAT - 5%"
            expense_head_doc.insert(ignore_permissions=True)
            created.append(acc.name)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed to create Expense Head for account: {acc.name}")

    # Summary
    message = (
        f"{len(created)} Expense Heads created.<br>"
        f"{len(skipped_linked)} skipped (account already linked).<br>"
        f"{len(skipped_duplicate)} skipped (duplicate expense head name)."
    )
    frappe.msgprint(message, alert=1)

# Separated checks

def account_already_linked(account_name):
    return frappe.db.exists("Expense Head", {"account": account_name})

def expense_head_name_exists(expense_head_name):
    return frappe.db.exists("Expense Head", {"expense_head": expense_head_name})