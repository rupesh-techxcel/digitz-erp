import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(filters)
    return columns, data, None, chart

def get_chart_data(filters=None):
    credit_sale = filters.get("credit_sale")
    if credit_sale == "Credit":
        is_credit_sale = 1
    elif credit_sale == "Cash":
        is_credit_sale = 0
    else:
        is_credit_sale = None

    query = """
        SELECT
            qr.customer,
            SUM(qr.rounded_total) AS amount
        FROM
            `tabQuotation` qr
        WHERE
            (%(is_credit_sale)s IS NULL OR qr.credit_sale = %(is_credit_sale)s)
    """
    if filters:
        if filters.get('customer'):
            query += " AND qr.customer = %(customer)s"
        if filters.get('from_date'):
            query += " AND qr.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND qr.posting_date <= %(to_date)s"

    query += " GROUP BY qr.customer ORDER BY qr.customer"
    data = frappe.db.sql(query, {"is_credit_sale": is_credit_sale, **filters}, as_list=True)

    customers = []
    customer_wise_amount = {}
    for row in data:
        if row[0] not in customers:
            customers.append(row[0])
        if customer_wise_amount.get(row[0]):
            customer_wise_amount[row[0]] += row[1]
        else:
            customer_wise_amount[row[0]] = row[1]
    data = list(customer_wise_amount.items())

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
    credit_sale = filters.get("credit_sale")
    if credit_sale == "Credit":
        is_credit_sale = 1
    elif credit_sale == "Cash":
        is_credit_sale = 0
    else:
        is_credit_sale = None

    query = """
        SELECT
            qr.name AS quotation_name,
            qr.customer,
            qr.posting_date AS posting_date,
            CASE
                WHEN qr.docstatus = 1 THEN 'Submitted'
                ELSE ''
            END AS docstatus,
            qr.rounded_total AS amount,
            qr.payment_mode,
            qr.payment_account
        FROM
            `tabQuotation` qr
        WHERE
            (%(is_credit_sale)s IS NULL OR qr.credit_sale = %(is_credit_sale)s)
            AND (%(customer)s IS NULL OR qr.customer = %(customer)s)
            AND (%(from_date)s IS NULL OR qr.posting_date >= %(from_date)s)
            AND (%(to_date)s IS NULL OR qr.posting_date <= %(to_date)s)
            AND qr.docstatus = 1
        ORDER BY
            qr.posting_date
    """
    data = frappe.db.sql(query, {
        "is_credit_sale": is_credit_sale,
        "customer": filters.get('customer'),
        "from_date": filters.get('from_date'),
        "to_date": filters.get('to_date')
    }, as_dict=True)

    return data

def get_columns():
    return [
        {
            "fieldname": "quotation_name",
            "fieldtype": "Link",
            "label": "Invoice No",
            "options": "Quotation",
            "width": 150
        },
        {
            "fieldname": "customer",
            "fieldtype": "Link",
            "label": "Customer",
            "options": "Customer",
            "width": 150
        },
        {
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "label": "Date",
            "width": 120
        },
        {
            "fieldname": "docstatus",
            "fieldtype": "Data",
            "label": "Status",
            "width": 120
        },
        {
            "fieldname": "amount",
            "fieldtype": "Currency",
            "label": "Invoice Amount",
            "width": 120
        },
        {
            "fieldname": "payment_mode",
            "fieldtype": "Link",
            "label": "Payment Mode",
            "options": "Payment Mode",
            "width": 120
        },
        {
            "fieldname": "payment_account",
            "fieldtype": "Link",
            "label": "Account",
            "options": "Account",
            "width": 120
        }
    ]
