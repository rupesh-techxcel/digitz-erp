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
def fetch_budget_utilization_for_report(budget_against,budget_for):
    pass

@frappe.whitelist()
def fetch_budget_utilization(reference_type, reference_value, transaction_date=None, company=None, project=None, cost_center=None):

    print("fetch_budget_utilization")

    """
    This method will calculate the actual utilization of the reference_value for the criterias passed 
    like company, project, cost_center and transaction_date(transaction_date is relavant in case checking
    is happening based on a company, sicne for budget's with company it belongs to a particular fiscal year).

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
    budget_against = None
    budget_utilized_values = {}

    for budget in budgets:
        
        budget_against_value = None
        
        if budget["budget_against"] == "Project":
            budget_against_value = budget["project"]
        elif budget["budget_against"] == "Cost Center":
            budget_against_value = budget["cost_center"]
        elif budget["budget_against"] == "Company":
            budget_against_value = budget["company"]            
        
        from_date = None
        to_date = None
        
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

        # Also check the actual value of the corresponding group's utilized value
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
                
        # Note that while checking the parent_account of the account we dont consider the tree structure
        # but only the immediate parent is considered.
        if reference_type == "Account":
            account_group = frappe.db.get_value("Account", reference_value, "parent_account")
            if item_group:
                group_budget_accounts = frappe.get_all(
                    "Budget Item",
                    filters={
                        "parent": budget["name"],
                        "reference_type": "Account Group",
                        "reference_value": account_group
                    },
                    fields=["budget_against", "budget_amount"]
                )

        # Combine both Item and Item Group budgets
        budget_items = budget_items + group_budget_items + group_budget_accounts

        if not budget_items:
            continue

        for item in budget_items:
            # Add to total budget
            # total_budget += item.get("budget_amount", 0)
            
            print("item")
            print(item)
            
            item_reference_type = item["reference_type"]
            item_reference_value = item["reference_value"]
            
            # Step 3: Calculate utilization for this budget item
            utilized = calculate_utilization(
                budget["budget_against"],item["budget_against"], budget_against_value,  item_reference_type, item_reference_value,from_date,to_date
            )           
            
            budget_utilized_values[budget_against_value] = utilized
        
    lowest_budget = None
    lowest_budget_against = None       
    if budget_utilized_values:   
        # Iterate through the budget_utilized_values
        lowest_budget_against = min(budget_utilized_values, key=budget_utilized_values.get)
        lowest_budget = budget_utilized_values[lowest_budget]

    # Step 4: Return results
    return {
        "no_budget": False,
        "utilized": total_utilized,
        "budget_against":lowest_budget_against,
        "budget": lowest_budget
    }

def get_balance_budget_value(reference_type, reference_value, transaction_date=None, company=None, project=None, cost_center=None):
    """
    Identify the maximum allowable balance value based on the budget.

    Arguments:
        reference_type (str): The type of reference ('Item', 'Account', 'Designation').
        reference_value (str): The value of the reference (e.g., item_code, account_name, or designation).
        transaction_date (str): The transaction date (optional).
        company (str): The company (optional).
        project (str): The project (optional).
        cost_center (str): The cost center (optional).

    Returns:
        dict: Information about the budget utilization, including no_budget, utilized, budget, remaining, and details.
    """
    import datetime

    # Ensure transaction_date is a valid date
    if transaction_date and isinstance(transaction_date, str):
        transaction_date = datetime.datetime.strptime(transaction_date, "%Y-%m-%d").date()

    # Initialize variables
    min_balance_value = float("inf")
    minimum_budget = {}

    def process_budget(budget_against, budget_against_value, from_date=None, to_date=None):
        """
        Process budgets for a specific budget type (Project, Cost Center, or Company).
        """
        nonlocal min_balance_value, minimum_budget

        budgets = frappe.get_all(
            "Budget",
            filters={budget_against.lower(): budget_against_value},
            fields=["name", "budget_against", "from_date", "to_date"]
        )

        for budget in budgets:
            # Validate date range for Company budgets
            if budget_against == "Company":
                budget_from_date = budget.get("from_date")
                budget_to_date = budget.get("to_date")

                if isinstance(budget_from_date, str):
                    budget_from_date = datetime.datetime.strptime(budget_from_date, "%Y-%m-%d").date()
                if isinstance(budget_to_date, str):
                    budget_to_date = datetime.datetime.strptime(budget_to_date, "%Y-%m-%d").date()

                if not budget_from_date or not budget_to_date:
                    frappe.throw("Company budgets must have a valid date range.")

                if transaction_date and not (budget_from_date <= transaction_date <= budget_to_date):
                    continue

            budget_items = frappe.get_all(
                "Budget Item",
                filters={
                    "parent": budget["name"],
                    "reference_type": reference_type,
                    "reference_value": reference_value
                },
                fields=["budget_against", "budget_amount"]
            )

            for item in budget_items:
                budget_amount = item.get("budget_amount", 0)
                utilized = calculate_utilization(
                    budget_against=budget["budget_against"],
                    item_budget_against=item["budget_against"],
                    budget_against_value=budget_against_value,
                    reference_type=reference_type,
                    reference_value=reference_value,
                    from_date=from_date,
                    to_date=to_date
                )

                balance_value = budget_amount - utilized

                # Considering lesser value here to restrict the actual input only upto that value
                if min_balance_value > balance_value :
                    min_balance_value = balance_value
                    minimum_budget = {
                        "Budget Against": budget["budget_against"],
                        "Reference Type": reference_type,
                        "Budget Amount": budget_amount,
                        "Used Amount": utilized,
                        "Available Balance": balance_value
                    }

                if reference_type == "Item":
                    item_group = frappe.db.get_value("Item", reference_value, "item_group")
                    if item_group:
                        process_item_group_budget(
                            budget["name"], budget["budget_against"], budget_against_value, item_group, from_date, to_date
                        )
                
                if reference_type == "Account":
                    account_group = frappe.db.get_value("Account", reference_value, "parent_account")
                    if parent_account:
                        process_account_group_budget(
                            budget["name"], budget["budget_against"], budget_against_value, account_group, from_date, to_date
                        )

    def process_item_group_budget(parent_budget, budget_against, budget_against_value, item_group, from_date=None, to_date=None):
        """
        Process budgets for the item group related to an item.
        """
        nonlocal min_balance_value, minimum_budget

        budget_items_for_item_group = frappe.get_all(
            "Budget Item",
            filters={
                "parent": parent_budget,
                "reference_type": "Item Group",
                "reference_value": item_group
            },
            fields=["budget_against", "budget_amount"]
        )

        for item2 in budget_items_for_item_group:
            utilized = calculate_utilization(
                budget_against=budget_against,
                item_budget_against=item2["budget_against"],
                budget_against_value=budget_against_value,
                reference_type="Item Group",
                reference_value=item_group,
                from_date=from_date,
                to_date=to_date
            )
            
            balance_value = item2["budget_amount"] - utilized

            # Considering lesser value here to restrict the actual input only upto that value
            if min_balance_value > balance_value:
                min_balance_value = balance_value
                minimum_budget = {
                    "Budget Against": budget_against,
                    "Reference Type": "Item Group",
                    "Budget Amount": item2["budget_amount"],
                    "Used Amount": utilized,
                    "Available Balance": balance_value
                }
                
    def process_account_group_budget(parent_budget, budget_against, budget_against_value, account_group, from_date=None, to_date=None):
        """
        Process budgets for the item group related to an item.
        """
        nonlocal min_balance_value, minimum_budget
        
        budget_items_for_account_group = frappe.get_all(
            "Budget Item",
            filters={
                "parent": parent_budget,
                "reference_type": "Account Group",
                "reference_value": account_group
            },
            fields=["budget_against", "budget_amount"]
        )

        for item3 in budget_items_for_account_group:
            utilized = calculate_utilization(
                budget_against=budget_against,
                item_budget_against=item3["budget_against"],
                budget_against_value=budget_against_value,
                reference_type="Account Group",
                reference_value=account_group,
                from_date=from_date,
                to_date=to_date
            )
            
            balance_value = item3["budget_amount"] - utilized

            # Considering lesser value here to restrict the actual input only upto that value
            if min_balance_value > balance_value:
                min_balance_value = balance_value
                minimum_budget = {
                    "Budget Against": budget_against,
                    "Reference Type": "Account Group",
                    "Budget Amount": item2["budget_amount"],
                    "Used Amount": utilized,
                    "Available Balance": balance_value
                }

    # Process each budget type
    if project:
        process_budget("Project", project)

    # Keep Cost_Center as it is not 'Cost Center' since it is converting to field cost_center in the process method
    if cost_center:
        process_budget("Cost_Center", cost_center)

    if company:
        process_budget("Company", company)

    # Return results
    if min_balance_value == float("inf"):
        return {
            "no_budget": True,
            "utilized": 0,
            "budget": 0,
            "remaining": 0,
            "details": {
                "Budget Against": None,
                "Reference Type": None,
                "Budget Amount": 0,
                "Used Amount": 0,
                "Available Balance": 0
            }
        }

    return {
        "no_budget": False,
        "utilized": minimum_budget.get("Used Amount", 0),
        "budget": minimum_budget.get("Budget Amount", 0),
        "remaining": minimum_budget.get("Available Balance", 0),
        "details": minimum_budget
    }


def calculate_utilization(
    budget_against,
    item_budget_against,
    budget_against_value,
    reference_type,
    reference_value,
    from_date,
    to_date,
):
    """
    Helper function to calculate utilization based on budget type and dimensions.
    """
    utilized = 0
    conditions = []

    # Parent table filters
    if budget_against == "Project":
        conditions.append(f"parent_table.project = '{budget_against_value}'")
    elif budget_against == "Cost Center":
        conditions.append(f"parent_table.cost_center = '{budget_against_value}'")
    elif budget_against == "Company":
        conditions.append(
            f"parent_table.company = '{budget_against_value}' AND posting_date >= '{from_date}' AND posting_date <= '{to_date}'"
        )

    # Reference-specific filters
    if reference_type == "Item":
        conditions.append(f"child_table.item = '{reference_value}'")
    elif reference_type == "Item Group":
        conditions.append(f"item_table.item_group = '{reference_value}'")
    elif reference_type == "Account":
        conditions.append(f"expense_table.account = '{reference_value}'")
    elif reference_type == "Account Group":
        conditions.append(
            f"""
            expense_table.account IN (
                SELECT name
                FROM `tabAccount`
                WHERE parent_account = '{reference_value}'
            )
            """
        )
    elif reference_type == "Designation":
        conditions.append(f"employee_table.designation = '{reference_value}'")

    where_clause = " AND ".join(conditions)

    # Calculate utilization based on item_budget_against
    if item_budget_against == "Purchase":
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

    elif item_budget_against == "Expense":
        # Expense Entry Details for Account and Account Group
        expense_total = frappe.db.sql(
            f"""
            SELECT SUM(expense_table.amount) AS total
            FROM `tabExpense Entry Details` AS expense_table
            INNER JOIN `tabExpense Entry` AS parent_table ON expense_table.parent = parent_table.name
            WHERE {where_clause}
            """,
            as_dict=True,
        )[0].get("total", 0) or 0

        utilized = expense_total

    elif item_budget_against == "Labour":
        # Labour Utilization from Timesheet with Employee Table Join
        labour_total = frappe.db.sql(
            f"""
            SELECT SUM(timesheet_detail.labour_cost) AS total
            FROM `tabTimeSheet Entry Detail` AS timesheet_detail
            INNER JOIN `tabTimeSheet Entry` AS parent_table ON timesheet_detail.parent = parent_table.name
            INNER JOIN `tabEmployee` AS employee_table ON timesheet_detail.employee = employee_table.name
            WHERE {where_clause}
            """,
            as_dict=True,
        )[0].get("total", 0) or 0

        utilized = labour_total

    return utilized

