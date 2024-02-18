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
    company_settings = frappe.db.sql("""select default_currency, use_customer_last_price, use_supplier_last_price,tax_excluded from tabCompany where name='{0}'""".format(default_company), as_dict = True)        
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
