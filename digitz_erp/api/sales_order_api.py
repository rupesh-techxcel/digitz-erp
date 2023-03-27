import frappe
from frappe.utils import get_datetime

@frappe.whitelist()

@frappe.whitelist()
def get_sales_invoice_exists(sales_order):    
   return frappe.db.exists('Sales Invoice', {'sales_order': sales_order})

@frappe.whitelist()
def get_delivery_note_exists(sales_order):    
   return frappe.db.exists('Delivery Note', {'sales_order': sales_order})