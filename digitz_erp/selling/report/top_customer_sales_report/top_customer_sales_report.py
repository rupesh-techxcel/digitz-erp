# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns, data = [], []
	chart = get_chart_data(filters) 
	columns = get_columns() 
	#print("chart")
	#print(chart)
	data = get_data(filters)
	return columns, data, None, chart

def get_chart_data(filters=None):
	
	query = """
    SELECT
        si.customer_name as customer,
        SUM(si.rounded_total) AS amount
    FROM
        `tabSales Invoice` si
    WHERE        
        si.posting_date >= %s
        AND si.posting_date <= %s
    GROUP BY si.customer_name
    ORDER BY amount DESC
    LIMIT 5
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

	#print("chart data")
	#print(data)

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
			si.customer_name as customer,
			SUM(si.rounded_total) AS amount
		FROM
			`tabSales Invoice` si
		WHERE			
			si.posting_date >= %s
			AND si.posting_date <= %s
		GROUP BY si.customer_name
		ORDER BY amount DESC
		LIMIT 20
		"""

	data = frappe.db.sql(query, (filters.get('from_date'), filters.get('to_date')), as_list=True)

	return data	
    
def get_columns():
    return [
        {
            "fieldname": "customer",
            "fieldtype": "Data",
            "label": "Customer",            
            "width": 150,
        },
        {
            "fieldname": "amount",
            "fieldtype": "Data",
            "label": "Amount",
            "width": 210,
        }       
    ]
