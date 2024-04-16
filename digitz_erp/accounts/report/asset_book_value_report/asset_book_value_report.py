# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)    
	return columns, data

def get_data(filters):
  
	# Base SQL query
    sql_query = """
        SELECT 
            asset_name,
            asset_group,
            asset_location,
            asset_category,
            gross_value,
            opening_depreciation,
            rate_of_depreciation
            value_after_depreciation
        FROM 
            `tabAsset`
        WHERE
            1=1
    """

    # Parameters for the query
    params = {}

    # Add AND clause if 'asset' filter is provided
    asset = filters.get('asset')
    if asset:
        sql_query += " AND asset = %(asset)s"
        params['asset'] = asset

    # Execute the query
    data = frappe.db.sql(sql_query, params, as_dict=True)

    return data

def get_columns():
    return [
        {
            "label": "Asset",
            "fieldname": "asset",
            "fieldtype": "Link",
            "options": "Asset",
            "width": 150
        },
        {
            "label": "Asset Group",
            "fieldname": "asset_group",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": "Date",
            "fieldname": "date_of_depreciation",
            "fieldtype": "Date",            
            "width": 120
        },
        {
            "label": "Opening Dpcn",
            "fieldname": "opening_depreciation",
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "label": "Depreciation",
            "fieldname": "depreciation",
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "label": "Accum. Dpcn",
            "fieldname": "accumulated_depreciation",
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "label": "Book Value",
            "fieldname": "book_value",
            "fieldtype": "Currency",
            "width": 100
        }        
    ]
