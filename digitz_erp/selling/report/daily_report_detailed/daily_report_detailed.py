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
            "fieldname": "total_sales",
            "label": "Total Sales",
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
            "fieldname": "total_credit_sales",
            "label": "Credit Sales",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "total_sales_return",
            "label": "Total Sales Return",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "total_cash_sales_return",
            "label": "Cash Sales Return",
            "fieldtype": "Currency",
            "width": 120
        },       
        {
            "fieldname": "total_credit_sales_return",
            "label": "Credit Sales Return",
            "fieldtype": "Currency",
            "width": 120
        },      
        {
            "fieldname": "total_purchase",
            "label": "Total Purchase",
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
            "fieldname": "total_purchase_return",
            "label": "Total Purchase Return",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "total_credit_purchase_return",
            "label": "Credit Purchase Return",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "total_cash_purchase_return",
            "label": "Cash Purchase Return",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "total_cash_receipts",
            "label": "Cash Receipt",
            "fieldtype": "Currency",
            "width": 120            
        },
        {
            "fieldname": "total_bank_receipts",
            "label": "Bank Receipt",
            "fieldtype": "Currency",
            "width": 120            
        },
        {
            "fieldname": "total_receipts",
            "label": "Total Receipt",
            "fieldtype": "Currency",
            "width": 120            
        },
         {
            "fieldname": "total_cash_payments",
            "label": "Cash Payment",
            "fieldtype": "Currency",
            "width": 120            
        },
        {
            "fieldname": "total_bank_payments",
            "label": "Bank Payment",
            "fieldtype": "Currency",
            "width": 120            
        },
        {
            "fieldname": "total_payments",
            "label": "Total Payment",
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
# Sales
def get_total_cash_sales(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_sales = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0)  as total_sales
	FROM `tabSales Invoice`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus<2 AND credit_Sale=0
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_sales[0].total_sales if total_sales[0].total_sales else 0

def get_total_credit_sales(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_sales = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0) as total_sales
	FROM `tabSales Invoice`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus<2 AND credit_Sale=1
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_sales[0].total_sales if total_sales[0].total_sales else 0

def get_total_sales(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_sales = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0) as total_sales
	FROM `tabSales Invoice`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus<2 
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_sales[0].total_sales if total_sales[0].total_sales else 0

# Sales Return
def get_total_cash_sales_return(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_sales = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0)  as total_sales
	FROM `tabSales Return`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus<2 AND credit_Sale=0
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_sales[0].total_sales if total_sales[0].total_sales else 0

def get_total_credit_sales_return(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_sales = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0) as total_sales
	FROM `tabSales Return`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus<2 AND credit_Sale=1
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_sales[0].total_sales if total_sales[0].total_sales else 0

def get_total_sales_return(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_sales = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0) as total_sales
	FROM `tabSales Return`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus<2 
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_sales[0].total_sales if total_sales[0].total_sales else 0

# Purchase
def get_total_cash_purchase(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_purchase = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0) as total_purchase
	FROM `tabPurchase Invoice`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus <2 and credit_purchase=0
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_purchase[0].total_purchase if total_purchase[0].total_purchase else 0

def get_total_credit_purchase(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_purchase = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0)  as total_purchase
	FROM `tabPurchase Invoice`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus <2 and credit_purchase=1
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_purchase[0].total_purchase if total_purchase[0].total_purchase else 0

def get_total_purchase(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_purchase = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0)  as total_purchase
	FROM `tabPurchase Invoice`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus <2 
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_purchase[0].total_purchase if total_purchase[0].total_purchase else 0

# Purchase Return
def get_total_cash_purchase_return(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_purchase = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0) as total_purchase
	FROM `tabPurchase Return`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus <2 and credit_purchase=0
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_purchase[0].total_purchase if total_purchase[0].total_purchase else 0

def get_total_credit_purchase_return(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_purchase = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0)  as total_purchase
	FROM `tabPurchase Return`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus <2 and credit_purchase=1
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_purchase[0].total_purchase if total_purchase[0].total_purchase else 0

def get_total_purchase_return(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")

	conditions = "AND warehouse = %(warehouse)s" if warehouse else ""

	total_purchase = frappe.db.sql(f"""
	SELECT COALESCE(SUM(rounded_total), 0)  as total_purchase
	FROM `tabPurchase Return`
	WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s and docstatus <2 
	{conditions}
	""", {"from_date": from_date, "to_date": to_date, "warehouse": warehouse}, as_dict=True)

	return total_purchase[0].total_purchase if total_purchase[0].total_purchase else 0

# Receipts
def get_total_cash_receipts(filters):  
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    print("before warehouse filter")
    warehouse = filters.get("warehouse", None)
    print("warehouse")
    print(warehouse)
    sql = """
    SELECT COALESCE(SUM(rd.amount), 0) as total_receipts
    FROM `tabReceipt Entry Detail` AS rd
    INNER JOIN `tabReceipt Entry` AS re ON rd.parent = re.name
    INNER JOIN `tabPayment Mode` AS pm ON pm.name = re.payment_mode 
    WHERE re.posting_date BETWEEN '{from_date}' AND '{to_date}' AND pm.mode in ('Cash') AND re.docstatus < 2 AND re.warehouse = '{warehouse}'
    """.format(from_date=from_date, to_date=to_date, warehouse=warehouse)

    frappe.db.sql(sql, as_dict=True)
    
    total_receipts = frappe.db.sql(sql, as_dict=True)
    
    return total_receipts[0].total_receipts if total_receipts and total_receipts[0].total_receipts else 0

def get_total_bank_receipts(filters):  
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    warehouse = filters.get("warehouse")
        
    total_receipts = frappe.db.sql(f"""
    SELECT COALESCE(SUM(rd.amount), 0) as total_receipts
    FROM `tabReceipt Entry Detail` AS rd
    INNER JOIN `tabReceipt Entry` AS re ON rd.parent = re.name
    INNER JOIN `tabPayment Mode` AS pm on pm.name= re.payment_mode 
    WHERE re.posting_date BETWEEN '{from_date}' AND '{to_date}' AND pm.mode not in ('Cash') AND re.docstatus<2 AND re.warehouse = '{warehouse}'
    """.format(from_date= from_date, to_date=to_date, warehouse=warehouse), as_dict=True)

    return total_receipts[0].total_receipts if  total_receipts[0].total_receipts else 0 

def get_total_receipts(filters):  
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    warehouse = filters.get("warehouse")
    
    total_receipts = frappe.db.sql(f"""
        SELECT COALESCE(SUM(rd.amount), 0) as total_receipts
        FROM `tabReceipt Entry Detail` AS rd
        INNER JOIN `tabReceipt Entry` AS re ON rd.parent = re.name
        WHERE re.posting_date BETWEEN '{from_date}' AND '{to_date}' AND re.docstatus<2 AND re.warehouse='{warehouse}'        
        """.format(from_date= from_date, to_date=to_date, warehouse=warehouse), as_dict=True)

    return total_receipts[0].total_receipts if  total_receipts[0].total_receipts else 0   
# Payments
def get_total_cash_payments(filters):  
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    warehouse = filters.get("warehouse")
    
    total_receipts = frappe.db.sql(f"""
        SELECT COALESCE(SUM(rd.amount), 0) as total_receipts
        FROM `tabPayment Entry Detail` AS rd
        INNER JOIN `tabPayment Entry` AS re ON rd.parent = re.name
        INNER JOIN `tabPayment Mode` AS pm on pm.name= re.payment_mode 
        WHERE re.posting_date BETWEEN '{from_date}' AND '{to_date}' AND pm.mode in ('Cash') AND re.docstatus <2 AND re.warehouse='{warehouse}'
        """.format(from_date= from_date, to_date=to_date, warehouse=warehouse), as_dict=True)
    return total_receipts[0].total_receipts if  total_receipts[0].total_receipts else 0

def get_total_bank_payments(filters):  
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    warehouse = filters.get("warehouse")
       
    total_receipts = frappe.db.sql(f"""
    SELECT COALESCE(SUM(rd.amount), 0) as total_receipts
    FROM `tabPayment Entry Detail` AS rd
    INNER JOIN `tabPayment Entry` AS re ON rd.parent = re.name
    INNER JOIN `tabPayment Mode` AS pm on pm.name= re.payment_mode 
    WHERE re.posting_date BETWEEN '{from_date}' AND '{to_date}' AND pm.mode not in ('Cash') AND re.docstatus<2 AND re.warehouse='{warehouse}'
    """.format(from_date= from_date, to_date=to_date, warehouse=warehouse), as_dict=True)

    return total_receipts[0].total_receipts if  total_receipts[0].total_receipts else 0 

def get_total_payments(filters):  
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    warehouse = filters.get("warehouse")
   
    total_receipts = frappe.db.sql(f"""
    SELECT COALESCE(SUM(rd.amount), 0) as total_receipts
    FROM `tabPayment Entry Detail` AS rd
    INNER JOIN `tabPayment Entry` AS re ON rd.parent = re.name
    WHERE re.posting_date BETWEEN '{from_date}' AND '{to_date}' AND re.docstatus<2 AND re.warehouse ='{warehouse}'        
    """.format(from_date= from_date, to_date=to_date, warehouse=warehouse), as_dict=True)

    return total_receipts[0].total_receipts if  total_receipts[0].total_receipts else 0   


def calculate_total_balance(cash_sales, cash_purchase,		cash_sales_return, cash_purchase_return,cash_receipt, cash_payment):
    return cash_sales-cash_purchase -cash_sales_return + cash_purchase_return +cash_receipt - cash_payment

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
       
    # Grand totals
    grand_total_sales = 0
    grand_total_cash_sales = 0
    grand_total_credit_sales = 0
    
    grand_total_sales_return = 0
    grand_total_cash_sales_return = 0
    grand_total_credit_sales_return = 0
    
    grand_total_purchase = 0
    grand_total_cash_purchase = 0
    grand_total_credit_purchase = 0
    
    grand_total_purchase_return = 0
    grand_total_cash_purchase_return = 0
    grand_total_credit_purchase_return = 0
    
    grand_total_receipts = 0
    grand_total_cash_receipts = 0
    grand_total_bank_receipts = 0
    
    grand_total_payments = 0
    grand_total_cash_payments = 0
    grand_total_bank_payments = 0
    
    grand_total_balance_cash = 0
    
    for warehouse in warehouses:
        warehouse_name = warehouse.name
        warehouse_filters = filters.copy()
        warehouse_filters["warehouse"] = warehouse_name
        
        # Sales
        total_sales = get_total_sales(warehouse_filters)
        total_cash_sales = get_total_cash_sales(warehouse_filters)
        total_credit_sales = get_total_credit_sales(warehouse_filters)
        
        # Sales Return
        total_sales_return = get_total_sales_return(warehouse_filters)
        total_cash_sales_return = get_total_cash_sales_return(warehouse_filters)
        total_credit_sales_return = get_total_credit_sales_return(warehouse_filters)
        
        # 
        total_cash_purchase = get_total_cash_purchase(warehouse_filters)
        total_credit_purchase = get_total_credit_purchase(warehouse_filters)
        total_purchase = get_total_purchase(warehouse_filters)
        
        
        # Purchase Return
        total_cash_purchase_return = get_total_cash_purchase_return(warehouse_filters)
        total_credit_purchase_return = get_total_credit_purchase_return(warehouse_filters)
        total_purchase_return = get_total_purchase_return(warehouse_filters)
        
        # Receipts
        total_cash_receipts = get_total_cash_receipts(warehouse_filters)
        total_bank_receipts = get_total_bank_receipts(warehouse_filters)
        total_receipts = get_total_receipts(warehouse_filters)
        
        # Payments
        total_cash_payments = get_total_cash_payments(warehouse_filters)
        total_bank_payments = get_total_bank_payments(warehouse_filters)
        total_payments = get_total_payments(warehouse_filters)
        
        
        total_balance_cash = calculate_total_balance(total_cash_sales, total_cash_purchase, total_cash_sales_return, total_cash_purchase_return, total_cash_receipts, total_cash_payments)
        
        cash_sales_data = get_cash_sales_data(warehouse_filters)
        credit_sales_data = get_credit_sales_data(warehouse_filters)
        cash_sales_return_data = get_cash_sales_return_data(warehouse_filters)
        credit_sales_return_data = get_credit_sales_return_data(warehouse_filters)
        
        cash_purchase_data = get_cash_purchase_data(warehouse_filters)
        credit_purchase_data = get_credit_purchase_data(warehouse_filters)
        cash_purchase_return_data = get_cash_purchase_return_data(warehouse_filters)
        credit_purchase_return_data = get_credit_purchase_return_data(warehouse_filters)
        
        cash_receipt_data = get_cash_receipt_data(warehouse_filters)        
        bank_receipt_data = get_bank_receipt_data(warehouse_filters)
               
        warehouse_data = {
            "warehouse": warehouse_name,
            "total_sales": total_sales,
            "total_cash_sales": total_cash_sales,
            "total_credit_sales": total_credit_sales,
            "total_sales_return": total_sales_return,
            "total_cash_sales_return": total_cash_sales_return,
            "total_credit_sales_return": total_credit_sales_return,
            "total_purchase": total_purchase,
            "total_cash_purchase": total_cash_purchase,            
            "total_credit_purchase": total_credit_purchase,
            "total_purchase_return": total_purchase_return,
            "total_cash_purchase_return": total_cash_purchase_return,            
            "total_credit_purchase_return": total_credit_purchase_return,
            "total_receipts": total_receipts,
            "total_cash_receipts": total_cash_receipts,
            "total_bank_receipts": total_bank_receipts,
            "total_payments": total_payments,
            "total_cash_payments": total_cash_payments,
            "total_bank_payments": total_bank_payments,                        
            "total_balance_cash": total_balance_cash,
            "cash_sales_data":cash_sales_data,
            "credit_sales_data": credit_sales_data,
            "cash_saes_return_data":cash_sales_return_data,
            "credit_sales_return_data": credit_sales_return_data,
            "cash_purchase_data": cash_purchase_data,
            "credit_purchase_data": credit_purchase_data,
            "cash_purchase_return_data": cash_purchase_return_data,
            "credit_purchase_return_data": credit_purchase_return_data, 
            "cash_receipt_data": cash_receipt_data,
            "bank_receipt_data": bank_receipt_data
        }
        data.append(warehouse_data)
        
        print("total cash receipts")
        print(total_cash_receipts)
        
    
        if not filters.get("warehouse"):           
            grand_total_cash_sales += total_cash_sales
            grand_total_credit_sales += total_credit_sales
            grand_total_sales += total_sales
            
            grand_total_cash_sales_return += total_cash_sales_return
            grand_total_credit_sales_return += total_credit_sales_return
            grand_total_sales_return += total_sales_return            
            
            grand_total_cash_purchase += total_cash_purchase
            grand_total_credit_purchase += total_credit_purchase
            grand_total_purchase += total_purchase
            
            grand_total_cash_purchase_return += total_cash_purchase_return
            grand_total_credit_purchase_return += total_credit_purchase_return
            grand_total_purchase_return += total_purchase_return
            
            grand_total_receipts += total_receipts
            grand_total_cash_receipts += total_cash_receipts
            grand_total_bank_receipts += total_bank_receipts
            
            grand_total_payments += total_payments
            grand_total_cash_payments += total_cash_payments
            grand_total_bank_payments += total_bank_payments
            
            grand_total_balance_cash += total_balance_cash
      
    warehouse_data = {
            "warehouse": "Totals",
            "total_sales": grand_total_sales,
            "total_cash_sales": grand_total_cash_sales,
            "total_credit_sales": grand_total_credit_sales,
            
            "total_sales_return": grand_total_sales_return,
            "total_cash_sales_return": grand_total_cash_sales_return,
            "total_credit_sales_return": grand_total_credit_sales_return,
            
            "total_purchases": grand_total_purchase,
            "total_cash_purchase": grand_total_cash_purchase,
            "total_credit_purchase": grand_total_credit_purchase,
            
            "total_purchase_return": grand_total_purchase_return,
            "total_cash_purchase_return": grand_total_cash_purchase_return,
            "total_credit_purchase_return": grand_total_credit_purchase_return,
            
            "total_receipts" : grand_total_receipts,
            "total_cash_receipts": grand_total_cash_receipts,
            "total_bank_receipts" : grand_total_bank_receipts,
            
            "total_receipts" : grand_total_receipts,
            "total_cash_receipts": grand_total_cash_receipts,
            "total_bank_receipts" : grand_total_bank_receipts,
            
            "total_balance_cash": grand_total_balance_cash
        }    
    data.append(warehouse_data)   
    print("data")
    print(data)
       
    return data

def get_cash_sales_data(filters):
    
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")
	sql = """
		SELECT name,customer_name,rounded_total FROM `tabSales Invoice` ts WHERE posting_date BETWEEN '{from_date}' AND '{to_date}' and docstatus<2 AND credit_Sale=0
		AND warehouse= '{warehouse}'""".format(from_date= from_date, to_date=to_date, warehouse=warehouse)
  
	detail_data =frappe.db.sql(sql, as_dict = True)
 
	return detail_data

def get_credit_sales_data(filters):
    
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")
	sql = """
		SELECT name,customer_name,rounded_total FROM `tabSales Invoice` ts WHERE posting_date BETWEEN '{from_date}' AND '{to_date}' and docstatus<2 AND credit_Sale=1
		AND warehouse= '{warehouse}'""".format(from_date= from_date, to_date=to_date, warehouse=warehouse)
  
	detail_data =frappe.db.sql(sql, as_dict = True)
 
	return detail_data

def get_cash_sales_return_data(filters):
    
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")
	sql = """
		SELECT name,customer_name,rounded_total FROM `tabSales Return` ts WHERE posting_date BETWEEN '{from_date}' AND '{to_date}' and docstatus<2 AND credit_Sale=0
		AND warehouse= '{warehouse}'""".format(from_date= from_date, to_date=to_date, warehouse=warehouse)
  
	detail_data =frappe.db.sql(sql, as_dict = True)
 
	return detail_data

def get_credit_sales_return_data(filters):
    
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")
	sql = """
		SELECT name,customer_name,rounded_total FROM `tabSales Return` ts WHERE posting_date BETWEEN '{from_date}' AND '{to_date}' and docstatus<2 AND credit_Sale=1
		AND warehouse= '{warehouse}'""".format(from_date= from_date, to_date=to_date, warehouse=warehouse)
  
	detail_data =frappe.db.sql(sql, as_dict = True)
 
	return detail_data

def get_cash_purchase_data(filters):
    
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")
	sql = """
		SELECT name,supplier,rounded_total FROM `tabPurchase Invoice` ts WHERE posting_date BETWEEN '{from_date}' AND '{to_date}' and docstatus<2 AND credit_purchase=0
		AND warehouse= '{warehouse}'""".format(from_date= from_date, to_date=to_date, warehouse=warehouse)
  
	detail_data =frappe.db.sql(sql, as_dict = True)
 
	return detail_data

def get_credit_purchase_data(filters):
    
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")
	sql = """
		SELECT name,supplier,rounded_total FROM `tabPurchase Invoice` ts WHERE posting_date BETWEEN '{from_date}' AND '{to_date}' and docstatus<2 AND credit_purchase=1
		AND warehouse= '{warehouse}'""".format(from_date= from_date, to_date=to_date, warehouse=warehouse)
  
	detail_data =frappe.db.sql(sql, as_dict = True)
 
	return detail_data

def get_cash_purchase_return_data(filters):
    
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")
	sql = """
		SELECT name,supplier,rounded_total FROM `tabPurchase Return` ts WHERE posting_date BETWEEN '{from_date}' AND '{to_date}' and docstatus<2 AND credit_purchase=0
		AND warehouse= '{warehouse}'""".format(from_date= from_date, to_date=to_date, warehouse=warehouse)
  	
	detail_data =frappe.db.sql(sql, as_dict = True)
 
	return detail_data

def get_credit_purchase_return_data(filters):
    
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	warehouse = filters.get("warehouse")
	sql = """
		SELECT name,supplier,rounded_total FROM `tabPurchase Return` ts WHERE posting_date BETWEEN '{from_date}' AND '{to_date}' and docstatus<2 AND credit_purchase=1
		AND warehouse= '{warehouse}'""".format(from_date= from_date, to_date=to_date, warehouse=warehouse)
  
	detail_data =frappe.db.sql(sql, as_dict = True)
 
	return detail_data

def get_cash_receipt_data(filters):

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")   
	warehouse = filters.get("warehouse")

    # With Allocation Union Without Allocation
	sql="""SELECT re.name as 'rcpt_no', c.customer_name AS 'account',
		CASE WHEN ra.reference_type='Sales Invoice' THEN 'SI' ELSE ra.reference_type END AS 'ref_type',
		ra.reference_name AS 'ref',
		ROUND(ra.paying_amount, 2) AS 'amount'
		FROM `tabReceipt Allocation` ra
		INNER JOIN `tabReceipt Entry` re on re.name= ra.parent
		INNER JOIN `tabCustomer` c ON c.name = ra.customer
		INNER JOIN `tabPayment Mode` AS pm ON pm.name = re.payment_mode
		WHERE re.posting_date BETWEEN '{from_date}' AND '{to_date}' AND re.docstatus < 2 AND re.warehouse = '{warehouse}'  AND pm.mode in ('Cash')

		UNION  

		SELECT re.name as 'rcpt_no',case when c.customer_name is null then rd.account else c.customer_name end  AS 'account',
		'' AS 'ref_type',
		'' AS 'ref',
		re.amount AS 'amount'
		FROM `tabReceipt Entry Detail` rd
		INNER JOIN `tabReceipt Entry` AS re ON re.name = rd.parent
		INNER JOIN `tabPayment Mode` AS pm ON pm.name = re.payment_mode	
		LEFT OUTER JOIN `tabCustomer` c on c.name = rd.customer
		WHERE re.posting_date BETWEEN '{from_date}' AND '{to_date}' AND re.docstatus < 2 AND re.warehouse = '{warehouse}' AND (rd.reference_type IS NULL OR rd.reference_type='') AND pm.mode in ('Cash')
		""".format(from_date=from_date, to_date=to_date, warehouse=warehouse)
  
	receipt_detail_data = frappe.db.sql(sql, as_dict=True)
	print("receipt_detail_data")
	print(receipt_detail_data)
	return receipt_detail_data

def get_bank_receipt_data(filters):

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")   
	warehouse = filters.get("warehouse")

    # With Allocation Union Without Allocation
	sql="""SELECT re.name as 'rcpt_no', c.customer_name AS 'account',
		CASE WHEN ra.reference_type='Sales Invoice' THEN 'SI' ELSE ra.reference_type END AS 'ref_type',
		ra.reference_name AS 'ref',
		ROUND(ra.paying_amount, 2) AS 'amount'
		FROM `tabReceipt Allocation` ra
		INNER JOIN `tabReceipt Entry` re on re.name= ra.parent
		INNER JOIN `tabCustomer` c ON c.name = ra.customer
		INNER JOIN `tabPayment Mode` AS pm ON pm.name = re.payment_mode
		WHERE re.posting_date BETWEEN '{from_date}' AND '{to_date}' AND re.docstatus < 2 AND re.warehouse = '{warehouse}'  AND pm.mode not in ('Cash')

		UNION  

		SELECT re.name as 'rcpt_no',case when c.customer_name is null then rd.account else c.customer_name end  AS 'account',
		'' AS 'ref_type',
		'' AS 'ref',
		re.amount AS 'amount'
		FROM `tabReceipt Entry Detail` rd
		INNER JOIN `tabReceipt Entry` AS re ON re.name = rd.parent
		INNER JOIN `tabPayment Mode` AS pm ON pm.name = re.payment_mode	
		LEFT OUTER JOIN `tabCustomer` c on c.name = rd.customer
		WHERE re.posting_date BETWEEN '{from_date}' AND '{to_date}' AND re.docstatus < 2 AND re.warehouse = '{warehouse}' AND (rd.reference_type IS NULL OR rd.reference_type='') AND pm.mode not in ('Cash')
		""".format(from_date=from_date, to_date=to_date, warehouse=warehouse)
  
	receipt_detail_data = frappe.db.sql(sql, as_dict=True)
	print("receipt_detail_data")
	print(receipt_detail_data)
	return receipt_detail_data




	
