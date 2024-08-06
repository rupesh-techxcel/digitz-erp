# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt


import frappe

def execute(filters=None):
    columns = [
        {"fieldname": "name", "label": "Project ID", "fieldtype": "Data", "width": 120},
        {"fieldname": "docstatus", "label": "Docstatus", "fieldtype": "Int", "width": 120},
        {"fieldname": "name1", "label": "Project Name", "fieldtype": "Data", "width": 120},
        {"fieldname": "retentation_percentage", "label": "Retention Percentage", "fieldtype": "Percent", "width": 120},
        {"fieldname": "retentation_amt", "label": "Retention Amount", "fieldtype": "Currency", "width": 120},
        {"fieldname": "expected_start_date", "label": "Expected Start Date", "fieldtype": "Date", "width": 120},
        {"fieldname": "expected_end_date", "label": "Expected End Date", "fieldtype": "Date", "width": 120},
        {"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 120},
        {"fieldname": "project_amount", "label": "Project Amount", "fieldtype": "Currency", "width": 120},
        {"fieldname": "project_delivery_date", "label": "Project Delivery Date", "fieldtype": "Date", "width": 120},
        {"fieldname": "priority", "label": "Priority", "fieldtype": "Data", "width": 120},
        {"fieldname": "advance_entry", "label": "Advance Entry", "fieldtype": "Currency", "width": 120},
        {"fieldname": "amount_after_retentation", "label": "Amount After Retention", "fieldtype": "Currency", "width": 120},
        {"fieldname": "project_stage_defination", "label": "Project Stage Definition", "fieldtype": "Data", "width": 120},
        {"fieldname": "percentage_of_completion", "label": "Percentage of Completion", "fieldtype": "Percent", "width": 120},
        {"fieldname": "proforma_invoice", "label": "Proforma Invoice", "fieldtype": "Data", "width": 120},
        {"fieldname": "sales_invoice", "label": "Sales Invoice", "fieldtype": "Data", "width": 120},
        {"fieldname": "net_total", "label": "Net Total", "fieldtype": "Currency", "width": 120},  # New Column
    ]

    conditions = ""
    if filters.get("project"):
        conditions += "AND p.name = %(project)s "
    if filters.get("status"):
        conditions += "AND p.status = %(status)s "

    data = frappe.db.sql(f"""
        SELECT
            p.name,
            p.docstatus,
            p.name1,
            p.retentation_percentage,
            p.retentation_amt,
            p.expected_start_date,
            p.expected_end_date,
            p.status,
            p.project_amount,
            p.project_delivery_date,
            p.priority,
            p.advance_entry,
            p.amount_after_retentation,
            pst.project_stage_defination,
            pst.percentage_of_completion,
            pst.proforma_invoice,
            pst.sales_invoice,
            pst.net_total
        FROM
            `tabProject` p
        LEFT JOIN
            `tabProject Stage Table` pst ON pst.parent = p.name
        WHERE
            1=1
            {conditions}
        ORDER BY
            p.creation DESC
    """, filters, as_dict=True)

    # Calculate total project amount and percentage of completion

    # Calculate the total amount received from sales invoices
    # total_received_amount = 0
    # for row in data:
    #     if row["sales_invoice"]:
    #         sales_invoices = row["sales_invoice"].split(",")
    #         for invoice in sales_invoices:
    #             total_received_amount += frappe.db.get_value("Sales Invoice", invoice, "net_total") or 0
    project_totals =  {}
    for row in data:
        id = row["name"]
        project_totals[id] = row["project_amount"]
        sales_invoice_net_totals = [row["net_total"] for row in data if row["net_total"] is not None]


    # Calculate average percentage of completion
    if filters.get("project"):
        print (data)
        total_project_amount = round(data[0].project_amount, 2)
        percentage_values = [row["percentage_of_completion"] for row in data if row["percentage_of_completion"] is not None]
        total_percentage_of_completion = sum(percentage_values)

        summary = [
        {"label": "Total Percentage of Completion", "value": round(total_percentage_of_completion)},
        {"label": "Total Project Amount", "value": total_project_amount},
        {"label": "Total Amount Received", "value": sum(sales_invoice_net_totals)},
        {"label": "Pending Amount", "value": round(total_project_amount - sum(sales_invoice_net_totals),2)}
        ]
    else:
        print()
        print(project_totals)
        print()
        total_project_amount = 0 
        for p in project_totals.values():
            total_project_amount += p
        percentage_values = [row["percentage_of_completion"] for row in data if row["percentage_of_completion"] is not None]
        total_percentage_of_completion = sum(percentage_values) / len(percentage_values) if percentage_values else 0


        summary = [
            {"label": "Average Percentage of Completion", "value": round(total_percentage_of_completion,2)},
            {"label": "Total Project Amount", "value": total_project_amount},
            {"label": "Total Amount Received", "value": sum(sales_invoice_net_totals)},
            {"label": "Pending Amount", "value": round(total_project_amount - sum(sales_invoice_net_totals),2)}
        ]

    chart_data = {
        "data": {
            "labels": [],
            "datasets": [
                {"name": "Percentage of Completion", "values": [], "chartType": "bar"},
                {"name": "Project Amount", "values": [], "chartType": "bar"}
            ]
        },
        "type": "bar",
        "colors": ["#3498db", "#2ecc71"]  # Blue, Green
    }

    for row in data:
        chart_data["data"]["labels"].append(row["name1"] or "")
        chart_data["data"]["datasets"][0]["values"].append(row["percentage_of_completion"] or 0)
        chart_data["data"]["datasets"][1]["values"].append(row["project_amount"] or 0)

    return columns, data, None, chart_data, summary

