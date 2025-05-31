import frappe
from frappe.utils import today, flt

def execute(filters=None):
    columns = get_columns()
    data, summary = get_data(filters)
    chart = get_chart_data(summary)
    return columns, data, None, chart

def get_columns():
    return [
        {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "designation", "label": "Designation", "fieldtype": "Data", "width": 150},
        {"fieldname": "date", "label": "Date", "fieldtype": "Date", "width": 100},
        {"fieldname": "leave_duration", "label": "Leave Duration", "fieldtype": "Float", "width": 100},
        {"fieldname": "leave_type", "label": "Leave Type", "fieldtype": "Data", "width": 100}
    ]

def get_data(filters):
    leave_date = filters.get('date', today())

    leave_records = frappe.db.sql("""
        SELECT 
            elr.employee, e.employee_name, e.designation, elr.date, elr.leave_duration, elr.leave_type
        FROM 
            `tabEmployee Leave Record` elr
        JOIN 
            `tabEmployee` e ON elr.employee = e.name
        WHERE 
            elr.date = %s
    """, (leave_date), as_dict=True)
    
    summary = get_summary(leave_records)
    
    return leave_records, summary

def get_summary(leave_records):
    summary = {}
    for record in leave_records:
        designation = record['designation']
        leave_duration = flt(record['leave_duration'])
        
        if designation not in summary:
            summary[designation] = 0
        
        summary[designation] += leave_duration
    
    return summary

def get_chart_data(summary):
    labels = list(summary.keys())
    values = [summary[designation] for designation in labels]
    
    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Total Leave Duration", 
                    "values": values
                }
            ]
        },
        "type": "bar",
        "height": 300
    }
    
    return chart
