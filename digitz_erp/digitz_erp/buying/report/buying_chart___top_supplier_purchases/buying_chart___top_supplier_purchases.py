# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns, data = [], []
	chart = get_chart_data(filters) 
	columns = get_columns() 
	print("chart")
	print(chart)
	data = get_data(filters)
	return columns, data, None, chart

def get_chart_data(filters=None):
	
	query = """
    SELECT
        pi.supplier,
        SUM(pi.rounded_total) AS amount
    FROM
        `tabPurchase Invoice` pi
    WHERE
        pi.credit_purchase = 1
        AND pi.posting_date >= %s
        AND pi.posting_date <= %s
    GROUP BY pi.supplier
    ORDER BY amount DESC
    LIMIT 20
"""

	data = frappe.db.sql(query, (filters.get('from_date'), filters.get('to_date')), as_list=True)

 
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

	print("chart data")
	print(data)

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

def get_data(filters=None):

	query = """
		SELECT
			pi.supplier,
			SUM(pi.rounded_total) AS amount
		FROM
			`tabPurchase Invoice` pi
		WHERE
			pi.credit_purchase = 1
			AND pi.posting_date >= %s
			AND pi.posting_date <= %s
		GROUP BY pi.supplier
		ORDER BY amount DESC
		LIMIT 20
		"""

	data = frappe.db.sql(query, (filters.get('from_date'), filters.get('to_date')), as_list=True)

	return data	
    
def get_columns():
    return [
        {
            "fieldname": "supplier",
            "fieldtype": "Data",
            "label": "Supplier",            
            "width": 150,
        },
        {
            "fieldname": "amount",
            "fieldtype": "Data",
            "label": "Amount",
            "width": 210,
        }       
    ]
