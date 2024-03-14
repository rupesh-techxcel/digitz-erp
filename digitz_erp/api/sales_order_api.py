import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_sales_invoice_exists(sales_order):    
   return frappe.db.exists('Sales Invoice', {'sales_order': sales_order})

@frappe.whitelist()
def get_delivery_note_exists(sales_order):    
   return frappe.db.exists('Delivery Note', {'sales_order': sales_order})

@frappe.whitelist()
def check_and_update_sales_order_status(document_name, doctype):
   sales_orders_query =""
   
   if(doctype == "Sales Invoice"):
      sales_orders_query = """select sales_order from `tabSales Invoice Sales Orders" where parent=%s"""
   
   elif doctype == "Delivery Note":
      sales_orders_query = """select sales_order from `tabDelivery Note Invoice Sales Orders" where parent=%s"""
   
   if(sales_orders_query !=""):
      
      sales_orders = frappe.db.sql(sales_orders_query,(document_name),as_dict = True)
         
      for sales_order_name in sales_orders:
      
         sql_query = """
         SELECT `name` FROM `tabSales Order Item`
         WHERE `parent` = %s
         """
         try:
            sales_order_items = frappe.db.sql(sql_query, sales_order_name, as_dict=True)
            
            sold_any = False
            at_least_one_partial_sale = False
            excess_allocation = False

            for so_item_dict in sales_order_items:
                  so_item_name = so_item_dict['name']
                  so_item = frappe.get_doc("Sales Order Item", so_item_name)
                  
                  if so_item.qty_sold_in_base_unit and so_item.qty_sold_in_base_unit > 0:
                     sold_any = True
                     if so_item.qty_sold_in_base_unit < so_item.qty_in_base_unit:
                        at_least_one_partial_sale = True
                     
                     # Check for excess allocation
                     if so_item.qty_sold_in_base_unit > so_item.qty_in_base_unit:
                        excess_allocation = True                
                        
            if not sold_any:
                  frappe.db.set_value("Sales Order", sales_order_name, "order_status", "Pending")
                  
            elif at_least_one_partial_sale:
                  frappe.db.set_value("Sales Order", sales_order_name, "order_status", "Partial")
            else:
                  frappe.db.set_value("Sales Order", sales_order_name, "order_status", "Completed")
                  
            if excess_allocation:
                  frappe.msgprint(f"Warning: Sales Order {sales_order_name} contains one or more items with excess allocation.")
                  print("message shown and continues...")

         except Exception:
            raise  # This will re-raise the last exception

