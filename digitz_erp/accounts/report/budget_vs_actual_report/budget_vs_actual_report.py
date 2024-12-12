import frappe
from frappe.utils import flt
from digitz_erp.api.accounts_api import calculate_utilization


def execute(filters=None):
    """
    Generate the Budget Vs Actual Report with chart data.

    Arguments:
        filters (dict): Filters selected in the report.

    Returns:
        tuple: (columns, data, chart) for the report.
    """
    if not filters:
        filters = {}

    # Get columns, data, and chart data
    columns = get_columns()
    data = prepare_data(filters)
    
    print("data")
    print(data)
    chart = prepare_chart_data(data)

    return columns, data, chart


def get_columns():
    """
    Define the columns for the report.

    Returns:
        list: Columns for the report.
    """
    return [
        {"label": "Budget Name", "fieldname": "budget_name", "fieldtype": "Data", "width": 150},
        {"label": "Budget Against", "fieldname": "budget_against", "fieldtype": "Data", "width": 120},
        {"label": "Selected Value", "fieldname": "selected_value", "fieldtype": "Data", "width": 150},
        {"label": "Reference Type", "fieldname": "reference_type", "fieldtype": "Data", "width": 120},
        {"label": "Reference Value", "fieldname": "reference_value", "fieldtype": "Data", "width": 150},
        {"label": "Budget Amount", "fieldname": "budget_amount", "fieldtype": "Currency", "width": 120},
        {"label": "Utilized Amount", "fieldname": "utilized_amount", "fieldtype": "Currency", "width": 120},
    ]


def prepare_data(filters):
    """
    Prepare the tabular data for the report.

    Arguments:
        filters (dict): Filters selected in the report.

    Returns:
        list: Tabular data for the report.
    """
    # Validate filters
    if not filters.get("budget_against"):
        frappe.throw("Please select a Budget Against value ('Project', 'Cost Center', or 'Company').")

    from_date, to_date = None, None
    if filters.get("budget_against") == "Company" and filters.get("fiscal_year"):
        fiscal_year = frappe.db.get_value("Fiscal Year", filters.get("fiscal_year"), ["year_start_date", "year_end_date"], as_dict=True)
        if not fiscal_year:
            frappe.throw("Invalid Fiscal Year selected.")
        from_date = fiscal_year.year_start_date
        to_date = fiscal_year.year_end_date

    budget_field = filters.get("budget_against").lower()
    budget_value = filters.get(budget_field)

    budgets = frappe.get_all(
        "Budget",
        filters={budget_field: budget_value},
        fields=["name", "budget_against", "from_date", "to_date"]
    )

    data = []
    
    budget_against_value = (
    filters.get("project") if filters.get("budget_against") == "Project" else
    filters.get("cost_center") if filters.get("budget_against") == "Cost Center" else
    filters.get("company") if filters.get("budget_against") == "Company" else None
    )

    for budget in budgets:
        if budget["budget_against"] == "Company" and (from_date or to_date):
            if not (budget["from_date"] <= from_date <= budget["to_date"]) or not (budget["from_date"] <= to_date <= budget["to_date"]):
                continue

        budget_items = frappe.get_all(
            "Budget Item",
            filters={"parent": budget["name"]},
            fields=["budget_against","reference_type", "reference_value", "budget_amount"]
        )
        
        for item in budget_items:
            utilized = calculate_utilization(
                budget_against=budget["budget_against"],
                item_budget_against=item["budget_against"],
                budget_against_value=budget_against_value,
                reference_type=item["reference_type"],
                reference_value=item["reference_value"],
                from_date=from_date,
                to_date=to_date,
            )

            # Debugging log for utilization
            print(f"Budget: {budget['name']}, Item: {item['reference_value']}, "
                  f"Utilized: {utilized}, Budget Amount: {item['budget_amount']}")

            data.append({
                "budget_name": budget["name"],
                "budget_against": budget["budget_against"],
                "selected_value": budget_value,
                "reference_type": item["reference_type"],
                "reference_value": item["reference_value"],
                "budget_amount": flt(item["budget_amount"]),
                "utilized_amount": flt(utilized),
            })
    
    print("data")
    print(data)

    return data


def prepare_chart_data(data):
    """
    Prepare the chart data from the tabular data.

    Arguments:
        data (list): Tabular data for the report.

    Returns:
        dict: Chart data for the report.
    """
    chart_labels = []
    budget_values = []
    utilized_values = []

    for row in data:
        chart_labels.append(f"{row['reference_type']} ({row['reference_value']})")
        budget_values.append(row["budget_amount"])
        utilized_values.append(row["utilized_amount"])

    return {
        "data": {
            "labels": chart_labels,
            "datasets": [
                {"name": "Budget Amount", "values": budget_values},
                {"name": "Utilized Amount", "values": utilized_values},
            ]
        },
        "type": "bar"
    }
