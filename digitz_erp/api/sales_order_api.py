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

@frappe.whitelist()
def update_sales_order_quantities_on_update(doc_si_or_do, forDeleteOrCancel=False):
        for item in doc_si_or_do.items:
            if not item.sales_order_item_reference_no:
                continue
            else:
                              
                total_quantity_sold_in_other_docs = 0
                total_quantity_sold = 0
                
                if doc_si_or_do.doctype == "Sales Invoice":
                   
                  total_quantity_sold_in_other_docs = frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_used_qty from `tabSales Invoice Item` sinvi inner join `tabSales Invoice` sinv on sinvi.parent= sinv.name WHERE sinvi.sales_order_item_reference_no=%s AND sinv.name !=%s and sinv.docstatus<2""",(item.sales_order_item_reference_no, doc_si_or_do.name))[0][0]
                  
                  total_quantity_sold_in_do = frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_used_qty from `tabDelivery Note Item` dinvi inner join `tabDelivery Note` dinv on dinvi.parent= dinv.name WHERE dinvi.sales_order_item_reference_no=%s and sinv.docstatus<2""",(item.sales_order_item_reference_no))[0][0]
                  
                  total_quantity_sold = (total_quantity_sold_in_other_docs if total_quantity_sold_in_other_docs else 0) + (total_quantity_sold_in_do if total_quantity_sold_in_do else 0)
                
                if doc_si_or_do.doctype == "Delivery Note":
                   
                  total_quantity_sold_in_si= frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_used_qty from `tabSales Invoice Item` sinvi inner join `tabSales Invoice` sinv on sinvi.parent= sinv.name WHERE sinvi.sales_order_item_reference_no=%s and sinv.docstatus<2""",(item.sales_order_item_reference_no, doc_si_or_do.name))[0][0]

                  total_quantity_sold_in_other_docs = frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_used_qty from `tabDelivery Note Item` dinvi inner join `tabDelivery Note` dinv on dinvi.parent= dinv.name WHERE dinvi.sales_order_item_reference_no=%s and dinv.name!=%s and dinv.docstatus<2""",(item.sales_order_item_reference_no, doc_si_or_do.name))[0][0]
                  
                  total_quantity_sold = (total_quantity_sold_in_other_docs if total_quantity_sold_in_other_docs else 0) + (total_quantity_sold_in_si if total_quantity_sold_in_si else 0)
               
                total_returned_qty_for_the_si_item = frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_returned_qty from `tabSales Return Item` sreti inner join `tabSales Return` sret on sreti.parent= sret.name WHERE sreti.si_item_reference in (select name from `tabSales Invoice Item` sit where sit.sales_order_item_reference_no=%s) and sret.docstatus<2""",(item.po_item_reference))[0][0]
                
                total_quantity_sold = total_quantity_sold - (total_returned_qty_for_the_si_item if total_returned_qty_for_the_si_item else 0)   + (item.qty_in_base_unit if not forDeleteOrCancel else 0)
                  
                so_item = frappe.get_doc("Sales Order Item", item.sales_order_item_reference_no)

                so_item.qty_sold_in_base_unit = total_quantity_sold 
                
                so_item.save()
                po_reference_any = True

        if(po_reference_any):
            frappe.msgprint("Purchased Qty of items in the corresponding purchase Order updated successfully", indicator= "green", alert= True)

