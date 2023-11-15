import frappe

@frappe.whitelist()
def get_expense_details(expense):
    return frappe.get_value('Expense Head', filters={'name': expense}, 
                            fieldname=['terms'], as_dict=True)
