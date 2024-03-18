import frappe
from datetime import datetime

@frappe.whitelist()
def get_customer_balance(supplier):
    today = datetime.today().date()

    sql_query = """
        SELECT SUM(credit_amount) - SUM(debit_amount) as supplier_balance FROM `tabGL Posting` WHERE party_type='Supplier' AND party=%s AND posting_date <= %s"""
    data = frappe.db.sql(sql_query, (supplier, today), as_dict=True)
    return data
    
@frappe.whitelist()
def get_supplier_balance(supplier):
    today = datetime.today().date()

    sql_query = """
        SELECT SUM(credit_amount) - SUM(debit_amount) as supplier_balance FROM `tabGL Posting` WHERE party_type='Supplier' AND party=%s AND DATE(posting_date) <= %s """
    data = frappe.db.sql(sql_query, (supplier, today), as_dict=True)
    return data

@frappe.whitelist()
def get_stock_ledgers(voucher,voucher_no):
    stock_ledgers = frappe.get_all("Stock Ledger",
                                    filters={"voucher":voucher,"voucher_no": voucher_no},
                                    fields=["name", "item","item_name", "warehouse", "qty_in", "qty_out", "valuation_rate", "balance_qty", "balance_value"])
    formatted_stock_ledgers = []
    for ledgers in stock_ledgers:
        formatted_stock_ledgers.append({
            "stock_ledger": ledgers.name,
            "item": ledgers.item,
            "item_name":ledgers.item_name,
            "warehouse": ledgers.warehouse,
            "qty_in": ledgers.qty_in,
            "qty_out": ledgers.qty_out,
            "valuation_rate": ledgers.valuation_rate,
            "balance_qty": ledgers.balance_qty,
            "balance_value": ledgers.balance_value
        })
    
    return formatted_stock_ledgers

@frappe.whitelist()
def get_gl_postings(voucher,voucher_no):
    gl_postings = frappe.get_all("GL Posting",
                                  filters={"voucher_type":voucher,
                                      "voucher_no": voucher_no},
                                  fields=["account", "debit_amount", "credit_amount", "against_account", "remarks"])
    formatted_gl_postings = []
    for posting in gl_postings:
        formatted_gl_postings.append({
            "gl_posting": posting.name,
            "account":posting.account,
            "debit_amount": posting.debit_amount,
            "credit_amount": posting.credit_amount,
            "against_account": posting.against_account,
            "remarks": posting.remarks
        })

    return formatted_gl_postings