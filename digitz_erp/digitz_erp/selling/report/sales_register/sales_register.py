# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    # Apply an additional filter to the data based on filters.get("warehouse")
    warehouse_filter = filters.get("warehouse")

    if warehouse_filter:
        data = [item for item in data if item.get("warehouse") == warehouse_filter]

    chart = get_chart_data(filters)
    return columns, data, None, chart

def get_chart_data(filters=None):
    credit_sale = filters.get('credit_sale')
    query = """
        SELECT
            si.customer,
            SUM(si.rounded_total) AS amount
        FROM
            `tabSales Invoice` si
        WHERE
            docstatus = 1 or docstatus=0
    """
    if filters:
        if credit_sale == 'Credit':
            sub_query = "AND si.credit_sale = 1"
            query += sub_query
        if credit_sale == 'Cash':
            sub_query = "AND si.credit_sale = 0"
            query += sub_query
        if filters.get('customer'):
            query += " AND si.customer = %(customer)s"
        if filters.get('from_date'):
            query += " AND si.posting_date >= %(from_date)s"
        if filters.get('to_date'):
            query += " AND si.posting_date <= %(to_date)s"

    query += " GROUP BY si.customer ORDER BY amount DESC LIMIT 20"
    
    data = frappe.db.sql(query, filters, as_list=True)

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
    data = ""

    credit_sale = filters.get('credit_sale')
    status = filters.get('status')

    if filters.get('customer') and filters.get('from_date') and filters.get('to_date'):
        query = """
            SELECT
                si.name AS sales_invoice_name,
                si.customer,
                si.posting_date AS posting_date,
                CASE
                    WHEN si.docstatus = 1 THEN 'Submitted'
                    WHEN si.docstatus = 0 THEN 'Draft'
				    WHEN si.docstatus = 2 THEN 'Cancelled'
                    ELSE ''
                END AS docstatus,
                si.warehouse,
                si.gross_total,
                si.tax_total,
                si.rounded_total AS amount,
                si.paid_amount,
                si.rounded_total - IFNULL(si.paid_amount, 0) AS balance_amount,
                si.payment_mode,
                si.payment_account
            FROM
                `tabSales Invoice` si
            WHERE
                si.customer = '{0}'
                AND si.posting_date BETWEEN '{1}' AND '{2}'
            """.format(filters.get('customer'), filters.get('from_date'), filters.get('to_date'))
        if credit_sale == 'Credit':
            sub_query = "AND si.credit_sale = 1 "
            query += sub_query
        if credit_sale == 'Cash':
            sub_query = "AND si.credit_sale = 0 "
            query += sub_query
        if status == 'Draft':
            sub_query = "AND si.docstatus = 0 "
            query += sub_query
        elif status == 'Submitted':
            sub_query = "AND si.docstatus = 1 "
            query += sub_query
        elif status == 'Cancelled':
            sub_query = "AND si.docstatus = 2 "
            query += sub_query
        elif status == 'Not Cancelled':
            sub_query = "AND si.docstatus !=2 "
            query += sub_query

        query += "ORDER BY si.posting_date"
        data = frappe.db.sql(query, as_dict=True)

    elif filters.get('from_date') and filters.get('to_date'):
        query = """
            SELECT
                si.name AS sales_invoice_name,
                si.customer,
                si.posting_date,
                CASE
                    WHEN si.docstatus = 1 THEN 'Submitted'
                    WHEN si.docstatus = 0 THEN 'Draft'
				    WHEN si.docstatus = 2 THEN 'Cancelled'
                    ELSE ''
                END AS docstatus,
                si.warehouse,
                si.posting_date,
                si.gross_total,
                si.tax_total,
                si.rounded_total AS amount,
                si.paid_amount,
                si.rounded_total - IFNULL(si.paid_amount, 0) AS balance_amount,
                si.payment_mode,
                si.payment_account
            FROM
                `tabSales Invoice` si
            WHERE
                si.posting_date BETWEEN '{0}' AND '{1}'
            """.format(filters.get('from_date'), filters.get('to_date'))
        if credit_sale == 'Credit':
            sub_query = "AND si.credit_sale = 1 "
            query += sub_query
        if credit_sale == 'Cash':
            sub_query = "AND si.credit_sale = 0 "
            query += sub_query
        if status == 'Draft':
            sub_query = "AND si.docstatus = 0 "
            query += sub_query
        elif status == 'Submitted':
            sub_query = "AND si.docstatus = 1 "
            query += sub_query
        elif status == 'Cancelled':
            sub_query = "AND si.docstatus = 2 "
            query += sub_query
        elif status == 'Not Cancelled':
            sub_query = "AND si.docstatus !=2 "
            query += sub_query
        
        print(query)

        data = frappe.db.sql(query, as_dict=True)

    elif filters.get('customer'):
        query = """
            SELECT
                si.name AS sales_invoice_name,
                si.customer,
                si.posting_date,
                CASE
                    WHEN si.docstatus = 1 THEN 'Submitted'
                    WHEN si.docstatus = 0 THEN 'Draft'
				    WHEN si.docstatus = 2 THEN 'Cancelled'
                    ELSE ''
                END AS docstatus,
                si.warehouse,
                si.gross_total,
                si.tax_total,
                si.rounded_total AS amount,
                si.paid_amount,
                si.rounded_total - IFNULL(si.paid_amount, 0) AS balance_amount,
                si.payment_mode,
                si.payment_account
            FROM
                `tabSales Invoice` si
            WHERE
                si.customer = '{0}'
            """.format(filters.get('customer'))
        if credit_sale == 'Credit':
            sub_query = "AND si.credit_sale = 1 "
            query += sub_query
        if credit_sale == 'Cash':
            sub_query = "AND si.credit_sale = 0 "
            query += sub_query
        if status == 'Draft':
            sub_query = "AND si.docstatus = 0 "
            query += sub_query
        elif status == 'Submitted':
            sub_query = "AND si.docstatus = 1 "
            query += sub_query
        elif status == 'Cancelled':
            sub_query = "AND si.docstatus = 2 "
            query += sub_query
        elif status == 'Not Cancelled':
            sub_query = "AND si.docstatus !=2 "
            query += sub_query

       
        print(query)


        data = frappe.db.sql(query, as_dict=True)
    else:
        query = """
            SELECT
                si.name AS sales_invoice_name,
                si.customer,
                si.posting_date AS posting_date,
                CASE
                    WHEN si.docstatus = 1 THEN 'Submitted'
                    WHEN si.docstatus = 0 THEN 'Draft'
				    WHEN si.docstatus = 2 THEN 'Cancelled'
                    ELSE ''
                END AS docstatus,
                si.warehouse,
                si.gross_total,
                si.tax_total,
                si.rounded_total AS amount,
                si.paid_amount,
                si.rounded_total - IFNULL(si.paid_amount, 0) AS balance_amount
            FROM
                `tabSales Invoice` si
            WHERE
                1
            """
        if credit_sale == 'Credit':
            sub_query = "AND si.credit_sale = 1 "
            query += sub_query
        if credit_sale == 'Cash':
            sub_query = "AND si.credit_sale = 0 "
            query += sub_query
        if status == 'Draft':
            sub_query = "AND si.docstatus = 0 "
            query += sub_query
        elif status == 'Submitted':
            sub_query = "AND si.docstatus = 1 "
            query += sub_query
        elif status == 'Cancelled':
            sub_query = "AND si.docstatus = 2 "
            query += sub_query
        elif status == 'Not Cancelled':
            sub_query = "AND si.docstatus !=2 "
            query += sub_query

        
        print(query)

        data = frappe.db.sql(query, as_dict=True)

    return data

def get_columns():
	return [
		{

			"fieldname": "sales_invoice_name",
			"fieldtype": "Link",
			"label": "Invoice No",
			"options": "Sales Invoice",
			"width": 120,

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
			"width": 90,
		},
  		{

			"fieldname": "docstatus",
			"fieldtype": "Data",
			"label": "Status",
			"width": 120,

		},
        {

			"fieldname": "warehouse",
			"fieldtype": "Data",
			"label": "Warehouse",
			"width": 120,

		},
    	{

			"fieldname": "gross_total",
			"fieldtype": "Currency",
			"label": "Taxable Amount",
			"width": 120,
		},    
        {

			"fieldname": "tax_total",
			"fieldtype": "Currency",
			"label": "Tax",
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
			"options": "Account" ,
			"width": 120,
		}
	]
