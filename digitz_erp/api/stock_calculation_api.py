import frappe

@frappe.whitelist()
def cancel_delivery_note(delivery_note):
    do = frappe.get_doc('Delivery Note',delivery_note)
    do.cancel()


def add_stock_for_purchase_receipt(item, warehouse, date, qty, rate):

    previous_purchases = frappe.db.get_list('Stock In Ledger', filters= {'date':['<', date], 'item': ['=', item],'warehouse':['=', warehouse], 'running_balance_qty':['>',0]}, fields= ['posting_date','voucher_type','voucher_no', 'running_balance_qty', 'incoming_rate'], as_lsit=True)

    balance_qty = 0

    for stock_in_ledger in previous_purchases:
        balance_qty = balance_qty + stock_in_ledger.running_balance_qty

    new_running_balance_qty = qty + balance_qty

    new_doc = frappe.get_doc('doctype':'Stock In Ledger', 'itemn': item, 'warehouse': warehouse, 'date': date, 'qty': qty, 'rate', rate
    'balance_qty': new_running_balance_qty, 'running_balance_qty': new_running_balance_qty
    )
    new_doc.insert()

