# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)    
	return columns, data

def get_data(filters):
    conditions = []
    values = []

    # Add conditions and values dynamically based on provided filters
    if 'employee' in filters and filters['employee']:
        conditions.append("`tabEmployee Document`.parent = %s")
        values.append(filters['employee'])

    if 'status' in filters and filters['status']:
        conditions.append("`tabEmployee Document`.status = %s")
        values.append(filters['status'])

    # Construct the WHERE clause based on conditions
    where_clause = " AND ".join(conditions) if conditions else "1 = 1"

    # Query the child table data based on the dynamic conditions
    try:
         data = frappe.db.sql(f"""
        SELECT 
            parent AS employee,
            document_name,
            document_type,
            next_expiry_date,
            renewal_action_status,
            status
        FROM 
            `tabEmployee Document`
        WHERE
            {where_clause}
    """, values, as_dict=True)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error executing query')
        frappe.throw(f"An error occurred while executing the query: {str(e)}")

    return data


def get_columns():
    return [
        {
            "label": "Employee",
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150
        },
        {
            "label": "Document Name",
            "fieldname": "document_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": "Document Type",
            "fieldname": "document_type",
            "fieldtype": "Data",            
            "width": 120
        },
        {
            "label": "Next Expiry Date",
            "fieldname": "next_expiry_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": "Renewal Action Status",
            "fieldname": "renewal_action_status",
            "fieldtype": "Select",
            "options": "Pending\nCompleted\nNot Required",  # Adjust as per your options
            "width": 150
        },
        {
            "label": "Status",
            "fieldname": "status",
            "fieldtype": "Select",
            "options": "Active\nExpired",
            "width": 100
        }
    ]

    
    
    

