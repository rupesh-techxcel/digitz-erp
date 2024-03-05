# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = get_columns()
    print(columns)
    data = get_combined_data(filters)
    chart = []
    return columns, data, None, chart

def get_purchase_data(filters=None):
    query = """
        SELECT
            'Standard Rated Expenses' AS label,
            ROUND(SUM(gross_total),2) AS total_gross_total,
            ROUND(SUM(tax_total),2) AS total_tax_total
        FROM
            `tabPurchase Invoice`
        WHERE
            docstatus != 2
            AND posting_date >= %(from_date)s
            AND posting_date <= %(to_date)s
    """
    if filters:
        if filters.get('posting_date'):
            query += " AND posting_date = %(posting_date)s"

    data = frappe.db.sql(query, filters, as_dict=True)
    return data

def get_sales_data(filters=None):
    query = """
         SELECT
            CONCAT('Standard rated supplies in ', c.emirate) as label,
            ROUND(SUM(ts.gross_total),2) AS total_gross_total,
            ROUND(SUM(ts.tax_total),2) AS total_tax_total,
            emirate
        FROM
            `tabSales Invoice` ts
        INNER JOIN
            `tabCustomer` c ON c.name = ts.customer
        WHERE
            ts.docstatus != 2
            AND ts.posting_date >= %(from_date)s
            AND ts.posting_date <= %(to_date)s
    """
    if filters:
        if filters.get('customer'):
            query += " AND ts.customer = %(customer)s"
        if filters.get('from_date'):
            query += " AND ts.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND ts.posting_date <= %(to_date)s"
    query += " GROUP BY emirate"

    data = frappe.db.sql(query, filters, as_dict=True)
    total_gross_total = sum(entry['total_gross_total'] for entry in data)
    total_tax_total = sum(entry['total_tax_total'] for entry in data)
    total_gross_total = round(total_gross_total,2)
    total_tax_total = round(total_tax_total,2)

    data = fillEmirates(data)

    # Add the total row
    data.append({
        'label': 'Total',
        'total_gross_total': total_gross_total,
        'total_tax_total': total_tax_total
    })    
    
    total_gross_total = total_gross_total if total_gross_total else 0 
    total_tax_total = total_tax_total if total_tax_total else 0
    

    return data,total_gross_total,total_tax_total

def fillEmirates(data):
    emirate_list = ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"]
    
    # Create a set of emirates already present in the data for O(1) lookup
    existing_emirates = {sales_data["emirate"] for sales_data in data}
    
    for emirate in emirate_list:
        if emirate not in existing_emirates:
            data.append({
                'emirate': emirate,  # Ensure you have a key for the emirate's name
                'label': 'Standard rated supplies in ' + emirate,
                'total_gross_total': 0.00,
                'total_tax_total': 0.00
            })
                           
    return data  

def get_combined_data(filters=None):
    
    sales_data, total_gross_sales,total_tax_sales = get_sales_data(filters)
    purchase_data = get_purchase_data(filters)
        
    # Calculate totals from the last row of purchase_data
    total_gross_purchase = purchase_data[0]['total_gross_total'] if purchase_data else 0
    total_tax_purchase = purchase_data[0]['total_tax_total'] if purchase_data else 0

    # Add Sl.No column to sales_data
    for idx, entry in enumerate(sales_data, start=1):
        entry['sl_no'] = idx

    # Add Sl.No column to purchase_data
    for idx, entry in enumerate(purchase_data, start=len(sales_data) + 2):
        entry['sl_no'] = idx

    total_gross_purchase = total_gross_purchase if total_gross_purchase else 0
    total_gross_sales = total_gross_sales if total_gross_sales else 0
    total_tax_sales = total_tax_sales if total_tax_sales else 0
    total_tax_purchase = total_tax_purchase if total_tax_purchase else 0

    # Create combined data including the calculated totals
    combined_data = sales_data + [{'label': ''}] + purchase_data + [
        {
            'sl_no': '',
            'label': 'Consolidated Tax',
            'total_gross_total': round(total_gross_sales-total_gross_purchase,2),
            'total_tax_total': round(total_tax_sales-total_tax_purchase,2)
        }
    ]

    return combined_data



def get_columns():
    return [               
        {
            "label": "Particulars",
            "fieldname": "label",
            "fieldtype": "Data",            
            "width": 400
        },        
        {
            "label": "Taxable Total",
            "fieldname": "total_gross_total",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Tax Total",
            "fieldname": "total_tax_total",
            "fieldtype": "Data",
            "width": 200
        },
    ]

