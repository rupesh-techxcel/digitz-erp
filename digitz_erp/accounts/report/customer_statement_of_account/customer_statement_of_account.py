# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):    
	
	if(filters.get('group_by')  == "Invoice"):
     
		if(filters.get('customer')):		
			columns = get_columns()
		else:
			columns = get_columns_with_customer()  
   
		data = get_data(filters)
  
	else:
		columns = get_columns_for_customer_group()
		data = get_data_customer_wise(filters)
  
	if filters.get('show_pending_only'):
		data = [
			row for row in data if 
			(row.get('doc_type') == 'Sales Invoice' and row.get('balance_amount', 0) > 0) or 
			(row.get('doc_type') == 'Sales Return' and row.get('balance_amount', 0) < 0) or 
			(row.get('doc_type') == 'Credit Note' and row.get('balance_amount', 0) < 0)
		]     
	return columns, data

def get_data_customer_wise(filters):
    
    customer_condition = "customer = '{}'".format(filters.get('customer')) if filters.get('customer') else "1=1"
    date_condition = "posting_date BETWEEN '{0}' AND '{1}'".format(filters.get('from_date'), filters.get('to_date')) if filters.get('from_date') and filters.get('to_date') else "1=1"
    
    invoice_query = f"""
        SELECT 
            customer,
            rounded_total,
            paid_amount,
            posting_date
        FROM `tabSales Invoice`
        WHERE 
            (docstatus = 1 or docstatus = 0) 
            AND credit_sale = 1 
            AND {customer_condition}
            AND {date_condition}
    """
    
    return_query = f"""
        SELECT 
            customer,
            rounded_total * -1 as rounded_total,
            paid_amount * -1 as paid_amount,
            posting_date
        FROM `tabSales Return`
        WHERE 
            (docstatus = 1 or docstatus = 0) 
            AND credit_sale = 1 
            AND {customer_condition}
            AND {date_condition}
    """

    combined_query = f"""
        SELECT 
            c.customer_name as customer,
            SUM(si.rounded_total) as amount,
            SUM(si.paid_amount) as paid_amount,
            SUM(si.rounded_total) - SUM(IFNULL(si.paid_amount, 0)) as balance_amount
        FROM (
            {invoice_query}
            UNION ALL
            {return_query}
        ) AS si
        LEFT JOIN `tabCustomer` c ON si.customer = c.name
        WHERE (c.exclude_from_showing_in_soa IS NULL OR c.exclude_from_showing_in_soa = 0)
        GROUP BY c.customer_name
        ORDER BY posting_date
    """

    return frappe.db.sql(combined_query, as_dict=True)
    
def get_data(filters):
    
    print("from get_data")
    
    # Define the base fields common in both tables, but handle customer_name outside of this since it's fetched via JOIN
    invoice_fields = """
        si.name as sales_invoice_name,
        si.posting_date as posting_date,
        si.rounded_total as amount,
        si.paid_amount,
        si.rounded_total - COALESCE(si.paid_amount, 0) as balance_amount,
        si.ship_to_location as 'ship_to_location'
    """
    
    return_fields = """
        si.name as sales_invoice_name,
        si.posting_date as posting_date,
        si.rounded_total*-1 as amount,
        si.paid_amount * -1 as paid_amount,
        (si.rounded_total - COALESCE(si.paid_amount, 0))*-1 as balance_amount,
        si.ship_to_location as 'ship_to_location'
    """

    invoice_fields = invoice_fields + ", si.delivery_note as delivery_note"
    return_fields = return_fields + ", '' as delivery_note"  # Assuming 'delivery_note' does not exist in 'tabSales Return'

    customer_condition = f"AND si.customer = '{filters.get('customer')}'" if filters.get('customer') else ""
    date_condition = f"AND si.posting_date BETWEEN '{filters.get('from_date')}' AND '{filters.get('to_date')}'" if filters.get('from_date') and filters.get('to_date') else ""

    invoice_query = f"""
    SELECT 
        {invoice_fields},'Sales Invoice' as doc_type ,
        c.customer_name as customer_name
    FROM 
        `tabSales Invoice` si 
    LEFT JOIN
        `tabCustomer` c ON si.customer = c.name
    WHERE 
        (si.docstatus = 1 or si.docstatus = 0) 
        AND si.credit_sale = 1 
        {customer_condition}
        {date_condition}
        AND (c.exclude_from_showing_in_soa IS NULL OR c.exclude_from_showing_in_soa = 0)
    """

    return_query = f"""
    SELECT 
        {return_fields},'Sales Return' as doc_type ,
        c.customer_name as customer_name
    FROM 
        `tabSales Return` si 
    LEFT JOIN
        `tabCustomer` c ON si.customer = c.name
    WHERE 
        (si.docstatus = 1 or si.docstatus = 0) 
        AND si.credit_sale = 1 
        {customer_condition}
        {date_condition}
        AND (c.exclude_from_showing_in_soa IS NULL OR c.exclude_from_showing_in_soa = 0)
    """

    final_query = f"({invoice_query}) UNION ALL ({return_query}) ORDER BY posting_date"

    data = frappe.db.sql(final_query, as_dict=True)

    # Assuming the delivery_note is relevant only for invoices
    for dl in data:
        if 'sales_invoice_name' in dl and 'tabSales Invoice' in dl['sales_invoice_name']:
            delivery_note_name = frappe.db.get_value("Sales Invoice Delivery Notes", {"parent": dl.get('sales_invoice_name')}, 'delivery_note')
            dl.update({"delivery_note": delivery_note_name or dl.get('delivery_note')})

    return data

def get_columns():
	return [
		{
		
			"fieldname": "sales_invoice_name",
			"fieldtype": "Link",
			"label": "Invoice No",
			"options": "Sales Invoice",
			"width": 150,
	
		},
		{
		
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"label": "Date",
			"width": 120,
	
		},
		{
		
			"fieldname": "ship_to_location",
			"fieldtype": "Data",
			"label": "Delivery Location",
			"width": 120,
	
		},
		# {
		
		# 	"fieldname": "delivery_note",
		# 	"fieldtype": "Data",
		# 	"label": "Delivery Note",
		# 	"width": 150,
	
		# },
		{
		
			"fieldname": "amount",
			"fieldtype": "Currency",
			"label": "Invoice Amount",
			"width": 120,
	
		},
		{
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"label": "Paid Amount",
			"width": 120,	
		},
  		{
			"fieldname": "balance_amount",
			"fieldtype": "Currency",
			"label": "Balance Amount",
			"width": 120,	
		}
	]

def get_columns_with_customer():
	return [
		{
		
			"fieldname": "customer_name",
			"fieldtype": "Link",
			"label": "Customer",
			"options": "Customer",
			"width": 150,	
		},
  		{
		
			"fieldname": "sales_invoice_name",
			"fieldtype": "Link",
			"label": "Invoice No",
			"options": "Sales Invoice",
			"width": 150,
	
		},
		{
		
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"label": "Date",
			"width": 120,
	
		},
		{
		
			"fieldname": "ship_to_location",
			"fieldtype": "Data",
			"label": "Delivery Location",
			"width": 120,
	
		},
		# {
		
		# 	"fieldname": "delivery_note",
		# 	"fieldtype": "Data",
		# 	"label": "Delivery Note",
		# 	"width": 150,
	
		# },
		{
		
			"fieldname": "amount",
			"fieldtype": "Currency",
			"label": "Invoice Amount",
			"width": 120,
	
		},
		{
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"label": "Paid Amount",
			"width": 120,	
		},
  		{
			"fieldname": "balance_amount",
			"fieldtype": "Currency",
			"label": "Balance Amount",
			"width": 120,	
		}
	]

def get_columns_for_customer_group():
	return [
		{
		
			"fieldname": "customer",
			"fieldtype": "Link",
			"label": "Customer",
			"options": "Customer",
			"width": 300,	
		},		
		{
		
			"fieldname": "amount",
			"fieldtype": "Currency",
			"label": "Invoice Amount",
			"width": 180,
	
		},
		{
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"label": "Paid Amount",
			"width": 180,	
		},
  		{
			"fieldname": "balance_amount",
			"fieldtype": "Currency",
			"label": "Balance Amount",
			"width": 180,	
		}
	]
