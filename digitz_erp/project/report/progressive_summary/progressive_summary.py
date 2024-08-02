# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = [
        {"fieldname": "name", "label": "ID", "fieldtype": "Data", "width": 120},
        {"fieldname": "customer", "label": "Customer", "fieldtype": "Data", "width": 144},
        {"fieldname": "description", "label": "Description", "fieldtype": "Data", "width": 120},
        {"fieldname": "item", "label": "Item (Stage Table)", "fieldtype": "Data", "width": 208},
        {"fieldname": "amount", "label": "Amount (Stage Table)", "fieldtype": "Currency", "width": 120},
        {"fieldname": "prev_amount", "label": "Prev Amount", "fieldtype": "Currency", "width": 120},
        {"fieldname": "current_amount", "label": "Current Amount", "fieldtype": "Currency", "width": 120},
        {"fieldname": "advance_deducation", "label": "Advance Deduction", "fieldtype": "Currency", "width": 120},
        {"fieldname": "retentation_deducation", "label": "Retention Deduction", "fieldtype": "Currency", "width": 120},
    ]

    conditions = ""
    if filters.get("project"):
        conditions += "AND pi.project = %(project)s "
    if filters.get("item"):
        conditions += "AND st.item = %(item)s "

    data = frappe.db.sql(f"""
        SELECT
            pi.name,
            pi.customer,
            st.description,
            st.item,
            st.amount,
            st.prev_amount,
            st.current_amount,
            pi.advance_deducation,
            pi.retentation_deducation
        FROM
            `tabProgressive Invoice` pi
        LEFT JOIN
            `tabStage Table` st ON st.parent = pi.name
        WHERE
            1 = 1
            {conditions}
        ORDER BY
            pi.creation DESC
    """, filters, as_dict=True)

    # if not data:
    #     frappe.msgprint("No data found for the given filters.")
    
    # Debugging: Print the retrieved data
    # frappe.logger().debug(data)
    # Calculate summary totals
    total_amount = sum((row["amount"] or 0) for row in data)
    # total_prev_amount = sum(row["prev_amount"] for row in data)
    # total_current_amount = sum(row["current_amount"] for row in data)

    summary = [
        {"label": "Total Amount", "value": total_amount},
        # {"label": "Total Prev Amount", "value": total_prev_amount},
        # {"label": "Total Current Amount", "value": total_current_amount}
    ]

    chart_data = {
        "data": {
            "labels": [],
            "datasets": [
                {
                    "name": "Amount", "values": []
                },
                {
                    "name": "Prev Amount", "values": []
                },
                {
                    "name": "Current Amount", "values": []
                }
            ]
        },
        "type": "bar",
        "colors": ["#00FF00", "#FFA500", "#254be6"]  # Example colors: Green, Orange, Red
    }

    for row in data:
        chart_data["data"]["labels"].append(row["item"] or "")
        chart_data["data"]["datasets"][0]["values"].append(row["amount"] or 0)
        chart_data["data"]["datasets"][1]["values"].append(row["prev_amount"] or 0)
        chart_data["data"]["datasets"][2]["values"].append(row["current_amount"] or 0)

    return columns, data, None, chart_data, summary
