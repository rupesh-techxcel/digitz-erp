# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import frappe.model.rename_doc as rd

class Project(Document):
    
    def before_validate(self):
        self.update_advance_amount()     
        self.update_estimate_material_cost()
            
    def on_update(self):
         
        progress_entry_exists = frappe.db.exists("Progress Entry", {"project": self.project_name})
        if not progress_entry_exists and self.docstatus ==0:     
            frappe.msgprint("Submit the document to create the first 'Progress Entry' for the project.", alert=True)
            
    def before_cancel(self):
        # Check if rows exist in the 'project_stage_table'
        if self.project_stage_table:
            frappe.throw(
                _("Cannot cancel the Project because there are rows in the 'Project Progress' table. "
                "Please delete the project progress entries before cancelling.")
            )

    def update_advance_amount(self):
        
        advance_amount_query = frappe.db.sql("""
        SELECT gross_total, advance_percentage
        FROM `tabSales Invoice`
        WHERE for_advance_payment = 1 AND sales_order = %s AND docstatus = 1
        """, (self.sales_order,), as_dict=True)

        # Handle cases where no matching invoices are found
        advance_amount = advance_amount_query[0].get("gross_total", 0) if advance_amount_query else 0
        advance_percentage = advance_amount_query[0].get("advance_percentage", 0) if advance_amount_query else 0
        self.advance_amount = advance_amount
        self.advance_percentage = advance_percentage
    
    def update_estimate_material_cost(self):
        if self.boq:
            estimate_doc = frappe.get_doc("Estimate",{'boq':self.boq})
            self.estimated_material_cost = estimate_doc.total_material_cost
    
    
@frappe.whitelist()
def calculate_retention_amt(sales_order_id, retention_percentage):
    sales_doc = frappe.get_doc("Sales Order", sales_order_id)

    try:
        net_total = float(sales_doc.gross_total)
        retention_percentage = float(retention_percentage)
    except ValueError as e:
        frappe.throw(f"Invalid value provided: {e}")

    retention_amt = (net_total * retention_percentage) / 100
    print("sales_order_amt", net_total)
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
