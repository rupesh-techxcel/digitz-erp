import frappe

def execute(filters=None):
    filters = filters or {}

    # Base conditions: Filter by status 'Open'
    conditions = "p.status = 'Open'"
    if filters.get("project"):
        conditions += f" AND p.name = '{filters['project']}'"

    # Query to fetch project progress data
    data = frappe.db.sql(f"""
        SELECT 
            p.name AS project_name,
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
            ) AS progress
        FROM 
            `tabProject` p
        WHERE 
            {conditions}
    """, as_dict=1)

    # Define columns
    columns = [
        {"label": "Project Name", "fieldname": "project_name", "fieldtype": "Link", "options": "Project", "width": 200},
        {"label": "Progress (%)", "fieldname": "progress", "fieldtype": "Percent", "width": 150},
    ]

    # Prepare chart data
    chart_data = {
        "data": {
            "labels": [row["project_name"] for row in data],
            "datasets": [
                {
                    "name": "Project Progress (%)",
                    "values": [row["progress"] or 0 for row in data]  # Handle null values
                }
            ]
        },
        "type": "bar",  # Chart type: 'bar', 'line', 'pie', etc.
        "height": 300
    }

    return columns, data, None, chart_data
