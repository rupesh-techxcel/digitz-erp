# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns, data = [], []
 
	if filters.get("group_by") == "Date":
		columns = get_columns_datewise()
		data = get_data_datewise(filters)
  
	elif filters.get("group_by") == "Supplier":
		columns = get_columns_supplierwise()
		data = get_data_supplierwise(filters)
  
	elif filters.get("group_by") == "Supplier And Date":
		columns = get_columns_supplier_and_datewise()
		data = get_data_supplier_and_datewise(filters)
  
	elif filters.get("group_by") == "None":
		columns = get_columns()
		data = get_data(filters)
 
	return columns, data

def get_data(filters):
    
	trans_data =[]
		
	if filters.get("supplier") and filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		supplier,document_no,document_date,amount,scheduled_date
		FROM 
		`tabPayment Schedule` ps
		WHERE ps.supplier = '{supplier}' and  ps.scheduled_date BETWEEN '{from_date}' and '{to_date}' ORDER BY ps.scheduled_date """.format(supplier=filters.get('supplier'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

	elif filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		supplier,document_no,document_date,amount,scheduled_date
		FROM 
		`tabPayment Schedule` ps
		WHERE ps.scheduled_date BETWEEN '{from_date}' and '{to_date}' ORDER BY ps.scheduled_date """.format(supplier=filters.get('supplier'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)


	return trans_data
    
def get_data_datewise(filters):
    
	trans_data =[]
		
	if filters.get("supplier") and filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		scheduled_date, sum(amount) as amount 
		FROM 
		`tabPayment Schedule` ps
		WHERE ps.supplier = '{supplier}' and  ps.scheduled_date BETWEEN '{from_date}' and '{to_date}' GROUP BY scheduled_date	ORDER BY ps.scheduled_date """.format(supplier=filters.get('supplier'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

	elif filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		scheduled_date, sum(amount) as amount 
		FROM 
		`tabPayment Schedule` ps
		WHERE  ps.scheduled_date BETWEEN '{from_date}' and '{to_date}' GROUP BY scheduled_date	ORDER BY ps.scheduled_date """.format(supplier=filters.get('supplier'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)


	return trans_data

def get_data_supplierwise(filters):
    
	trans_data =[]

	if filters.get("supplier") and filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		supplier, sum(amount) as amount 
		FROM 
		`tabPayment Schedule` ps
		WHERE ps.supplier = '{supplier}' and  ps.scheduled_date BETWEEN '{from_date}' and '{to_date}' GROUP BY supplier	ORDER BY ps.scheduled_date """.format(supplier=filters.get('supplier'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

	if  filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		supplier, sum(amount) as amount 
		FROM 
		`tabPayment Schedule` ps
		WHERE ps.scheduled_date BETWEEN '{from_date}' and '{to_date}' GROUP BY supplier	ORDER BY ps.scheduled_date """.format( from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

	return trans_data

def get_data_supplier_and_datewise(filters):
    
	trans_data = []

	if filters.get("supplier") and filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		scheduled_date, supplier, sum(amount) as amount 
		FROM 
		`tabPayment Schedule` ps
		WHERE ps.supplier = '{supplier}' and  ps.scheduled_date BETWEEN '{from_date}' and '{to_date}' GROUP BY supplier,scheduled_date	ORDER BY ps.scheduled_date """.format(supplier=filters.get('supplier'), from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

	if  filters.get("from_date") and filters.get("to_date"):
		trans_data = frappe.db.sql("""
		SELECT
		scheduled_date, supplier, sum(amount) as amount 
		FROM 
		`tabPayment Schedule` ps
		WHERE  ps.scheduled_date BETWEEN '{from_date}' and '{to_date}' GROUP BY supplier,scheduled_date	ORDER BY ps.scheduled_date """.format(from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)

	return trans_data


def get_columns_supplierwise():     
 
	return [
			{		
				"fieldname": "supplier",
				"fieldtype": "Data",
				"label": "Supplier",			
				"width": 230,	
			},						
   			{
				"fieldname": "amount",
				"fieldtype": "Currency",
				"label": "Amount",
				"width": 110,	
			}
		]
 
def get_columns_datewise():     
 
	return [
			{		
				"fieldname": "scheduled_date",
				"fieldtype": "Date",
				"label": "Date",			
				"width": 230,	
			},						
   			{
				"fieldname": "amount",
				"fieldtype": "Currency",
				"label": "Amount",
				"width": 110,	
			}
		]
 
def get_columns_supplier_and_datewise():     
 
	return [
			{		
				"fieldname": "scheduled_date",
				"fieldtype": "Date",
				"label": "Date",			
				"width": 230,	
			},
   			{		
				"fieldname": "supplier",
				"fieldtype": "Link",
				"label": "Supplier",
				"options": "Supplier",    		
				"width": 230,	
			},												
   			{
				"fieldname": "amount",
				"fieldtype": "Currency",
				"label": "Amount",
				"width": 110,	
			}
		]
 
def get_columns():     
 
	return [
			{		
				"fieldname": "scheduled_date",
				"fieldtype": "Date",
				"label": "Scheduled Date",			
				"width": 230,	
			},
   			{		
				"fieldname": "supplier",
				"fieldtype": "Link",
				"label": "Supplier",
				"options": "Supplier",    		
				"width": 230,	
			},	
      		{		
				"fieldname": "document_no",
				"fieldtype": "Data",
				"label": "Document",			
				"width": 230,	
			},
        	{		
				"fieldname": "document_date",
				"fieldtype": "Date",
				"label": "Document Date",			
				"width": 230,	
			},				
   			{
				"fieldname": "amount",
				"fieldtype": "Currency",
				"label": "Amount",
				"width": 110,	
			}
		]
 
 
