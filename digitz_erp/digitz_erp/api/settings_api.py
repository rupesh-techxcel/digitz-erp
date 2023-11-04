import frappe

@frappe.whitelist()
def get_default_company():
    
    default_company = frappe.db.get_single_value("Global Settings",'default_company')    
    
    return default_company

@frappe.whitelist()
def get_default_currency():
        
    default_company = get_default_company()
    default_currency = frappe.get_value('Company', default_company,  ['default_currency'])
    return default_currency

@frappe.whitelist()
def get_company_settings():
    default_company = get_default_company()
    company_settings = frappe.db.sql("""select default_currency, use_customer_last_price, use_supplier_last_price from tabCompany where name='{0}'""".format(default_company), as_dict = True)        
    return company_settings


