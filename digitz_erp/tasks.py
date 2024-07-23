import frappe

def re_post_stock_ledgers():
    frappe.call('digitz_erp.api.stock_update.re_post_stock_ledgers')