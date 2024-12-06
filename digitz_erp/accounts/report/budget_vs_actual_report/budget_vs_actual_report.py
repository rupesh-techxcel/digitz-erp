import frappe
from digitz_erp.api.accounts_api import fetch_budget_utilization

def execute(filters=None):
    if not filters:
        filters = {}

    # Validate mandatory filters
    validate_filters(filters)

    # Build a budget filter for fetching budgets
    budget_filter = build_budget_filter(filters)
    
    print("budget_filter")
    print(budget_filter)
    
    budgets = frappe.get_all(
        "Budget",
        filters=budget_filter,
        fields=["name", "budget_against", "company", "project", "cost_center"]
    )

    if not budgets:
        return get_empty_result()

    # Initialize data and chart details
    data = []
    chart_data = {"labels": [], "datasets": []}
    budget_values, utilized_values = [], []

    for budget in budgets:
        
        print("budget")
        print(budget)
        
        total_budget = 0
        total_utilized = 0

        # Fetch budget items for the current budget
        budget_items = frappe.get_all(
            "Budget Item",
            filters={"parent": budget["name"]},
            fields=["reference_type", "reference_value", "budget_amount"]
        )
        
        print("budget_items")
        print(budget_items)
        utilized = 0

        for item in budget_items:
            
            print("here")
            
            utilization_data = None
            print("budget")
            print(budget)
            
            if budget.budget_against  == "Project":
                
                print("Project")
                print("reference_type")
                print(item["reference_type"])
                
                # Calculate utilization for each Budget Item
                utilization_data = fetch_budget_utilization(
                    reference_type=item["reference_type"],
                    reference_value=item["reference_value"],  
                    transaction_date=frappe.utils.today(),                  
                    project=budget.get("project"),
                    company =budget.get("company")
                )                
                
            elif budget.budget_against == "Company":
                # Calculate utilization for each Budget Item
                utilization_data = fetch_budget_utilization(
                    reference_type=item["reference_type"],
                    reference_value=item["reference_value"],
                    transaction_date=frappe.utils.today(),
                    company=budget.get("company")
                )
            elif budget.budget_against == "Cost Center":
                # Calculate utilization for each Budget Item
                utilization_data = fetch_budget_utilization(
                    reference_type=item["reference_type"],
                    reference_value=item["reference_value"],                                       
                    cost_center=budget.get("cost_center")
                )
            
            print("utilization_data")
            print(utilization_data)

            if utilization_data:
                utilized = utilization_data.get("utilized", 0)            
                total_utilized += utilized
                total_budget += item.get("budget_amount", 0)

        # Append data to the report
        data.append({
            "Budget Name": budget["name"],
            "Budget Against": budget["budget_against"],
            "Company": budget.get("company") or "-",
            "Project": budget.get("project") or "-",
            "Cost Center": budget.get("cost_center") or "-",
            "Budget Amount": total_budget,
            "Utilized Amount": total_utilized,
            "Remaining Amount": total_budget - total_utilized
        })

        # Append chart data
        budget_values.append(total_budget)
        utilized_values.append(total_utilized)
        chart_data["labels"].append(budget["name"])

    # Prepare chart datasets
    chart_data["datasets"] = [
        {"name": "Budget", "values": budget_values},
        {"name": "Utilized", "values": utilized_values}
    ]

    return get_columns(), data, {"type": "bar", "data": chart_data}


def validate_filters(filters):
    """
    Validate filters based on 'budget_against'.
    """
    if not filters.get("budget_against"):
        frappe.throw("Please select a value for 'Budget Against'.")

    if filters["budget_against"] == "Company" and not filters.get("company"):
        frappe.throw("Please select a 'Company'.")
    if filters["budget_against"] == "Project" and not filters.get("project"):
        frappe.throw("Please select a 'Project'.")
    if filters["budget_against"] == "Cost Center" and not filters.get("cost_center"):
        frappe.throw("Please select a 'Cost Center'.")


def build_budget_filter(filters):
    """
    Build a filter dictionary for fetching budgets.
    """
    budget_filter = {"budget_against": filters.get("budget_against")}

    if filters["budget_against"] == "Company":
        budget_filter["company"] = filters.get("company")
    elif filters["budget_against"] == "Project":
        budget_filter["project"] = filters.get("project")
    elif filters["budget_against"] == "Cost Center":
        budget_filter["cost_center"] = filters.get("cost_center")

    return {k: v for k, v in budget_filter.items() if v}  # Remove any empty values


def get_columns():
    """
    Define columns for the report.
    """
    return [
        {"fieldname": "Budget Name", "label": "Budget Name", "fieldtype": "Data", "width": 200},
        {"fieldname": "Budget Against", "label": "Budget Against", "fieldtype": "Data", "width": 120},
        {"fieldname": "Company", "label": "Company", "fieldtype": "Link", "options": "Company", "width": 150},
        {"fieldname": "Project", "label": "Project", "fieldtype": "Link", "options": "Project", "width": 150},
        {"fieldname": "Cost Center", "label": "Cost Center", "fieldtype": "Link", "options": "Cost Center", "width": 150},
        {"fieldname": "Budget Amount", "label": "Budget Amount", "fieldtype": "Currency", "width": 150},
        {"fieldname": "Utilized Amount", "label": "Utilized Amount", "fieldtype": "Currency", "width": 150},
        {"fieldname": "Remaining Amount", "label": "Remaining Amount", "fieldtype": "Currency", "width": 150},
    ]


def get_empty_result():
    """
    Return empty results for the report.
    """
    return get_columns(), [], {"type": "bar", "data": {"labels": [], "datasets": []}}
