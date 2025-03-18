# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    filters = filters or {}

    # Get columns
    columns = get_columns()

    # Get data
    data = get_data(filters)

    # Get chart data
    chart_data = get_chart(data)

    return columns, data, None, chart_data

def get_columns():
    return [
        {"fieldname": "project", "label": "Project", "fieldtype": "Link", "options": "Project", "width": 150},
        {"fieldname": "sales_order_value", "label": "Sales Order Value", "fieldtype": "Currency", "width": 150},
        {"fieldname": "material_cost", "label": "Material Cost", "fieldtype": "Currency", "width": 150},
        {"fieldname": "labour_cost", "label": "Labour Cost", "fieldtype": "Currency", "width": 150},
        {"fieldname": "overhead_cost", "label": "Overhead Cost", "fieldtype": "Currency", "width": 150},
        {"fieldname": "profit", "label": "Profit", "fieldtype": "Currency", "width": 150},
    ]

def get_data(filters):
    conditions = ""
    if filters.get("project"):
        conditions += " AND project.name = %(project)s"

    query = f"""
        SELECT
            project.name AS project,
            project.project_value AS sales_order_value,
            project.material_cost AS material_cost,
            project.labour_cost AS labour_cost,
            project.overheads AS overhead_cost,
            (project.project_value - project.material_cost - project.labour_cost - project.overheads) AS profit
        FROM
            `tabProject` project
        WHERE
            IFNULL(project.project_value, 0) > 0
            {conditions}
    """

    return frappe.db.sql(query, filters, as_dict=1)

def get_chart(data):
    return {
        "data": {
            "labels": [row["project"] for row in data],
            "datasets": [
                {
                    "name": "Sales Order Value",
                    "values": [row["sales_order_value"] or 0 for row in data]
                },
                {
                    "name": "Profit",
                    "values": [row["profit"] or 0 for row in data]
                }
            ]
        },
        "type": "bar",  # Chart type: 'bar', 'line', 'pie', etc.
        "height": 300
    }
