import frappe
from frappe.utils import getdate, today, flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    return columns, data, None, chart

def get_columns():
    return [
        {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "designation", "label": "Designation", "fieldtype": "Data", "width": 150},
        {"fieldname": "payroll_date", "label": "Payroll Date", "fieldtype": "Date", "width": 100},
        {"fieldname": "total_earnings", "label": "Total Earnings", "fieldtype": "Currency", "width": 150},
        {"fieldname": "total_deductions", "label": "Total Deductions", "fieldtype": "Currency", "width": 150},
        {"fieldname": "salary_payable_amount", "label": "Salary Payable Amount", "fieldtype": "Currency", "width": 150}
    ]

def get_data(filters):
    if not filters:
        return []

    year = filters.get('year')
    month = filters.get('month')
    employee = filters.get('employee')

    # Define the month number
    months = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
        'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    month_num = months.get(month)

    # Build the query
    query = """
        SELECT 
            ss.employee, ss.employee_name, ss.designation, ss.payroll_date, 
            SUM(CASE WHEN ssd.type = 'Earning' THEN ssd.amount ELSE 0 END) as total_earnings,
            SUM(CASE WHEN ssd.type = 'Deduction' THEN ssd.amount ELSE 0 END) as total_deductions,
            ss.salary_payable_amount
        FROM 
            `tabSalary Slip` ss
        JOIN 
            `tabSalary Slip Detail` ssd ON ss.name = ssd.parent
        WHERE 
            YEAR(ss.payroll_date) = %s AND MONTH(ss.payroll_date) = %s
    """
    
    # Add employee filter if provided
    if employee:
        query += " AND ss.employee = %s"
        params = (year, month_num, employee)
    else:
        params = (year, month_num)

    query += " GROUP BY ss.employee, ss.employee_name, ss.designation, ss.payroll_date, ss.salary_payable_amount"

    # Execute the query
    salary_slips = frappe.db.sql(query, params, as_dict=True)

    # Format amounts to 2 decimal places
    for slip in salary_slips:
        slip['total_earnings'] = "{:.2f}".format(slip['total_earnings'])
        slip['total_deductions'] = "{:.2f}".format(slip['total_deductions'])
        slip['salary_payable_amount'] = "{:.2f}".format(slip['salary_payable_amount'])
    
    return salary_slips

def get_chart_data(data):
    designation_salary_map = {}
    
    for row in data:
        if row['designation'] not in designation_salary_map:
            designation_salary_map[row['designation']] = 0
        designation_salary_map[row['designation']] += flt(row['salary_payable_amount'])
    
    labels = list(designation_salary_map.keys())
    values = [round(flt(designation_salary_map[designation]), 2) for designation in labels]
    
    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Total Salary", 
                    "values": values
                }
            ]
        },
        "type": "bar",
        "height": 300
    }
    
    return chart