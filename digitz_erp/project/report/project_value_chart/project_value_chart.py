import frappe

def execute(filters=None):
    filters = filters or {}

    # Base conditions: Filter by status 'Open'
    conditions = "p.status = 'Open'"
    if filters.get("project"):
        conditions += f" AND p.name = '{filters['project']}'"

    # Query to fetch project value data
    data = frappe.db.sql(f"""
        SELECT 
            p.name AS project_name,
            p.project_value
        FROM 
            `tabProject` p
        WHERE 
            {conditions}
    """, as_dict=1)

    # Define columns
    columns = [
        {"label": "Project Name", "fieldname": "project_name", "fieldtype": "Link", "options": "Project", "width": 200},
        {"label": "Project Value", "fieldname": "project_value", "fieldtype": "Currency", "width": 150},
    ]

    # Prepare chart data with green color for bars
    chart_data = {
        "data": {
            "labels": [row["project_name"] for row in data],
            "datasets": [
                {
                    "name": "Project Value",
                    "values": [row["project_value"] or 0 for row in data],  # Handle null values
                    "chartType": "bar"
                }
            ]
        },
        "type": "bar",  # Chart type: 'bar', 'line', 'pie', etc.
        "colors": ["#28a745"],  # Green color for bars
        "height": 300
    }

    return columns, data, None, chart_data
