import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(filters)
    return columns, data, None, chart

def get_chart_data(filters=None):
    credit_purchase = filters.get("credit_purchase")
    if credit_purchase == "Credit":
        is_credit_purchase = 1
    elif credit_purchase == "Cash":
        is_credit_purchase = 0

    query = """
        SELECT
            pi.supplier,
            SUM(pi.rounded_total) AS amount
        FROM
            `tabPurchase Invoice` pi
        WHERE
            (%(is_credit_purchase)s IS NULL OR pi.credit_purchase = %(is_credit_purchase)s)
    """
    if filters:
        if filters.get('supplier'):
            query += " AND pi.supplier = %(supplier)s"
        if filters.get('from_date'):
            query += " AND pi.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND pi.posting_date <= %(to_date)s"

    query += " GROUP BY pi.supplier ORDER BY pi.supplier"
    data = frappe.db.sql(query,as_list=True)

    suppliers = []
    supplier_wise_amount = {}
    for row in data:
        if row[0] not in suppliers:
            suppliers.append(row[0])
        if supplier_wise_amount.get(row[0]):
            supplier_wise_amount[row[0]] += row[1]
        else:
            supplier_wise_amount[row[0]] = row[1]
    data = list(supplier_wise_amount.items())

    datasets = []
    labels = []
    chart = {}

    if data:
        for d in data:
            labels.append(d[0])
            datasets.append(d[1])

        chart = {
            "data": {
                "labels": labels,
                "datasets": [{"values": datasets}]
            },
            "type": "bar"
        }
    return chart

def get_data(filters):
    credit_purchase = filters.get("credit_purchase")
    if credit_purchase == "Credit":
        is_credit_purchase = 1
    elif credit_purchase == "Cash":
        is_credit_purchase = 0

    query = """
            SELECT
            pi.supplier,
            pi.name AS purchase_invoice_name,
            pi.posting_date AS posting_date,
            CASE
                WHEN pi.docstatus = 1 THEN 'Submitted'
                ELSE ''
            END AS docstatus,
            pi.rounded_total AS amount,
            pi.paid_amount,
            pi.rounded_total - IFNULL(pi.paid_amount, 0) AS balance_amount,
            pi.payment_mode,
            pi.payment_account
        FROM
            `tabPurchase Invoice` pi)
        WHERE
            (%(is_credit_purchase)s IS NULL OR pi.credit_purchase = %(is_credit_purchase)s)
            AND (%(supplier)s IS NULL OR pi.supplier = %(supplier)s)
            AND (%(from_date)s IS NULL OR pi.posting_date >= %(from_date)s)
            AND (%(to_date)s IS NULL OR pi.posting_date <= %(to_date)s)
            AND pi.docstatus = 1
        ORDER BY
            pi.posting_date
    """
    data = frappe.db.sql(query, as_dict=True)

    return data

def get_columns():
    return [
        {
            "fieldname": "supplier",
            "fieldtype": "Link",
            "label": "Supplier",
            "options": "Supplier",
            "width": 150,
        },
        {
            "fieldname": "purchase_invoice_name",
            "fieldtype": "Link",
            "label": "Invoice No",
            "options": "Purchase Invoice",
            "width": 150,
        },
        {
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "label": "Date",
            "width": 120,
        },
        {
            "fieldname": "docstatus",
            "fieldtype": "Data",
            "label": "Status",
            "width": 120,
        },
        {
            "fieldname": "amount",
            "fieldtype": "Currency",
            "label": "Invoice Amount",
            "width": 120,
        },
        {
            "fieldname": "paid_amount",
            "fieldtype": "Currency",
            "label": "Paid Amount",
            "width": 100,
        },
        {
            "fieldname": "balance_amount",
            "fieldtype": "Currency",
            "label": "Balance Amount",
            "width": 100,
        },
        {
            "fieldname": "payment_mode",
            "fieldtype": "Link",
            "label": "Payment Mode",
            "options": "Payment Mode",
            "width": 120,
        },
        {
            "fieldname": "payment_account",
            "fieldtype": "Link",
            "label": "Account",
            "options": "Account",
            "width": 120,
        }
    ]
