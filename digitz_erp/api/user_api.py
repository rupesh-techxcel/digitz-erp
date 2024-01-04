import frappe

@frappe.whitelist()
def get_user_default_warehouse():
    
    user = frappe.session.user

    # returnValue = frappe.db.sql("""SELECT warehouse FROM `tabUser Warehouse` WHERE user = '{}' AND is_default = 1""".format(user), as_dict=1)
    
    user_default_warehouse = frappe.get_value('User Warehouse', {'user':user, 'is_default':1}, ['warehouse'])
    
    return user_default_warehouse

@frappe.whitelist()
def get_user_default_warehouse_2():
    
    user = frappe.session.user

    # returnValue = frappe.db.sql("""SELECT warehouse FROM `tabUser Warehouse` WHERE user = '{}' AND is_default = 1""".format(user), as_dict=1)
    
    user_default_warehouse = frappe.get_value('User Warehouse', {'user':user, 'is_default':1}, ['warehouse'])
    
    if(not user_default_warehouse):        
         return frappe.get_value('Company', ['warehouse'])
    else:
        return user_default_warehouse
    