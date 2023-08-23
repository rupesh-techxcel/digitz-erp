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
    else:
        is_credit_purchase = None

    query = """
        SELECT
            po.supplier,
            SUM(po.rounded_total) AS amount
        FROM
            `tabPurchase Order` po
        WHERE
            (%(is_credit_purchase)s IS NULL OR po.credit_purchase = %(is_credit_purchase)s)
    """
    if filters:
        if filters.get('supplier'):
            query += " AND po.supplier = %(supplier)s"
        if filters.get('from_date'):
            query += " AND po.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND po.posting_date <= %(to_date)s"

    query += " GROUP BY po.supplier ORDER BY po.supplier"
    data = frappe.db.sql(query, {"is_credit_purchase": is_credit_purchase, **filters}, as_list=True)

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
    else:
        is_credit_purchase = None

    query = """
        SELECT
            po.supplier,
            po.name AS purchase_order_name,
            po.posting_date AS posting_date,
            CASE
                WHEN po.docstatus = 1 THEN 'Submitted'
                ELSE ''
            END AS docstatus,
            po.rounded_total AS amount
        FROM
            `tabPurchase Order` po
        WHERE
            (%(is_credit_purchase)s IS NULL OR po.credit_purchase = %(is_credit_purchase)s)
            AND (%(supplier)s IS NULL OR po.supplier = %(supplier)s)
            AND (%(from_date)s IS NULL OR po.posting_date >= %(from_date)s)
            AND (%(to_date)s IS NULL OR po.posting_date <= %(to_date)s)
            AND po.docstatus = 1
        ORDER BY
            po.posting_date
    """
    data = frappe.db.sql(query, {
        "is_credit_purchase": is_credit_purchase,
        "supplier": filters.get('supplier'),
        "from_date": filters.get('from_date'),
        "to_date": filters.get('to_date')
    }, as_dict=True)

    return data

def get_columns():
    return [
        {
            "fieldname": "supplier",
            "fieldtype": "Link",
            "label": "Supplier",
            "options": "Supplier",
            "width": 415
        },
        {
            "fieldname": "purchase_order_name",
            "fieldtype": "Link",
            "label": "Purchase Order No",
            "options": "Purchase Order",
            "width": 250
        },
        {
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "label": "Date",
            "width": 170
        },
        {
            "fieldname": "docstatus",
            "fieldtype": "Data",
            "label": "Status",
            "width": 170
        },
        {
            "fieldname": "amount",
            "fieldtype": "Currency",
            "label": "Invoice Amount",
            "width": 200
        },
        
    ]
