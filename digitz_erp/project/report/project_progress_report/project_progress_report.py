import frappe

def execute(filters=None):
    filters = filters or {}

    # Get data
    data = get_data(filters)

    # Get columns
    columns = get_columns()

    # Get chart data
    chart_data = get_chart(data)

    return columns, data, None, chart_data

def get_data(filters):
    # Base conditions
    conditions = "p.status = 'Open'"
    if filters.get("project"):
        conditions += f" AND p.name = '{filters['project']}'"

    # Query to fetch project data
    return frappe.db.sql(f"""
        SELECT 
            p.name AS project_name,
            c.customer_name AS customer_name,
            p.actual_start_date,
            p.actual_end_date,
            p.project_value,
            (
                SELECT 
                    pe.total_completion_percentage 
                FROM 
                    `tabProgress Entry` pe 
                WHERE 
                    pe.project = p.name 
                ORDER BY 
                    pe.posting_date DESC 
                LIMIT 1
            ) AS progress,
            p.status
        FROM 
            `tabProject` p
        LEFT JOIN 
            `tabCustomer` c ON p.customer = c.name
        WHERE 
            {conditions}
    """, as_dict=1)

def get_columns():
    # Define columns
    return [
        {"label": "Project Name", "fieldname": "project_name", "fieldtype": "Link", "options": "Project", "width": 200},
        {"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 200},
        {"label": "Actual Start Date", "fieldname": "actual_start_date", "fieldtype": "Date", "width": 150},
        {"label": "Actual End Date", "fieldname": "actual_end_date", "fieldtype": "Date", "width": 150},
        {"label": "Project Value", "fieldname": "project_value", "fieldtype": "Currency", "width": 150},
        {"label": "Progress (%)", "fieldname": "progress", "fieldtype": "Percent", "width": 150},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]

def get_chart(data):
    # Prepare chart data
    return {
        "data": {
            "labels": [row["project_name"] for row in data],
            "datasets": [
                {
                    "name": "Progress (%)",
                    "values": [row["progress"] or 0 for row in data]  # Handle null values
                },
                {
                    "name": "Project Value",
                    "values": [row["project_value"] or 0 for row in data]  # Handle null values
                }
            ]
        },
        "type": "bar",  # Chart type: 'bar', 'line', 'pie', etc.
        "height": 300
    }
