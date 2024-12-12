# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = [
        {"fieldname": "project", "label": "Project", "fieldtype": "Link", "options": "Project", "width": 150},
        {"fieldname": "sales_order_value", "label": "Sales Order Value", "fieldtype": "Currency", "width": 150},
        {"fieldname": "material_cost", "label": "Material Cost", "fieldtype": "Currency", "width": 150},
        {"fieldname": "labour_cost", "label": "Labour Cost", "fieldtype": "Currency", "width": 150},
        {"fieldname": "overhead_cost", "label": "Overhead Cost", "fieldtype": "Currency", "width": 150},
        {"fieldname": "profit", "label": "Profit", "fieldtype": "Currency", "width": 150},
    ]

    conditions = ""
    if filters.get("project"):
        conditions += "AND project.name = %(project)s"

    data = frappe.db.sql(f"""
        SELECT
            project.name AS project,
            project.sales_order_value AS sales_order_value,
            project.material_cost AS material_cost,
            project.labour_cost AS labour_cost,
            project.overheads AS overhead_cost,
            (project.sales_order_value - project.material_cost - project.labour_cost - project.overheads) AS profit
        FROM
            `tabProject` project
        WHERE
            IFNULL(project.sales_order_value, 0) > 0
            {conditions}
    """, filters, as_dict=1)

    return columns, data
