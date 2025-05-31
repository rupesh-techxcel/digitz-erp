import frappe

@frappe.whitelist()
def after_install_hr():
    
    create_shift_payment_units()    
    create_salary_group()
    
def create_salary_group():
    salary_group = "General"
    if not frappe.db.exists("Salary Group", salary_group):
        salary_group_doc = frappe.get_doc({"doctype":"Salary Group", "group_name":salary_group})
        salary_group_doc.insert(ignore_permissions = True)
        print(f"Salary Group '{salary_group}' created successfully.")
    else:
        print(f"Salary Group '{salary_group}' already exists.")
    
def create_shift_payment_units():
    
    unit = "HRS"
    if not frappe.db.exists("Shift Payment Unit", {"name": unit}):
        
        shift_payment_unit = frappe.get_doc({
            "doctype": "Shift Payment Unit",
            "unit_name": unit            
        })
        
        shift_payment_unit.insert()
        print(f"Inserted Shift Payment Unit: {unit}")