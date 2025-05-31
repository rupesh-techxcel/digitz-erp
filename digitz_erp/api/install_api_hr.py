import frappe

@frappe.whitelist()
def after_install_hr():
    
    create_shift_payment_units()    
    create_salary_group()
    setup_default_shift_configuration()
    
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
        print(f"Inserted Default Payment Unit: {unit}")
        
def create_default_shift():
    shift_name = "Default Shift"

    # Ensure payment unit exists before referencing it
    if not frappe.db.exists("Shift Payment Unit", {"unit_name": "HRS"}):
        create_shift_payment_units()

    if not frappe.db.exists("Shift", {"shift_name": shift_name}):
        shift = frappe.get_doc({
            "doctype": "Shift",
            "shift_name": shift_name,
            "start_time": "08:00:00",
            "end_time": "18:00:00",
            "break_in_minutes": 60,
            "shift_payment_unit": "HRS"
        })
        shift.insert()
        shift.submit()
        print(f"Inserted Shift: {shift_name}")
    else:
        print(f"Shift '{shift_name}' already exists.")

def set_default_shift_in_hr_settings():
    if frappe.db.exists("Shift", {"shift_name": "Default Shift"}):
        hr_settings = frappe.get_single("HR Settings")
        hr_settings.default_shift = "Default Shift"
        hr_settings.save()
        frappe.db.commit()
        print("Default Shift has been set in HR Settings.")
    else:
        print("Shift 'Default Shift' does not exist, cannot set in HR Settings.")

def setup_default_shift_configuration():    
    create_default_shift()
    set_default_shift_in_hr_settings()
        