import frappe
from datetime import datetime

@frappe.whitelist()
def get_customer_balance(supplier):
    today = datetime.today().date()

    sql_query = """
        SELECT SUM(credit_amount) - SUM(debit_amount) as supplier_balance FROM `tabGL Posting` WHERE party_type='Customer' AND party=%s AND posting_date <= %s"""
    data = frappe.db.sql(sql_query, (supplier, today), as_dict=True)
    
    print("returns customer balance")
    
    return data
    
import frappe
from datetime import datetime

@frappe.whitelist()
def get_supplier_balance(supplier, date=None):
    """
    Fetch the supplier balance as of a specific date or today if no date is provided.

    :param supplier: The supplier for whom to fetch the balance.
    :param date: (Optional) The date up to which the balance is calculated. Defaults to today.
    :return: Supplier balance as a dictionary.
    """
    # Use today's date if no date is provided
    if not date:
        date = datetime.today().strftime('%Y-%m-%d')  # Format as 'YYYY-MM-DD'

    # Debugging the date and supplier
    print(f"Fetching balance for supplier: {supplier}, Date: {date}")

    sql_query = """
        SELECT SUM(credit_amount) - SUM(debit_amount) as supplier_balance 
        FROM `tabGL Posting` 
        WHERE party_type='Supplier' AND party=%s AND posting_date <= %s
    """
    data = frappe.db.sql(sql_query, (supplier, date), as_dict=True)

    return data


@frappe.whitelist()
def get_stock_ledgers(voucher,voucher_no):
    stock_ledgers = frappe.get_all("Stock Ledger",
                                    filters={"voucher":voucher,"voucher_no": voucher_no},
                                    fields=["name", "item","item_name", "warehouse", "qty_in", "qty_out", "valuation_rate", "balance_qty", "balance_value"])
    formatted_stock_ledgers = []
    for ledgers in stock_ledgers:
        formatted_stock_ledgers.append({
            "stock_ledger": ledgers.name,
            "item": ledgers.item,
            "item_name":ledgers.item_name,
            "warehouse": ledgers.warehouse,
            "qty_in": ledgers.qty_in,
            "qty_out": ledgers.qty_out,
            "valuation_rate": ledgers.valuation_rate,
            "balance_qty": ledgers.balance_qty,
            "balance_value": ledgers.balance_value
        })
    
    return formatted_stock_ledgers

@frappe.whitelist()
def get_stock_ledgers_project(voucher,voucher_no):
    project_stock_ledger = frappe.get_all("Project Stock Ledger",
                                    filters={"voucher":voucher,"voucher_no": voucher_no},
                                    fields=["name", "item","item_name", "project", "consumed_qty", "qty_in", "qty_out", "valuation_rate", "balance_qty", "balance_value"])
    formatted_project_stock_ledger = []
    for ledgers in project_stock_ledger:
        formatted_project_stock_ledger.append({
            "stock_ledger": ledgers.name,
            "item": ledgers.item,
            "item_name":ledgers.item_name,
            "project": ledgers.project,
            "qty_in": ledgers.qty_in,
            "qty_out": ledgers.qty_out,
            "valuation_rate": ledgers.valuation_rate,
            "balance_qty": ledgers.balance_qty,
            "balance_value": ledgers.balance_value,
            "consumed_qty": ledgers.consumed_qty
        })
    
    return formatted_project_stock_ledger

@frappe.whitelist()
def get_gl_postings(voucher,voucher_no):
    gl_postings = frappe.get_all("GL Posting",
                                  filters={"voucher_type":voucher,
                                      "voucher_no": voucher_no},
                                  fields=["account", "debit_amount", "credit_amount", "against_account","party", "remarks","project","cost_center"])
    formatted_gl_postings = []
    total_debit = 0
    total_credit = 0
    
    for posting in gl_postings:
        total_debit += posting.debit_amount or 0
        total_credit += posting.credit_amount or 0
        formatted_gl_postings.append({
            "gl_posting": posting.name,
            "account":posting.account,
            "debit_amount": posting.debit_amount,
            "credit_amount": posting.credit_amount,
            "against_account": posting.against_account if posting.against_account else "",
            "remarks": posting.remarks,
            "project":posting.project if posting.project else "",
            "cost_center":posting.cost_center if posting.cost_center else "",
            "party":posting.party if posting.party else ""
        })

    print("formatted_gl_postings")
    print(formatted_gl_postings)
    
    return {
        "gl_postings": formatted_gl_postings,
        "total_debit": total_debit,
        "total_credit": total_credit
    }

import datetime

import datetime
import frappe


@frappe.whitelist()
def fetch_budget_utilization_for_report(budget_against,reference_type, reference_value):
    pass

@frappe.whitelist()
def fetch_budget_utilization(reference_type, reference_value, transaction_date, company=None, project=None, cost_center=None):
    
    print("fetch_budget_utilization")
    
    """
    Fetch budget utilization values for the given criteria across budget items.

    :param reference_type: 'Item', 'Item Group', 'Account', 'Account Group', or 'Designation'
    :param reference_value: The specific value of the reference type (e.g., Item name, Account name, Designation name)
    :param transaction_date: Date of the transaction to find the applicable budget
    :param company: Company to filter (optional)
    :param project: Project to filter (optional)
    :param cost_center: Cost center to filter (optional)
    :return: A dictionary containing utilized, budget amount, and whether a budget exists
    """
    
    print("Params in fetch_budget_utilization")
    
    print(reference_type)
    print(reference_value)
    print(transaction_date)
    print(company)
    print(project)
    print(cost_center)

    # Ensure transaction_date is a valid date
    if company and isinstance(transaction_date, str):
        transaction_date = datetime.datetime.strptime(transaction_date, "%Y-%m-%d").date()

    # Step 1: Fetch budgets based on filters
    budget_filters = {
        "company": company,
        "project": project,
        "cost_center": cost_center
    }

    budgets = frappe.get_all(
        "Budget",
        filters={k: v for k, v in budget_filters.items() if v},
        fields=["name", "from_date", "to_date", "budget_against"]
    )

    if not budgets:
        return {"no_budget": True, "utilized": 0, "budget": 0}

    # Initialize variables
    total_budget = 0
    total_utilized = 0

    for budget in budgets:
        # Apply date range only for 'Company' budgets
        if budget["budget_against"] == "Company":
            from_date = budget.get("from_date")
            to_date = budget.get("to_date")

            # Ensure both from_date and to_date are valid
            if isinstance(from_date, str):
                from_date = datetime.datetime.strptime(from_date, "%Y-%m-%d").date()
            if isinstance(to_date, str):
                to_date = datetime.datetime.strptime(to_date, "%Y-%m-%d").date()

            # Throw error if either date is still None
            if not from_date or not to_date:
                frappe.throw("Company budgets must have a valid date range (from_date and to_date).")

            # Perform comparison only if all dates are valid
            if not (from_date <= transaction_date <= to_date):
                continue

        # Fetch budget items related to the budget
        budget_items = frappe.get_all(
            "Budget Item",
            filters={
                "parent": budget["name"],
                "reference_type": reference_type,
                "reference_value": reference_value
            },
            fields=["budget_against", "budget_amount"]
        )

        # Fetch budget items for the Item Group if reference_type is "Item"
        group_budget_items = []
        if reference_type == "Item":
            item_group = frappe.db.get_value("Item", reference_value, "item_group")
            if item_group:
                group_budget_items = frappe.get_all(
                    "Budget Item",
                    filters={
                        "parent": budget["name"],
                        "reference_type": "Item Group",
                        "reference_value": item_group
                    },
                    fields=["budget_against", "budget_amount"]
                )

        # Combine both Item and Item Group budgets
        budget_items = budget_items + group_budget_items

        if not budget_items:
            continue

        for item in budget_items:
            # Add to total budget
            total_budget += item.get("budget_amount", 0)
            
            print("item")
            print(item)

            # Step 3: Calculate utilization for this budget item
            utilized = calculate_utilization(
                item["budget_against"], company, project, cost_center, reference_type, reference_value
            )

            # Add to total utilized amount
            total_utilized += utilized

    # Step 4: Return results
    return {
        "no_budget": False,
        "utilized": total_utilized,
        "budget": total_budget
    }


def calculate_utilization(budget_against, company, project, cost_center, reference_type, reference_value):
    """
    Helper function to calculate utilization based on budget type and dimensions.
    """
    utilized = 0
    conditions = []

    # Parent table filters
    if project:
        conditions.append(f"parent_table.project = '{project}'")
    if cost_center:
        conditions.append(f"parent_table.cost_center = '{cost_center}'")
    if company:
        conditions.append(f"parent_table.company = '{company}'")

    # Reference-specific filters        
    if reference_type == "Item":
        # Join with Item table to get item_group
        item_group = frappe.db.get_value("Item", reference_value, "item_group")
        if item_group:
            conditions.append(f"item_table.item_group = '{item_group}'")

    elif reference_type == "Item Group":
        conditions.append(f"item_table.item_group = '{reference_value}'")

    where_clause = " AND ".join(conditions)

    # Calculate utilization based on budget_against
    if budget_against in ["Purchase", "Company", "Cost Center"]:
        # Purchase Order
        purchase_order_total = frappe.db.sql(
            f"""
            SELECT SUM(child_table.gross_amount) AS total
            FROM `tabPurchase Order Item` AS child_table
            INNER JOIN `tabPurchase Order` AS parent_table ON child_table.parent = parent_table.name
            INNER JOIN `tabItem` AS item_table ON child_table.item = item_table.item_code
            WHERE {where_clause}
            """,
            as_dict=True,
        )[0].get("total", 0) or 0

        # Purchase Receipt
        purchase_receipt_total = frappe.db.sql(
            f"""
            SELECT SUM(child_table.gross_amount) AS total
            FROM `tabPurchase Receipt Item` AS child_table
            INNER JOIN `tabPurchase Receipt` AS parent_table ON child_table.parent = parent_table.name
            INNER JOIN `tabItem` AS item_table ON child_table.item = item_table.item_code
            WHERE {where_clause}
            """,
            as_dict=True,
        )[0].get("total", 0) or 0

        # Purchase Invoice
        purchase_invoice_total = frappe.db.sql(
            f"""
            SELECT SUM(child_table.gross_amount) AS total
            FROM `tabPurchase Invoice Item` AS child_table
            INNER JOIN `tabPurchase Invoice` AS parent_table ON child_table.parent = parent_table.name
            INNER JOIN `tabItem` AS item_table ON child_table.item = item_table.item_code
            WHERE {where_clause}
            """,
            as_dict=True,
        )[0].get("total", 0) or 0

        utilized = max(purchase_order_total, purchase_receipt_total, purchase_invoice_total)

    return utilized
