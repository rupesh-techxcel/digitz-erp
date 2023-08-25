# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    
	if(filters.get('group_by')  == "Invoice"):    
		if(filters.get('supplier')):
			print("customer filter")
			columns = get_columns()
		else:
			print("other filter")
			columns = get_columns_with_supplier()  
			data = get_data(filters)
	else:
		columns = get_columns_for_supplier_group()		
		data = get_data_supplier_wise(filters)
  
	if(filters.get('show_pending_only')):		
		data = [row for row in data if row.get('balance_amount', 0) > 0]
	
	return columns, data

def get_data(filters):
	data = ""

	print(filters.get('supplier'))
 
	if filters.get('supplier') and  filters.get('from_date') and filters.get('to_date'):
     	
  
		# data = frappe.db.sql(""" SELECT si.name as purchase_invoice_name,si.posting_date as posting_date,si.rounded_total as amount,pi.paid_amount,si.rounded_total - IFNULL(pi.paid_amount,0) as balance_amount,si.delivery_note as delivery_note,si.ship_to_location as 'ship_to_location' FROM `tabSales Invoice` si  where (si.docstatus = 1 or si.docstatus=0) and si.credit_sale=1 and si.customer = '{0}' and si.posting_date BETWEEN '{1}' and '{2}'  order by si.posting_date""".format(filters.get('customer'),filters.get('from_date'),filters.get('to_date')),as_dict=True)
		data = frappe.db.sql("""
		SELECT 
		pi.name as purchase_invoice_name,
		pi.supplier_inv_no,
		pi.posting_date as posting_date,
		pi.rounded_total as amount,
		pi.paid_amount,
		pi.rounded_total - IFNULL(pi.paid_amount, 0) as balance_amount,		
		s.supplier_name as supplier_name
		FROM 
		`tabPurchase Invoice` pi
		LEFT JOIN
		`tabSupplier` s ON pi.supplier = s.name
		WHERE 
		(pi.docstatus = 1 or pi.docstatus = 0) 
		AND pi.credit_purchase = 1 
		AND pi.supplier = '{0}' 
		AND pi.posting_date BETWEEN '{1}' and '{2}'		
		ORDER BY 
		pi.posting_date
		""".format(filters.get('supplier'), filters.get('from_date'), filters.get('to_date')), as_dict=True)
  
  		# data = frappe.db.sql(""" SELECT si.name as purchase_invoice_name,si.posting_date as posting_date,si.rounded_total as amount,pi.paid_amount,si.rounded_total - IFNULL(pi.paid_amount,0) as balance_amount,si.delivery_note as delivery_note,si.ship_to_location as 'ship_to_location' FROM `tabSales Invoice` si  where si.docstatus = 0 and si.credit_sale=1 and si.customer = '{0}' and si.posting_date BETWEEN '{1}' and '{2}'  order by si.posting_date""".format(filters.get('customer'),filters.get('from_date'),filters.get('to_date')),as_dict=True)
  
	elif filters.get('from_date') and filters.get('to_date'):
		data = frappe.db.sql("""
		SELECT 
		pi.name as purchase_invoice_name,
  		pi.supplier_inv_no,
		pi.posting_date as posting_date,
		pi.rounded_total as amount,
		pi.paid_amount,
		pi.rounded_total - IFNULL(pi.paid_amount, 0) as balance_amount,		
		s.supplier_name as supplier_name
		FROM 
		`tabPurchase Invoice` pi
		LEFT JOIN
		`tabSupplier` s ON pi.supplier = s.name
		WHERE 
		(pi.docstatus = 1 or pi.docstatus = 0) 
		AND pi.credit_purchase = 1 		
		AND pi.posting_date BETWEEN '{0}' and '{1}'		
		ORDER BY 
		pi.posting_date
		""".format(filters.get('from_date'), filters.get('to_date')), as_dict=True)
     
		# data = frappe.db.sql(""" SELECT si.customer, si.name as purchase_invoice_name,si.posting_date as posting_date,si.rounded_total as amount,pi.paid_amount,si.rounded_total - IFNULL(pi.paid_amount,0) as balance_amount,si.delivery_note as delivery_note,si.ship_to_location as ship_to_location FROM `tabSales Invoice` si where (si.docstatus = 1 or si.docstatus=0) and si.credit_sale=1  and si.posting_date BETWEEN '{0}' and '{1}' order by si.posting_date""".format(filters.get('from_date'),filters.get('to_date')),as_dict=True)
	elif filters.get('supplier'):
		data = frappe.db.sql("""
		SELECT 
		pi.name as purchase_invoice_name,
  		pi.supplier_inv_no,
		pi.posting_date as posting_date,
		pi.rounded_total as amount,
		pi.paid_amount,
		pi.rounded_total - IFNULL(pi.paid_amount, 0) as balance_amount,		
		s.supplier_name as supplier_name
		FROM 
		`tabPurchase Invoice` pi
		LEFT JOIN
		`tabSupplier` s ON pi.supplier = s.name
		WHERE 
		(pi.docstatus = 1 or pi.docstatus = 0) 
		AND pi.credit_purchase = 1 
		AND si.supplier = '{0}'				
		ORDER BY 
		pi.posting_date
		""".format(filters.get('supplier')), as_dict=True)
		# data = frappe.db.sql(""" SELECT si.name as purchase_invoice_name,si.posting_date,si.rounded_total as amount,pi.paid_amount,si.rounded_total - IFNULL(pi.paid_amount,0) as balance_amount,si.delivery_note as delivery_note,si.ship_to_location as ship_to_location FROM `tabSales Invoice` si where (si.docstatus = 1 or si.docstatus=0) and si.credit_sale=1 and si.customer = '{}' order by posting_date""".format(filters.get('customer')),as_dict=True)

	else:
		data = frappe.db.sql("""
		SELECT 
		pi.name as purchase_invoice_name,
		pi.supplier_inv_no,
		pi.posting_date as posting_date,
		pi.rounded_total as amount,
		pi.paid_amount,
		pi.rounded_total - IFNULL(pi.paid_amount, 0) as balance_amount,		
		s.supplier_name as supplier_name
		FROM 
		`tabPurchase Invoice` pi
		LEFT JOIN
		`tabSupplier` s ON pi.supplier = s.name
		WHERE 
		(pi.docstatus = 1 or pi.docstatus = 0) 
		AND pi.credit_sale = 1 		
		ORDER BY 
		pi.posting_date
		""", as_dict=True) 
	
	return data

def get_data_supplier_wise(filters):
	data = ""	
 
	if filters.get('supplier') and  filters.get('from_date') and filters.get('to_date'):
     	
  
		# data = frappe.db.sql(""" SELECT si.name as purchase_invoice_name,si.posting_date as posting_date,si.rounded_total as amount,pi.paid_amount,si.rounded_total - IFNULL(pi.paid_amount,0) as balance_amount,si.delivery_note as delivery_note,si.ship_to_location as 'ship_to_location' FROM `tabSales Invoice` si  where (si.docstatus = 1 or si.docstatus=0) and si.credit_sale=1 and si.customer = '{0}' and si.posting_date BETWEEN '{1}' and '{2}'  order by si.posting_date""".format(filters.get('customer'),filters.get('from_date'),filters.get('to_date')),as_dict=True)
		data = frappe.db.sql("""
		SELECT 
		s.supplier_name as supplier,  
		SUM(pi.rounded_total) as amount,
		SUM(pi.paid_amount),
		SUM(pi.rounded_total) - SUM(IFNULL(pi.paid_amount, 0)) as balance_amount				
		FROM 
		`tabPurchase Invoice` pi
		LEFT JOIN
		`tabSupplier` s ON pi.supplier = s.name
		WHERE 
		(pi.docstatus = 1 or pi.docstatus = 0) 
		AND pi.credit_purchase = 1 
		AND pi.supplier = '{0}' 
		AND pi.posting_date BETWEEN '{1}' and '{2}'		
		GROUP BY s.supplier_name
		ORDER BY 
		pi.posting_date
		""".format(filters.get('supplier'), filters.get('from_date'), filters.get('to_date')), as_dict=True)
  
  		# data = frappe.db.sql(""" SELECT si.name as purchase_invoice_name,si.posting_date as posting_date,si.rounded_total as amount,pi.paid_amount,si.rounded_total - IFNULL(pi.paid_amount,0) as balance_amount,si.delivery_note as delivery_note,si.ship_to_location as 'ship_to_location' FROM `tabSales Invoice` si  where si.docstatus = 0 and si.credit_sale=1 and si.customer = '{0}' and si.posting_date BETWEEN '{1}' and '{2}'  order by si.posting_date""".format(filters.get('customer'),filters.get('from_date'),filters.get('to_date')),as_dict=True)
  
	elif filters.get('from_date') and filters.get('to_date'):
		data = frappe.db.sql("""
		SELECT 
		s.supplier_name as supplier,  
		SUM(pi.rounded_total) as amount,
		SUM(pi.paid_amount),
		SUM(pi.rounded_total) - SUM(IFNULL(pi.paid_amount, 0)) as balance_amount				
		FROM 
		`tabPurchase Invoice` pi
		LEFT JOIN
		`tabSupplier` s ON pi.supplier = s.name
		WHERE 
		(pi.docstatus = 1 or pi.docstatus = 0) 
		AND pi.credit_purchase = 1 		
		AND pi.posting_date BETWEEN '{0}' and '{1}'		
		GROUP BY s.supplier_name
		ORDER BY 
		pi.posting_date
		""".format(filters.get('from_date'), filters.get('to_date')), as_dict=True)
     
		# data = frappe.db.sql(""" SELECT si.customer, si.name as purchase_invoice_name,si.posting_date as posting_date,si.rounded_total as amount,pi.paid_amount,si.rounded_total - IFNULL(pi.paid_amount,0) as balance_amount,si.delivery_note as delivery_note,si.ship_to_location as ship_to_location FROM `tabSales Invoice` si where (si.docstatus = 1 or si.docstatus=0) and si.credit_sale=1  and si.posting_date BETWEEN '{0}' and '{1}' order by si.posting_date""".format(filters.get('from_date'),filters.get('to_date')),as_dict=True)
	elif filters.get('supplier'):
		data = frappe.db.sql("""
		SELECT 
		s.supplier_name as supplier,  
		SUM(pi.rounded_total) as amount,
		SUM(pi.paid_amount),
		SUM(pi.rounded_total) - SUM(IFNULL(pi.paid_amount, 0)) as balance_amount				
		FROM 
		`tabPurchase Invoice` pi
		LEFT JOIN
		`tabSupplier` s ON pi.supplier = s.name
		WHERE 
		(pi.docstatus = 1 or pi.docstatus = 0) 
		AND pi.credit_purchase = 1 
		AND si.supplier = '{0}'				
		GROUP BY s.supplier_name
		ORDER BY 
		pi.posting_date
		""".format(filters.get('supplier')), as_dict=True)
		# data = frappe.db.sql(""" SELECT si.name as purchase_invoice_name,si.posting_date,si.rounded_total as amount,pi.paid_amount,si.rounded_total - IFNULL(pi.paid_amount,0) as balance_amount,si.delivery_note as delivery_note,si.ship_to_location as ship_to_location FROM `tabSales Invoice` si where (si.docstatus = 1 or si.docstatus=0) and si.credit_sale=1 and si.customer = '{}' order by posting_date""".format(filters.get('customer')),as_dict=True)

	else:
		data = frappe.db.sql("""
		SELECT 
		s.supplier_name as supplier,  
		SUM(pi.rounded_total) as amount,
		SUM(pi.paid_amount),
		SUM(pi.rounded_total) - SUM(IFNULL(pi.paid_amount, 0)) as balance_amount				
		FROM 
		`tabPurchase Invoice` pi
		LEFT JOIN
		`tabSupplier` s ON pi.supplier = s.name
		WHERE 
		(pi.docstatus = 1 or pi.docstatus = 0) 
		AND pi.credit_sale = 1 		
		GROUP BY p.supplier_name
		ORDER BY 
		pi.posting_date
		""", as_dict=True) 
	
	return data
def get_columns():
	return [
		{		
			"fieldname": "purchase_invoice_name",
			"fieldtype": "Link",
			"label": "Invoice No",
			"options": "Purchase Invoice",
			"width": 150,	
		},
  		{
			"fieldname": "supplier_inv_no",
			"fieldtype": "Data",
			"label": "Supplier Invoice No",			
			"width": 150,
		},
		{		
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"label": "Date",
			"width": 120,	
		},
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

def get_columns_with_supplier():
	return [
		{
		
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"label": "Supplier",			
			"width": 150,	
		},
  		{		
			"fieldname": "purchase_invoice_name",
			"fieldtype": "Link",
			"label": "Invoice No",
			"options": "Purchase Invoice",
			"width": 150,	
		},
		{
			"fieldname": "supplier_inv_no",
			"fieldtype": "Data",
			"label": "Supplier Invoice No",			
			"width": 150,
		},    
		{		
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"label": "Date",
			"width": 120,	
		},		
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
def get_columns_for_supplier_group():
	return [
		{
		
			"fieldname": "supplier",
			"fieldtype": "Data",
			"label": "Supplier",			
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
