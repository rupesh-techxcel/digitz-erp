import frappe
from frappe.utils import add_days, add_months, cint, cstr, flt, formatdate, get_first_day, getdate
import math
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta


@frappe.whitelist()
def get_default_company():
    
    default_company = frappe.db.get_single_value("Global Settings",'default_company')    
    
    return default_company


@frappe.whitelist()
def add_seconds_to_time(time_str, seconds=1):
    """
    Adds a specified number of seconds to a time string.
    
    Parameters:
        time_str (str): The time string in '%H:%M:%S' or '%H:%M:%S.%f' format.
        seconds (int): The number of seconds to add. Default is 1 second.

    Returns:
        str: The new time string in '%H:%M:%S' format.
    """
    # Try parsing with milliseconds format first, then fall back to seconds-only format
    try:
        datetime_object = datetime.strptime(time_str, '%H:%M:%S.%f')
    except ValueError:
        datetime_object = datetime.strptime(time_str, '%H:%M:%S')
    
    # Add the specified number of seconds
    new_datetime = datetime_object + timedelta(seconds=seconds)
    
    # Return the new time as a string without milliseconds
    return new_datetime.strftime('%H:%M:%S')

@frappe.whitelist()
def get_default_currency():
        
    default_company = get_default_company()
    default_currency = frappe.get_value('Company', default_company,  ['default_currency'])
    return default_currency

@frappe.whitelist()
def get_default_payable_account():        
    default_company = get_default_company()
    default_payable_account = frappe.get_value('Company', default_company,  ['default_payable_account'])
    return default_payable_account

@frappe.whitelist()
def get_default_tax():        
    default_company = get_default_company()
    tax = frappe.get_value('Company', default_company,  ['tax'])
    return tax


@frappe.whitelist()
def get_company_settings():
    default_company = get_default_company()
    company_settings = frappe.db.sql("""select default_currency, use_customer_last_price, use_supplier_last_price,tax_excluded,default_asset_location,use_custom_item_group_description_in_estimation,overheads_based_on_percentage from tabCompany where name='{0}'""".format(default_company), as_dict = True)        
    return company_settings

@frappe.whitelist()
def get_supplier_terms(supplier):
    supplier_terms = frappe.get_doc("Supplier", supplier)
    use_default_supplier_terms = supplier_terms.get("use_default_supplier_terms")

    if use_default_supplier_terms:
        default_company = get_default_company()
        supplier_terms_in_company = frappe.get_value('Company', default_company, 'supplier_terms')

        if supplier_terms_in_company:
            return frappe.get_value('Terms And Conditions', filters={'template_name': supplier_terms_in_company}, 
                                    fieldname=['template_name', 'terms'], as_dict=True)
    else:
        return frappe.get_value('Terms And Conditions', filters={'template_name': supplier_terms.get("default_terms")}, 
                                fieldname=['template_name', 'terms'], as_dict=True)

@frappe.whitelist()
def get_customer_terms(customer):
    customer_terms = frappe.get_doc("Customer", customer)
    use_default_customer_terms = customer_terms.get("use_default_customer_terms")

    if use_default_customer_terms:
        default_company = get_default_company()
        supplier_terms_in_company = frappe.get_value('Company', default_company, 'customer_terms')

        if supplier_terms_in_company:
            return frappe.get_value('Terms And Conditions', filters={'template_name': supplier_terms_in_company}, 
                                    fieldname=['template_name', 'terms'], as_dict=True)
    else:
        return frappe.get_value('Terms And Conditions', filters={'template_name': customer_terms.get("default_terms")}, 
                                fieldname=['template_name', 'terms'], as_dict=True)


@frappe.whitelist()
def get_terms_for_template(template):
    return frappe.get_value('Terms And Conditions', filters={'template_name': template}, 
                            fieldname=['terms'], as_dict=True)

@frappe.whitelist()
def get_fiscal_years():
    # Query to get distinct years from the posting_date column in tabGL Posting
    fiscal_years = frappe.db.sql("""
        SELECT DISTINCT YEAR(posting_date) AS year
        FROM `tabGL Posting`
        ORDER BY year DESC
    """, as_dict=True)

    # Extract the year and return it as a list of strings
    return [str(fy.year) for fy in fiscal_years]

@frappe.whitelist()
def get_period_list(start_date, end_date, periodicity):
    
    if(periodicity == "Default"):
        return
    
    months_to_add = {"Yearly": 12, "Half-Yearly": 6, "Quarterly": 3, "Monthly": 1}[periodicity]

    period_list = []    
    
    # full_start_date = start_date
    # full_end_date = end_date
    
    # # Add the 'total' period entry at the start
    # total_period = frappe._dict({
    #     "from_date": full_start_date,
    #     "to_date": full_end_date,
    #     "key": "total",
    #     "label": "Total Period"
    # })
    
    # period_list.append(total_period)
    
    start_date = getdate(start_date)
    end_date = getdate(end_date)

    months = get_months(start_date, end_date)    

    for i in range(cint(math.ceil(months / months_to_add))):
        
        period = frappe._dict({"from_date": start_date})

        if i == 0 :
                to_date = add_months(get_first_day(start_date), months_to_add)
        else:
            to_date = add_months(start_date, months_to_add)
        
        start_date = to_date

        # Subtract one day from to_date, as it may be first day in next fiscal year or month
        to_date = add_days(to_date, -1)

        if to_date <= end_date:
            # the normal case
            period.to_date = to_date
        else:
            # if a fiscal year ends before a 12 month period
            period.to_date = end_date

        period_list.append(period)

        if period.to_date == end_date:
            break

    # common processing
    for opts in period_list:
        key = opts["to_date"].strftime("%b_%Y").lower()
        if periodicity == "Monthly":
            label = formatdate(opts["to_date"], "MMM YYYY")
        else:
            label = get_label(periodicity, opts["from_date"], opts["to_date"])            

        opts.update(
            {
                "key": key.replace(" ", "_").replace("-", "_"),
                "label": label
            }
        )
    return period_list

def get_months(start_date, end_date):
    start_date = getdate(start_date)
    end_date = getdate(end_date)
    diff = (12 * end_date.year + end_date.month) - (12 * start_date.year + start_date.month)
    return diff + 1

def get_label(periodicity, from_date, to_date):
    from_date = getdate(from_date)
    to_date = getdate(to_date)

    if periodicity == "Yearly":
        if from_date.year == to_date.year:
            label = formatdate(from_date, "yyyy")
        else:
            label = formatdate(from_date, "yyyy") + "-" + formatdate(to_date, "yyyy")
    else:
        label = formatdate(from_date, "MMM yyyy") + " - " + formatdate(to_date, "MMM yyyy")

    return label

def get_gl_narration(document_type):
    
    narration =frappe.get_value("GL Narration",{"doc_type":document_type},['narration'])
    return narration

@frappe.whitelist()
def show_a_message(msg):
    frappe.msgprint(msg, alert=True)