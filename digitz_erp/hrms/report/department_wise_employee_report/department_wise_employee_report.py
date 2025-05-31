# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns, data = [], []
 
    data = get_data(filters)
    columns = get_columns()
    chart = get_chart_data(data)
    return columns, data, None, chart

def get_data(filters=None):
    if filters is None:
        filters = {}

    conditions = []
    if filters.get("employee"):
        conditions.append("employee_code = %(employee)s")
    if filters.get("designation"):
        conditions.append("designation = %(designation)s")
    if filters.get("department"):
        conditions.append("department = %(department)s")
    if filters.get("status"):
        conditions.append("status = %(status)s")
    
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    query = f"""
        SELECT employee_code, employee_name, department, designation, status 
        FROM `tabEmployee`
        {where_clause}
    """
    
    print("query")
    print(query)
    
    data = frappe.db.sql(query, filters, as_dict=True)
    
    return data

def get_columns():
    return [
        {
            "fieldname": "employee_code",
            "fieldtype": "Link",
            "label": "Employee Code",
            "options": "Employee",
            "width": 200,
        },
        {
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "label": "Employee Name",
            "width": 200,
        },
        {
            "fieldname": "designation",
            "fieldtype": "Link",
            "label": "Designation",
            "options": "Designation",
            "width": 200,
        },
        {
            "fieldname": "department",
            "fieldtype": "Link",
            "label": "Department",
            "options": "Department",
            "width": 200,
        },
        {
            "fieldname": "status",
            "fieldtype": "Data", 
            "label": "Status",
            "width": 200
        }
    ]

def get_chart_data(data):
    department_counts = {}
    for row in data:
        department = row["department"]
        if department in department_counts:
            department_counts[department] += 1
        else:
            department_counts[department] = 1

    labels = list(department_counts.keys())
    values = list(department_counts.values())

    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Employee Count",
                    "values": values
                }
            ]
        },
        "type": "bar",  # Change this to 'line', 'pie', etc. based on the type of chart you want
        "colors": ["#7cd6fd"],
    }
    return chart
