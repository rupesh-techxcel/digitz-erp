import frappe

def execute(filters=None):
    columns = [
        {"label": "Item", "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 150},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 150},
        {"label": "Opening Qty", "fieldname": "opening_qty", "fieldtype": "Float", "width": 120},
        {"label": "Purchase Qty", "fieldname": "purchase_qty", "fieldtype": "Float", "width": 120},
        {"label": "Sales Qty", "fieldname": "sales_qty", "fieldtype": "Float", "width": 120},
        {"label": "Purchase Return Qty", "fieldname": "purchase_return_qty", "fieldtype": "Float", "width": 150},
        {"label": "Sales Return Qty", "fieldname": "sales_return_qty", "fieldtype": "Float", "width": 150},
        {"label": "Balance Qty", "fieldname": "balance_qty", "fieldtype": "Float", "width": 120},
    ]

    data = frappe.db.sql("""
        SELECT
            sle.item,
            item.item_name,
            sle.balance_qty as opening_qty,
            sle.posting_date,
            COALESCE(pur.qty, 0) as purchase_qty,
            COALESCE(sal.qty, 0) as sales_qty,
            COALESCE(pur_return.qty, 0) as purchase_return_qty,
            COALESCE(sal_return.qty, 0) as sales_return_qty,
            sle.balance_qty + COALESCE(pur.qty, 0) - COALESCE(sal.qty, 0) - COALESCE(pur_return.qty, 0) + COALESCE(sal_return.qty, 0) as balance_qty
        FROM
            `tabStock Ledger` sle
        INNER JOIN
            tabItem item ON sle.item = item.item_code
        LEFT JOIN
            `tabPurchase Invoice` pur_inv ON pur_inv.posting_date = %(posting_date)s
        LEFT JOIN
            `tabPurchase Invoice Item` pur ON pur.parent = pur_inv.name AND pur.item = sle.item
        LEFT JOIN
            `tabSales Invoice` sal_inv ON sal_inv.posting_date = %(posting_date)s
        LEFT JOIN
            `tabSales Invoice Item` sal ON sal.parent = sal_inv.name AND sal.item = sle.item
        LEFT JOIN
            `tabPurchase Return` pur_return_inv ON pur_return_inv.posting_date = %(posting_date)s
        LEFT JOIN
            `tabPurchase Return Item` pur_return ON pur_return.parent = pur_return_inv.name AND pur_return.item_code = sle.item
        LEFT JOIN
            `tabSales Return` sal_return_inv ON sal_return_inv.posting_date = %(posting_date)s
        LEFT JOIN
            `tabSales Return Item` sal_return ON sal_return.parent = sal_return_inv.name AND sal_return.item = sle.item
        # WHERE
        #     sle.posting_date < %(posting_date)s
        ORDER BY
            sle.item, sle.posting_date DESC
    """, {"posting_date": filters.get("posting_date")}, as_dict=1)

    return columns, data
