import frappe
from frappe.utils import today, flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    data = group_data_by_salary_group(data)
    return columns, data

def get_data(filters):
    conditions = []
    if filters:
        if filters.get("employee"):
            conditions.append("sr.employee = %(employee)s")
        if filters.get("salary_group"):
            conditions.append("e.salary_group = %(salary_group)s")
    
    conditions = "WHERE " + " AND ".join(conditions) if conditions else ""

    data = frappe.db.sql(f"""
        SELECT sr.employee, e.employee_name, e.salary_group,sr.salary_month, sr.basic_salary,sr.deductions_for_leave, sr.salary_month,
               CONCAT(FORMAT(sr.overtime_trips, 0), '@', FORMAT(sr.overtime_rate, 2), '=', FORMAT(sr.overtime_amount, 2)) AS overtime_details,
               CONCAT(
                   FORMAT(sr.holiday_days, 0), '@', FORMAT(sr.holiday_rate, 2), '+',
                   FORMAT(sr.holiday_overtime, 0), '- Ded:', FORMAT(sr.holiday_deductions, 2),
                   '=', FORMAT(sr.holiday_amount, 2)                  
               ) AS holiday_details,
               CONCAT(FORMAT(sr.shutdown_nos, 0), '@', FORMAT(sr.shutdown_rate, 2), '=', FORMAT(sr.shutdown_amount, 2)) AS shutdown_details,
               CONCAT(FORMAT(sr.others_hrs, 0), '@', FORMAT(sr.others_rate, 2), '=', FORMAT(sr.others_amount, 2)) AS others_details,
               sr.gross_salary, sr.advance_deduction, sr.total_deductions, sr.net_salary
        FROM `tabSalary Report Record` sr
        INNER JOIN `tabEmployee` e ON sr.employee = e.name 
        {conditions}
    """, filters, as_dict=True)
    
    return data

def get_columns():
    return [
        {"fieldname": "employee_name", "label": "Employee", "fieldtype": "Data", "width": 120},
        {"fieldname": "salary_month", "label": "Month", "fieldtype": "Data", "width": 60},        
        {"fieldname": "basic_salary", "label": "Basic Salary", "fieldtype": "Float", "width": 100},        
        {"fieldname": "deductions_for_leave", "label": "Leave Deduction", "fieldtype": "Float", "width": 100},
        {"fieldname": "overtime_details", "label": "Overtime Details", "fieldtype": "Data", "width": 150},
        {"fieldname": "holiday_details", "label": "Holiday Details", "fieldtype": "Data", "width": 150},
        {"fieldname": "shutdown_details", "label": "Shutdown Details", "fieldtype": "Data", "width": 150},
        {"fieldname": "others_details", "label": "Others Details", "fieldtype": "Data", "width": 150},
        {"fieldname": "gross_salary", "label": "Gross Salary", "fieldtype": "Currency", "width": 100},
        {"fieldname": "advance_deduction", "label": "Advance Ded.", "fieldtype": "Float", "width": 100},        
        {"fieldname": "net_salary", "label": "Net Salary", "fieldtype": "Currency", "width": 100},
    ]

def group_data_by_salary_group(data):
    grouped_data = []
    current_group = None

    for row in data:
        if row['salary_group'] != current_group:
            # Add a row for the salary group
            grouped_data.append({
                "employee_name": f"{row['salary_group']}",
                "basic_salary": None,
                "deductions_for_leave": None,
                "overtime_details": None,
                "holiday_details": None,
                "shutdown_details": None,
                "others_details": None,
                "gross_salary": None,
                "advance_deduction": None,
                "total_deductions": None,
                "net_salary": None,
                "indent": 0,
                "is_group": 1
            })
            current_group = row['salary_group']

        # Add the actual data row
        grouped_data.append({
            "employee_name": row['employee_name'],
            "basic_salary": row['basic_salary'],
            "deductions_for_leave":row['deductions_for_leave'],
            "salary_month":row['salary_month'],
            "overtime_details": row['overtime_details'],
            "holiday_details": row['holiday_details'],
            "shutdown_details": row['shutdown_details'],
            "others_details": row['others_details'],
            "gross_salary": row['gross_salary'],
            "advance_deduction": row['advance_deduction'],
            "total_deductions": row['total_deductions'],
            "net_salary": row['net_salary'],
            "indent": 1,
            "is_group": 0
        })

    return grouped_data
