# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Project(Document):
    def before_save(self):
        net_total = frappe.db.get_value("Sales Order", self.sales_order, "net_total")
        self.project_amount = net_total


@frappe.whitelist()
def create_project_via_sales_order(sales_order_id):
    print(sales_order_id)

    sales_doc = frappe.get_doc("Sales Order", sales_order_id)

    return {
        "customer": sales_doc.customer,
        "sales_order": sales_doc.name,
        "project_amount": sales_doc.net_total,
        "sales_order_id": sales_order_id,
    }


@frappe.whitelist()
def calculate_rest_amt(sales_order_id, retentation_percentage):
    sales_doc = frappe.get_doc("Sales Order", sales_order_id)

    try:
        net_total = float(sales_doc.net_total)
        retention_percentage = float(retentation_percentage)
    except ValueError as e:
        frappe.throw(f"Invalid value provided: {e}")

    retention_amt = (net_total * retention_percentage) / 100

    return {
        "total_project_amt": net_total,
        "retentation_amt": retention_amt,
        "amount_after_retentation": net_total - retention_amt,
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
