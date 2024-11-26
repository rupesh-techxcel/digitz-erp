import frappe

def execute(filters=None):
	filters = filters or {}

	# Base conditions
	conditions = "p.status = 'Open'"
	if filters.get("project"):
		conditions += f" AND p.name = '{filters['project']}'"

	# Query to fetch project data with customer_name, actual_start_date, actual_end_date, progress, and project_value
	data = frappe.db.sql(f"""
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

	# Define columns
	columns = [
		{"label": "Project Name", "fieldname": "project_name", "fieldtype": "Link", "options": "Project", "width": 200},
		{"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 200},
		{"label": "Actual Start Date", "fieldname": "actual_start_date", "fieldtype": "Date", "width": 150},
		{"label": "Actual End Date", "fieldname": "actual_end_date", "fieldtype": "Date", "width": 150},
		{"label": "Project Value", "fieldname": "project_value", "fieldtype": "Currency", "width": 150},
		{"label": "Progress (%)", "fieldname": "progress", "fieldtype": "Percent", "width": 150},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
	]

	# Prepare chart data
	chart_data = {
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

	return columns, data, None, chart_data
