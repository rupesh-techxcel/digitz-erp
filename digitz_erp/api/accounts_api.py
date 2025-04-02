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

@frappe.whitelist()
def get_balance_budget_value(reference_type, reference_value, doc_type, doc_name, transaction_date=None, company=None, project=None, cost_center=None):
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
  
    global min_balance_value, minimum_budget
    min_balance_value = float("inf")
    minimum_budget = {}

    if transaction_date and isinstance(transaction_date, str):
        transaction_date = datetime.datetime.strptime(transaction_date, "%Y-%m-%d").date()
    
    # Note that the conditions project, cost_center and company can occur at a time and the system
    # should return the maximum allowed budget balance based on all of them for the passing reference_type and reference_value
    
    # Process budgets for project and cost center
    if project:        
        process_budget("Project", project, doc_type, doc_name, transaction_date, reference_type, reference_value)
    
    if cost_center:
        process_budget("Cost Center", cost_center,doc_type,doc_name, transaction_date, reference_type, reference_value)

    # process_budget("Company", company,doc_type,doc_name, transaction_date, reference_type, reference_value)

    if min_balance_value == float("inf"):
        print("no_budget")
        return {
            "no_budget": True,
            "utilized": 0,
            "budget": 0,
            "remaining": 0,
            "details": {}
        }
        
    
    print("no_budget=false")

    return {
        "no_budget": False,
        "utilized": minimum_budget.get("Used Amount", 0),
        "budget": minimum_budget.get("Budget Amount", 0),
        "remaining": minimum_budget.get("Available Balance", 0),
        "details": minimum_budget
    }


def process_budget(budget_against, budget_against_value,doc_type,doc_name, transaction_date, reference_type, reference_value):
    """
    Process budgets for a specific budget type (Project, Cost Center, or Company).
    """
    global min_balance_value, minimum_budget

    filters = {budget_against.lower(): budget_against_value}
    
    # Verify whether budget has configured to apply for Purchase Receipt
    
    material_request = False
    purchase_order = False
    purchase_receipt = False    
    purchase_invoice = False

    # Apply additional filters based on the document type
    if doc_type == "Material Request":
        filters["material_request"] = True
    elif doc_type == "Purchase Receipt":
        filters["purchase_receipt"] = True
    elif doc_type == "Purchase Order":
        filters["purchase_order"] = True
    elif doc_type == "Purchase Invoice":
        filters["purchase_invoice"] = True

    budgets = frappe.get_all(
        "Budget",
        filters=filters,
        fields=["name", "budget_against", "from_date", "to_date"]
    )
    
    print(budgets)
    
    for budget in budgets:
        # For budget set for company, verify the transation_date with the budget_from_date and budget_to_date
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
        
        # In item budget_against is "Purchase"
        # Reference Type is "Item"
        # Reference Value is "ITEM 1"        
        # "budget_against" can be "Project","Cost Center" or may be "Company" based on the value assigned in the 'Budget'
        
        for item in budget_items:
            budget_amount = item.get("budget_amount", 0)
            utilized = calculate_utilization(
                budget_against=budget["budget_against"], # Company/Project/Cost Center
                budget_against_value=budget_against_value, # Eg:Project Name
                item_budget_against=item["budget_against"], # Eg:Purchase                
                doc_type = doc_type,
                doc_name = doc_name, #Passing to exclude the current document values, and to be handled from document itself
                reference_type=reference_type,
                reference_value=reference_value,
                from_date=None,
                to_date=None
            )

            balance_value = budget_amount - utilized

            if min_balance_value > balance_value:
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
                process_item_group_budget(budget["name"], budget["budget_against"], budget_against_value, item_group,doc_type,doc_name)

        if reference_type == "Account":
            account_group = frappe.db.get_value("Account", reference_value, "parent_account")
            if account_group:
                process_account_group_budget(budget["name"], budget["budget_against"], budget_against_value, account_group)


def process_item_group_budget(parent_budget, budget_against, budget_against_value, item_group,doc_type,doc_name):
    """
    Process budgets for the item group related to an item.
    """
    global min_balance_value, minimum_budget

    budget_items_for_item_group = frappe.get_all(
        "Budget Item",
        filters={
            "parent": parent_budget,
            "reference_type": "Item Group",
            "reference_value": item_group
        },
        fields=["budget_against", "budget_amount"]
    )

    for item in budget_items_for_item_group:
        utilized = calculate_utilization(
            budget_against=budget_against,   #Company/Project/Cost Center
            budget_against_value=budget_against_value, #Project Name
            item_budget_against=item["budget_against"], #Purchase , Expense , Labour       
            doc_type = doc_type,
            doc_name = doc_name,
            reference_type="Item Group",
            reference_value=item_group,
            from_date=None,
            to_date=None
        )

        balance_value = item["budget_amount"] - utilized

        if min_balance_value > balance_value:
            min_balance_value = balance_value
            minimum_budget = {
                "Budget Against": budget_against,
                "Reference Type": "Item Group",
                "Budget Amount": item["budget_amount"],
                "Used Amount": utilized,
                "Available Balance": balance_value
            }


def process_account_group_budget(parent_budget, budget_against, budget_against_value, account_group):
    """
    Process budgets for the account group related to an account.
    """
    global min_balance_value, minimum_budget

    budget_items_for_account_group = frappe.get_all(
        "Budget Item",
        filters={
            "parent": parent_budget,
            "reference_type": "Account Group",
            "reference_value": account_group
        },
        fields=["budget_against", "budget_amount"]
    )

    for item in budget_items_for_account_group:
        utilized = calculate_utilization(
            budget_against=budget_against,
            budget_against_value=budget_against_value,
            doc_type = None,
            doc_name = None,
            item_budget_against=item["budget_against"],            
            reference_type="Account Group",
            reference_value=account_group,
            from_date=None,
            to_date=None
        )

        balance_value = item["budget_amount"] - utilized

        if min_balance_value > balance_value:
            min_balance_value = balance_value
            minimum_budget = {
                "Budget Against": budget_against,
                "Reference Type": "Account Group",
                "Budget Amount": item["budget_amount"],
                "Used Amount": utilized,
                "Available Balance": balance_value
            }

@frappe.whitelist()
def calculate_utilization(
    budget_against,
    budget_against_value,
    item_budget_against,    
    doc_type,
    doc_name,
    reference_type,
    reference_value,
    from_date,
    to_date,
):
    """
    Helper function to calculate utilization based on budget type and dimensions.
    """
    
    print(budget_against)
    print(item_budget_against)
    print(budget_against_value)
    print(reference_type)
    print(reference_value)
    
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
        conditions.append(f"expense_table.expense_account = '{reference_value}'")
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
        
    # Exclude current document
    conditions.append(f"parent_table.name != '{doc_name}'")
    conditions.append(f"parent_table.docstatus =1")

    where_clause = " AND ".join(conditions)

    # Calculate utilization based on item_budget_against
    if item_budget_against == "Purchase":
        # Purchase Order
        purchase_order_total = 0
        if doc_type == "Purchase Order":
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

        purchase_receipt_total = 0
        
        if(doc_type == "Purchase Receipt"):
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

        purchase_invoice_total = 0
        if doc_type == "Purchase Invoice":
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
        
        material_request_total = 0
        if doc_type == "Material Request":
            # Purchase Invoice
            material_request_total = frappe.db.sql(
                f"""
                SELECT SUM(child_table.qty* child_table.valuation_rate) AS total
                FROM `tabMaterial Request Item` AS child_table
                INNER JOIN `tabMaterial Request` AS parent_table ON child_table.parent = parent_table.name
                INNER JOIN `tabItem` AS item_table ON child_table.item = item_table.item_code
                WHERE {where_clause}
                """,
                as_dict=True,
            )[0].get("total", 0) or 0

        utilized = max(material_request_total,purchase_order_total, purchase_receipt_total, purchase_invoice_total)

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

