# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import frappe.model.rename_doc as rd

class Project(Document):
    def before_save(self):
        net_total = frappe.db.get_value("Sales Order", self.sales_order, "net_total")
        self.project_amount = net_total

    def before_insert(self):
        warehouse_name = f"{self.project_name} - Warehouse"

        exists = frappe.db.exists('Warehouse',warehouse_name)

        if(exists):
            frappe.throw(f"Warehouse with name, {warehouse_name} already exist. Try With Some Other Name !")

    def after_insert(self):
        warehouse_name = f"{self.project_name} - Warehouse"
        global_settings = frappe.get_doc("Global Settings")

        warehouse = frappe.get_doc({
                'doctype': 'Warehouse',
                'warehouse_name': warehouse_name,
                'company': global_settings.default_company,
                'project': self.project_name
            })

        warehouse.save()   

    def before_rename(self, old, new, merge=False):
        warehouse_name = f"{new} - Warehouse"
        exists = frappe.db.exists('Warehouse', warehouse_name)
        if exists:
            frappe.throw(_("Warehouse with name {0} already exists. Try with some other name!").format(warehouse_name))
    
    def after_rename(self, old, new, merge=False):
        old_wh_name = f"{old} - Warehouse"
        new_wh_name = f"{new} - Warehouse"
        
        try:
            rd.rename_doc("Warehouse",old_wh_name, new_wh_name, force=False, merge=False, ignore_permissions=False, ignore_if_exists=False)

        except frappe.DoesNotExistError:
            frappe.msgprint(_("Warehouse {0} not found. Skipping warehouse rename.").format(old_wh_name))
        except Exception as e:
            frappe.log_error(f"Error renaming warehouse: {str(e)}")
            frappe.throw(_("Error renaming warehouse. Please check the error log."))


@frappe.whitelist()
def create_project_via_sales_order(sales_order_id):
    #print(sales_order_id)

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
