# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	
	columns = get_columns() 
	data =get_data(filters)
	print("data from document psoting status report")
	print(data)
	return columns, data

def get_data(filters):
    data = frappe.db.sql("""
        SELECT document_type,
               document_name,
               posting_status
        FROM `tabDocument Posting Status` 
        WHERE posting_status="Pending" or posting_status ="Cancel Pending"
    """, filters, as_list=True)

    return data


def get_columns():
    return [
        {
            "fieldname": "document_name",
            "fieldtype": "Dynamic Link",
            "label": "Document Name",
            "options": "document_type",
            "width": 200,
        },
        {
            "fieldname": "document_type",
            "fieldtype": "Link",
            "label": "Document Type",
            "options": "DocType",
            "width": 200,
        },
        {
            "fieldname": "posting status",
            "fieldtype": "Data",
            "label": "Posting Status",
            "width": 150,
        },
    ]

