import frappe

@frappe.whitelist()
def get_user_default_warehouse():
    
    user = frappe.session.user

    # returnValue = frappe.db.sql("""SELECT warehouse FROM `tabUser Warehouse` WHERE user = '{}' AND is_default = 1""".format(user), as_dict=1)
    
    user_default_warehouse = frappe.get_value('User Warehouse', {'user':user, 'is_default':1}, ['warehouse'])

    print("user_default_warehouse")        
    print(user_default_warehouse)
    
    return user_default_warehouse
    