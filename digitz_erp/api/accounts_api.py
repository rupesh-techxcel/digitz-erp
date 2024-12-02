import frappe
from datetime import datetime

@frappe.whitelist()
def get_customer_balance(supplier):
    today = datetime.today().date()

    sql_query = """
        SELECT SUM(credit_amount) - SUM(debit_amount) as supplier_balance FROM `tabGL Posting` WHERE party_type='Customer' AND party=%s AND posting_date <= %s"""
    data = frappe.db.sql(sql_query, (supplier, today), as_dict=True)
    return data
    
@frappe.whitelist()
def get_supplier_balance(supplier):
    today = datetime.today().date()

    sql_query = """
        SELECT SUM(credit_amount) - SUM(debit_amount) as supplier_balance FROM `tabGL Posting` WHERE party_type='Supplier' AND party=%s AND DATE(posting_date) <= %s """
    data = frappe.db.sql(sql_query, (supplier, today), as_dict=True)
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
def fetch_budget_utilization(budget_against, reference_type, reference_value, company=None, project=None, cost_center=None, from_date=None, to_date=None):
    """
    Fetch budget utilization values for the given criteria.

    :param budget_against: 'Purchase', 'Expense', or 'Labour'
    :param reference_type: 'Item', 'Item Group', 'Account', 'Account Group', or 'Designation'
    :param reference_value: The specific value of the reference type (e.g., Item name, Account name, Designation name)
    :param company: Company to filter
    :param project: Project to filter
    :param cost_center: Cost center to filter
    :param from_date: Start date of the range (relevant only for 'Company')
    :param to_date: End date of the range (relevant only for 'Company')
    :return: A dictionary containing utilized, budget amount, and whether a budget exists
    """

    # Step 1: Validate budget availability
    filters = {
        "budget_against": budget_against,
        "company": company,
        "project": project,
        "cost_center": cost_center,
    }
    budget = frappe.get_all("Budget", filters=filters, fields=["name", "total_budget_amount"])

    if not budget:
        # No budget exists for the specified criteria
        return {"no_budget": True, "utilized": 0, "budget": 0}

    budget_amount = budget[0].get("total_budget_amount", 0)

    # Step 2: Initialize conditions for utilization queries
    conditions = []

    # Add filters based on the budget dimensions
    if company:
        conditions.append(f"`company` = '{company}'")
    if project:
        conditions.append(f"`project` = '{project}'")
    if cost_center:
        conditions.append(f"`cost_center` = '{cost_center}'")

    # Include date range filters only if 'Company' is the budget dimension
    if budget_against == "Company" and from_date and to_date:
        conditions.append(f"`posting_date` BETWEEN '{from_date}' AND '{to_date}'")

    # Add reference filters based on `reference_type` and `reference_value`
    if reference_type == "Item":
        conditions.append(f"`item_code` = '{reference_value}'")
    elif reference_type == "Item Group":
        conditions.append(f"`item_group` = '{reference_value}'")
    elif reference_type == "Account":
        conditions.append(f"`account` = '{reference_value}'")
    elif reference_type == "Account Group":
        accounts = frappe.get_all("Account", filters={"parent_account": reference_value}, pluck="name")
        account_conditions = ", ".join([f"'{acc}'" for acc in accounts])
        conditions.append(f"`account` IN ({account_conditions})")
    elif reference_type == "Designation":
        conditions.append(f"`designation` = '{reference_value}'")

    where_clause = " AND ".join(conditions)

    # Step 3: Calculate utilized amounts based on budget_against
    utilized = 0

    if budget_against == "Purchase":
        # Fetch utilization from Purchase-related tables
        purchase_order_total = frappe.db.sql(
            f"""
            SELECT SUM(`gross_amount`) AS total
            FROM `tabPurchase Order Item`
            WHERE {where_clause}
            """,
            as_dict=True,
        )[0].get("total", 0)

        purchase_receipt_total = frappe.db.sql(
            f"""
            SELECT SUM(`gross_amount`) AS total
            FROM `tabPurchase Receipt Item`
            WHERE {where_clause}
            """,
            as_dict=True,
        )[0].get("total", 0)

        purchase_invoice_total = frappe.db.sql(
            f"""
            SELECT SUM(`gross_amount`) AS total
            FROM `tabPurchase Invoice Item`
            WHERE {where_clause}
            """,
            as_dict=True,
        )[0].get("total", 0)

        utilized = max(purchase_order_total, purchase_receipt_total, purchase_invoice_total)

    elif budget_against == "Expense":
        # Fetch utilization from GL Entry
        utilized = frappe.db.sql(
            f"""
            SELECT SUM(`debit_amount`) AS total
            FROM `tabGL Entry`
            WHERE {where_clause}
            """,
            as_dict=True,
        )[0].get("total", 0)

    elif budget_against == "Labour":
        # Fetch utilization from Time Sheet Entry Detail
        utilized = frappe.db.sql(
            f"""
            SELECT SUM(`labour_cost`) AS total
            FROM `tabTime Sheet Entry Detail`
            INNER JOIN `tabTime Sheet Entry` AS parent
            ON `tabTime Sheet Entry Detail`.`parent` = parent.`name`
            WHERE {where_clause}
            """,
            as_dict=True,
        )[0].get("total", 0)

    # Step 4: Return results
    return {
        "no_budget": False,
        "utilized": utilized,
        "budget": budget_amount
    }

