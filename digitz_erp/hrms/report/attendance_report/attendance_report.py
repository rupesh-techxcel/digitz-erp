import frappe
from frappe.utils import today

def execute(filters=None):
    columns = get_columns()
    data, summary = get_data(filters)
    return columns, data, None, get_chart_data(summary)

def get_columns():
    return [
        {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "designation", "label": "Designation", "fieldtype": "Data", "width": 150},
        {"fieldname": "attendance_date", "label": "Attendance Date", "fieldtype": "Date", "width": 100},
        {"fieldname": "attendance_status", "label": "Attendance Status", "fieldtype": "Data", "width": 100}
    ]

def get_data(filters):
    attendance_date = filters.get('date', today())

    attendance_records = frappe.db.sql("""
        SELECT 
            a.employee, a.employee_name, e.designation, a.attendance_date, a.attendance_status
        FROM 
            `tabAttendance` a inner join `tabEmployee` e on e.employee_code = a.employee
        WHERE 
            attendance_date = %s
    """, (attendance_date), as_dict=True)
    
    summary = get_summary(attendance_records)
    
    return attendance_records, summary

def get_summary(attendance_records):
    summary = {}
    for record in attendance_records:
        designation = record['designation']
        status = record['attendance_status']
        
        if designation not in summary:
            summary[designation] = {'Present': 0, 'Leave': 0}
        
        if status == 'Present':
            summary[designation]['Present'] += 1
        else:
            summary[designation]['Leave'] += 1
    
    return summary

def get_chart_data(summary):
    labels = list(summary.keys())
    present_values = [summary[designation]['Present'] for designation in labels]
    absent_values = [summary[designation]['Leave'] for designation in labels]
    
    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Present", 
                    "values": present_values
                },
                {
                    "name": "Leave", 
                    "values": absent_values
                }
            ]
        },
        "type": "bar",
        "height": 300
    }
    
    return chart
