# stock_ledger_report.py
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Item"), "fieldname": "item_name", "fieldtype": "Link", "options": "Item", "width": 100},
        {"label": _("Opening Qty"), "fieldname": "opening_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Stock Recon Qty"), "fieldname": "stock_recon_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Purchase Qty"), "fieldname": "purchase_qty", "fieldtype": "Float", "width": 120},
        {"label": _("Purchase Return Qty"), "fieldname": "purchase_return_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Sales Qty"), "fieldname": "sales_qty", "fieldtype": "Float", "width": 120},
        {"label": _("Sales Return Qty"), "fieldname": "sales_return_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Transfer In Qty"), "fieldname": "transfer_in_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Transfer Out Qty"), "fieldname": "transfer_out_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Balance Qty"), "fieldname": "balance_qty", "fieldtype": "Float", "width": 120},
        # Add other columns as needed
    ]

def get_data(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    item = filters.get("item")
    warehouse = filters.get("warehouse")
    show_all = filters.get("show_all")
    
    # Filter conditions
    item_condition = f" AND item = '{item}'" if item else ""
    warehouse_condition = f" AND warehouse = '{warehouse}'" if warehouse else ""

    # Fetch the opening quantity for all items based on the last record's balance quantity
    opening_balance_query = f"""
    SELECT
        item as item_code,
        i.item_name,
        balance_qty as opening_qty
    FROM `tabStock Ledger` sl
    INNER JOIN `tabItem` i on i.name = sl.item
    WHERE (item, posting_date) IN (
        SELECT
            item,
            MAX(posting_date) as max_posting_date
        FROM `tabStock Ledger`
        WHERE posting_date < '{from_date}'
            {item_condition}
            {warehouse_condition}
        GROUP BY item
    )
    """

    opening_balance_data = frappe.db.sql(opening_balance_query, as_dict=True)
    
    print(opening_balance_data)
    print(opening_balance_data)

    stock_recon_qty_query = f"""
        SELECT item as item_code, SUM(balance_qty) as balance_qty,
        SUM(qty_in) as qty_in,
        SUM(qty_out) as qty_out
        FROM `tabStock Ledger`
        WHERE voucher = 'Stock Reconciliation'
            AND posting_date >= '{from_date} 00:00:00'
            AND posting_date < '{to_date} 23:59:59'
            {item_condition}
            {warehouse_condition}
        GROUP BY item
    """

    stock_recon_qty_data = frappe.db.sql(stock_recon_qty_query, as_dict=True)

    purchase_qty_query = f"""
        SELECT item as item_code, SUM(qty_in) as purchase_qty
        FROM `tabStock Ledger`
        WHERE voucher = 'Purchase Invoice'
            AND posting_date >= '{from_date} 00:00:00'
            AND posting_date < '{to_date} 23:59:59'
            {item_condition}
            {warehouse_condition}
        GROUP BY item
    """

    purchase_qty_data = frappe.db.sql(purchase_qty_query, as_dict=True)

     # Fetch the purchase return quantity for all items within the specified date range
    purchase_return_qty_query = f"""
        SELECT item as item_code, SUM(qty_out) as purchase_return_qty
        FROM `tabStock Ledger`
        WHERE voucher = 'Purchase Return'
            AND posting_date >= '{from_date} 00:00:00'
            AND posting_date < '{to_date} 23:59:59'
            {item_condition}
            {warehouse_condition}
        GROUP BY item
    """

    purchase_return_qty_data = frappe.db.sql(purchase_return_qty_query, as_dict=True)


    sales_qty_query = f"""
        SELECT item as item_code, SUM(qty_out) as sales_qty
        FROM `tabStock Ledger`
        WHERE voucher = 'Sales Invoice'
            AND posting_date >= '{from_date} 00:00:00'
            AND posting_date < '{to_date} 23:59:59'
            {item_condition}
            {warehouse_condition}
        GROUP BY item
    """.format(from_date=from_date,to_date=to_date, item_condition=item_condition,warehouse_condition=warehouse_condition)

    sales_qty_data = frappe.db.sql(sales_qty_query, as_dict=True)

    # Fetch the sales return quantity for all items within the specified date range
    sales_return_qty_query = f"""
        SELECT item as item_code, SUM(qty_in) as sales_return_qty
        FROM `tabStock Ledger`
        WHERE voucher = 'Sales Return'
            AND posting_date >= '{from_date} 00:00:00'
            AND posting_date < '{to_date} 23:59:59'

            {item_condition}
            {warehouse_condition}
        GROUP BY item
    """.format(from_date=from_date,to_date=to_date, item_condition=item_condition,warehouse_condition=warehouse_condition)

    sales_return_qty_data = frappe.db.sql(sales_return_qty_query, as_dict=True)

    transfer_in_qty_query = f"""
    SELECT item as item_code, SUM(qty_in) as transfer_in_qty
    FROM `tabStock Ledger`
    WHERE voucher = 'Stock Transfer'
        AND (qty_in > 0)
        AND posting_date >= '{from_date} 00:00:00'
        AND posting_date < '{to_date} 23:59:59'
        {item_condition}
        {warehouse_condition}
    GROUP BY item
    """.format(from_date=from_date,to_date=to_date, item_condition=item_condition,warehouse_condition=warehouse_condition)

    transfer_in_qty_data = frappe.db.sql(transfer_in_qty_query, as_dict=True)


    # Fetch the transfer out quantity for all items within the specified date range
    transfer_out_qty_query = f"""
        SELECT item as item_code, SUM(qty_out) as transfer_out_qty
        FROM `tabStock Ledger`
        WHERE voucher = 'Stock Transfer'
            AND qty_out > 0
            AND posting_date >= '{from_date} 00:00:00'
            AND posting_date < '{to_date} 23:59:59'

            {item_condition}
            {warehouse_condition}
        GROUP BY item
    """

    transfer_out_qty_data = frappe.db.sql(transfer_out_qty_query, as_dict=True)
    
    opening_value_exists = False
    transaction_value_exists = False

    data = []
    for opening_balance_row in opening_balance_data:

        item_row = {"item_name": opening_balance_row.item_name, "opening_qty": opening_balance_row.opening_qty, "closing_qty": 0, "purchase_qty": 0, "purchase_return_qty":0, "sales_qty":0, "sales_return_qty":0, "transfer_in_qty":0, "transfer_out_qty":0, "balance_qty":0}

        balance_qty = opening_balance_row.opening_qty
        
        opening_value_exists = balance_qty != 0
        transaction_value_exists = False

        # For reconciliation it can be qty_in and qty_out both needs to be considered for balance_qty
        for stock_recon_qty_row in stock_recon_qty_data:
            if stock_recon_qty_row.item_code == opening_balance_row.item_code:
                item_row["stock_recon_qty"] = stock_recon_qty_row.balance_qty
                balance_qty += stock_recon_qty_row.qty_in - stock_recon_qty_data.qty_out

                (transaction_value_exists) = True
                break

        # Find the matching purchase_qty_row for the item
        for purchase_qty_row in purchase_qty_data:
            if purchase_qty_row.item_code == opening_balance_row.item_code:
                item_row["purchase_qty"] = purchase_qty_row.purchase_qty
                balance_qty += purchase_qty_row.purchase_qty

                if not (transaction_value_exists):
                    (transaction_value_exists) = purchase_qty_row.purchase_qty !=0

                break

        # Find the matching purchase_return_qty_row for the item
        for purchase_return_qty_row in purchase_return_qty_data:
            if purchase_return_qty_row.item_code == opening_balance_row.item_code:
                item_row["purchase_return_qty"] = purchase_return_qty_row.purchase_return_qty
                balance_qty += (purchase_return_qty_row.purchase_return_qty * -1)

                if not (transaction_value_exists):
                    (transaction_value_exists) = purchase_return_qty_row.purchase_return_qty !=0

                break

        # Find the matching sales_qty_row for the item
        for sales_qty_row in sales_qty_data:
            if sales_qty_row.item_code == opening_balance_row.item_code:
                item_row["sales_qty"] = sales_qty_row.sales_qty
                balance_qty += (sales_qty_row.sales_qty * -1)

                if not (transaction_value_exists):
                    (transaction_value_exists) = sales_qty_row.sales_qty !=0

                break

        # Find the matching sales_return_qty_row for the item
        for sales_return_qty_row in sales_return_qty_data:
            if sales_return_qty_row.item_code == opening_balance_row.item_code:
                item_row["sales_return_qty"] = sales_return_qty_row.sales_return_qty
                balance_qty += sales_return_qty_row.sales_return_qty

                if not (transaction_value_exists):
                    (transaction_value_exists) = sales_return_qty_row.sales_return_qty !=0

                break

        for transfer_in_qty_row in transfer_in_qty_data:
            if transfer_in_qty_row.item_code == opening_balance_row.item_code:
                item_row["transfer_in_qty"] = transfer_in_qty_row.transfer_in_qty
                balance_qty += transfer_in_qty_row.transfer_in_qty

                if not (transaction_value_exists):
                    (transaction_value_exists) = transfer_in_qty_row.transfer_in_qty !=0

                break

        # Find the matching transfer_out_qty_row for the item
        for transfer_out_qty_row in transfer_out_qty_data:
            if transfer_out_qty_row.item_code == opening_balance_row.item_code:
                item_row["transfer_out_qty"] = transfer_out_qty_row.transfer_out_qty
                balance_qty += (transfer_out_qty_row.transfer_out_qty * -1)

                if not (transaction_value_exists):
                    (transaction_value_exists) = transfer_out_qty_row.transfer_out_qty !=0

                break

        item_row["balance_qty"] = balance_qty

        if not show_all and transaction_value_exists:
            data.append(item_row)
        elif show_all and (transaction_value_exists or opening_value_exists):
            data.append(item_row)

    return data
