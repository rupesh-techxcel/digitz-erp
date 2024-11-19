# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import frappe.model.rename_doc as rd
from digitz_erp.api.project_api import update_project_advance_amount

class Project(Document):
    def before_save(self):
        net_total = frappe.db.get_value("Sales Order", self.sales_order, "net_total")
        self.project_amount = net_total
    
    def on_update(self):
        self.update_advance_amount()
        
    
    def advance_entry_exists(self):
        allocation_exists = frappe.db.exists("Receipt Allocation", {
        "reference_type": "Sales Order",
        "reference_name": self.sales_order
        })

        return bool(allocation_exists)
        
    def update_advance_amount(self):
    
        progress_entry_exists = frappe.db.exists("Progress Entry", {"project": self.project_name})

        if not progress_entry_exists:
            
            if self.advance_entry_exists():                
                
                if not self.advance_amount:
                    
                    # Step 3: Fetch total allocated amount from Receipt Allocation
                    total_advance = frappe.db.sql("""
                        SELECT SUM(paying_amount) AS total_advance
                        FROM `tabReceipt Allocation`
                        WHERE reference_type = 'Sales Order' AND reference_name = %s
                    """, (self.sales_order,), as_dict=True)[0].get('total_advance', 0) or 0
                    
                    self.advance_amount = total_advance
                    frappe.msgprint("Advance amount fetched from the 'Receipt Entry' made for the 'Sales Order'.", alert=True)
            else:
                frappe.msgprint("Advance for the project can be recorded using a 'Receipt Entry' linked to the 'Sales Order'.", alert=True)

@frappe.whitelist()
def calculate_retention_amt(sales_order_id, retention_percentage):
    sales_doc = frappe.get_doc("Sales Order", sales_order_id)

    try:
        net_total = float(sales_doc.net_total)
        retention_percentage = float(retention_percentage)
    except ValueError as e:
        frappe.throw(f"Invalid value provided: {e}")

    retention_amt = (net_total * retention_percentage) / 100
    
    print("retention_amt",retention_amt)

    return {
        "total_project_amt": net_total,
        "retention_amt": retention_amt,
        "amount_after_retention": net_total - retention_amt,
    }


@frappe.whitelist()
def load_project_amt(sales_order_id):
    sales_doc = frappe.get_doc("Sales Order", sales_order_id)

    try:
        net_total = float(sales_doc.net_total)
    except ValueError as e:
        frappe.throw(f"Invalid value provided: {e}")

    return {
        "total_project_amt": net_total,
    }


@frappe.whitelist()
def get_project(project_id):
    project_doc = frappe.get_doc("Project", project_id)

    if project_doc:
        return project_doc
    else:
        return ""
