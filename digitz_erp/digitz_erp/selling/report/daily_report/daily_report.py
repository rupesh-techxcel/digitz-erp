# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import data


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)    
    
    return columns, data, None, None

def get_default_warehouse_for_user():
    
      user_default_warehouse = frappe.get_value('User Warehouse', {'user': frappe.session.user, 'is_default':1}, ['warehouse'], as_dict =1 )
      return user_default_warehouse
    
def get_columns():
    return [
        {
            "fieldname": "warehouse",
            "label": "Warehouse",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "total_credit_sales",
            "label": "Credit Sales",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "total_cash_sales",
            "label": "Cash Sales",
            "fieldtype": "Currency",
            "width": 120
        },

        {
            "fieldname": "total_credit_purchase",
            "label": "Credit Purchase",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "total_cash_purchase",
            "label": "Cash Purchase",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "total_receipt",
            "label": "Receipt",
            "fieldtype": "Currency",
            "width": 120            
        },
        {
            "fieldname": "total_balance_cash",
            "label": "Balance Cash",
            "fieldtype": "Currency",
            "width": 120            
        },
    ]

def get_total_cash_sales(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_sales = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0)  as total_sales
	FROM `tabSales Invoice`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus!=2 AND credit_Sale=0
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_sales[0].total_sales if total_sales[0].total_sales else 0

def get_total_receipts(filters):  
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    warehouse = filters.get("warehouse")
    conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

    total_receipts = frappe.db.sql(f"""
        SELECT COALESCE(SUM(rd.amount), 0) as total_receipts
        FROM `tabReceipt Entry Detail` AS rd
        INNER JOIN `tabReceipt Entry` AS re ON rd.parent = re.name
        WHERE re.posting_date BETWEEN %(from_date)s AND %(to_date)s
        {conditions}
    """, {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

    return total_receipts[0].total_receipts if  total_receipts[0].total_receipts else 0   

def get_total_credit_sales(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_sales = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0) as total_sales
	FROM `tabSales Invoice`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus!=2 AND credit_Sale=1
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_sales[0].total_sales if total_sales[0].total_sales else 0

def get_total_credit_purchase(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_purchase = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0)  as total_purchase
	FROM `tabPurchase Invoice`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus !=2 and credit_purchase=1
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_purchase[0].total_purchase if total_purchase[0].total_purchase else 0

def get_total_cash_purchase(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_purchase = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0) as total_purchase
	FROM `tabPurchase Invoice`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus !=2 and credit_purchase=0
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_purchase[0].total_purchase if total_purchase[0].total_purchase else 0

def calculate_total_balance(cash_sales, cash_purchase, receipts):
    return cash_sales - cash_purchase + receipts

def calculate_grand_total(data):
    grand_total = {
        "warehouse": "Grand Total",
        "total_cash_sales": sum(item.get("total_cash_sales", 0) for item in data),
        "total_cash_purchase": sum(item.get("total_cash_purchase", 0) for item in data),
        "total_credit_sales": sum(item.get("total_credit_sales", 0) for item in data),
        "total_credit_purchase": sum(item.get("total_credit_purchase", 0) for item in data),
        "total_receipts": sum(item.get("total_receipts", 0) for item in data),
        "total_balance_cash": sum(item.get("total_balance_cash", 0) for item in data)
    }
    data.append(grand_total)

def get_data(filters):
    
    warehouses = frappe.get_all("Warehouse", fields=["name"])
        # Get the list of all warehouses
    all_warehouses = frappe.get_all("Warehouse", fields=["name"])
    
    # Check if a warehouse filter is provided
    warehouse_filter = filters.get("warehouse")
    
    # If a warehouse filter is provided, filter the list of warehouses accordingly
    if warehouse_filter:
        warehouses = [wh for wh in all_warehouses if wh.name == warehouse_filter]
    else:
        # If no filter is provided, use all warehouses
        warehouses = all_warehouses
    
    data = []

    grand_total_cash_sales = 0
    grand_total_credit_sales = 0
    grand_total_cash_purchase = 0
    grand_total_credit_purchase = 0
    grand_total_receipts = 0
    grand_total_balance_cash = 0
    
    for warehouse in warehouses:
        warehouse_name = warehouse.name
        warehouse_filters = filters.copy()
        warehouse_filters["warehouse"] = warehouse_name
        
        total_cash_sales = get_total_cash_sales(warehouse_filters)
        total_credit_sales = get_total_credit_sales(warehouse_filters)
        total_cash_purchase = get_total_cash_purchase(warehouse_filters)
        total_credit_purchase = get_total_credit_purchase(warehouse_filters)
        total_receipts = get_total_receipts(warehouse_filters)       
        
        total_balance_cash = calculate_total_balance(total_cash_sales, total_cash_purchase, total_receipts)      
        
        warehouse_data = {
            "warehouse": warehouse_name,
            "total_cash_sales": total_cash_sales,
            "total_cash_purchase": total_cash_purchase,
            "total_credit_sales": total_credit_sales,
            "total_credit_purchase": total_credit_purchase,
            "total_receipts": total_receipts,
            "total_balance_cash": total_balance_cash
        }
        data.append(warehouse_data)
        
        if not filters.get("warehouse"):           
            grand_total_cash_sales += total_cash_sales
            grand_total_credit_sales += total_credit_sales
            grand_total_cash_purchase += total_cash_purchase
            grand_total_credit_purchase += total_credit_purchase
            grand_total_receipts += total_receipts
            grand_total_balance_cash += total_balance_cash

    if not filters.get("warehouse"):    
        warehouse_data = {
            "warehouse": "Totals",
            "total_cash_sales": grand_total_cash_sales,
            "total_cash_purchase": grand_total_cash_purchase,
            "total_credit_sales": grand_total_credit_sales,
            "total_credit_purchase": grand_total_credit_purchase,
            "total_receipts": grand_total_receipts,
            "total_balance_cash": grand_total_balance_cash
        }    
        data.append(warehouse_data)   
    
    return data
