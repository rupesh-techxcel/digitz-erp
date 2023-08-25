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

    query = """
    SELECT
        si.customer,
        SUM(si.rounded_total) AS amount
    FROM
        `tabSales Invoice` si
    """

    if filters:
        if filters.get('customer'):
            query += "si.customer = %(customer)s"
        if filters.get('from_date'):
            query += " AND si.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND si.posting_date <= %(to_date)s"
        if is_credit_sale == 1 or is_credit_sale == 0:  # Changed OR to lower case
            query += " AND si.credit_sale = %(is_credit_sale)s"  # Fixed column name

        query += " GROUP BY si.customer"  # Removed ORDER BY from here
        query += " ORDER BY si.customer"  # Added ORDER BY here

    data = frappe.db.sql(query, as_list=True)  # Changed as_list=True to as_dict=True


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
    is_credit_sale = None
    if credit_sale == "Credit" :
        is_credit_sale = 1
    elif credit_sale == "Cash":
        is_credit_sale = 0

    query = """
        SELECT
            si.name AS sales_invoice_name,
            si.customer,
            si.posting_date AS posting_date,
            CASE
                WHEN si.docstatus = 1 THEN 'Submitted'
                ELSE ''
            END AS docstatus,
            si.rounded_total AS amount,
            si.paid_amount,
            si.rounded_total - IFNULL(si.paid_amount, 0) AS balance_amount,
            si.payment_mode,
            si.payment_account
        FROM
            `tabSales Invoice` si
        WHERE
            (%(is_credit_sale)s IS NULL OR si.credit_sale = %(is_credit_sale)s)
            AND (%(customer)s IS NULL OR si.customer = %(customer)s)
            AND (%(from_date)s IS NULL OR si.posting_date >= %(from_date)s)
            AND (%(to_date)s IS NULL OR si.posting_date <= %(to_date)s)
            AND si.docstatus = 1
        ORDER BY
            si.posting_date
    """

    data = frappe.db.sql(query, as_dict=True)

    return data


def get_columns():
    return [
        {
            "fieldname": "sales_invoice_name",
            "fieldtype": "Link",
            "label": "Invoice No",
            "options": "Sales Invoice",
            "width": 150,
        },
        {
            "fieldname": "customer",
            "fieldtype": "Link",
            "label": "Customer",
            "options": "Customer",
            "width": 210,
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
            "width": 120,
        },
        {
            "fieldname": "balance_amount",
            "fieldtype": "Currency",
            "label": "Balance Amount",
            "width": 120,
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
