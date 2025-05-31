import frappe
from datetime import datetime
from frappe.utils import getdate,add_days

@frappe.whitelist()
def validate_leave_period_dates(leave_period,leave_from_date,leave_to_date):
    
    leave_period = frappe.get_doc("Leave Period",leave_period)
    leave_from_date = getdate(leave_from_date)
    leave_to_date = getdate(leave_to_date)
    leave_period_from_date = getdate(leave_period.from_date)
    leave_period_to_date = getdate(leave_period.to_date)
    
    if not (leave_period_from_date <= leave_from_date and leave_period_to_date >= leave_to_date):        
        frappe.throw("The applied leave dates are not within the selected leave period.")

@frappe.whitelist()
def check_employee_leave_assignment(employee):
    
    leave_policy_assignment = frappe.db.sql("""
			SELECT name 
			FROM `tabLeave Policy Assignment` lpa 
			WHERE 
			lpa.name IN (
				SELECT parent 
				FROM `tabLeave Policy Employee` lpe 
				WHERE lpe.employee = %s
			)
		""", (employee), as_dict=True)
    
    if not leave_policy_assignment:
        return False
    else:
        return True


@frappe.whitelist()
def get_employee_leave_policy_assignment(employee, leave_period):
    leave_policy_assignment = frappe.db.sql("""
			SELECT name 
			FROM `tabLeave Policy Assignment` lpa 
			WHERE lpa.leave_period = %s 
			AND lpa.name IN (
				SELECT parent 
				FROM `tabLeave Policy Employee` lpe 
				WHERE lpe.employee = %s
			)
		""", (leave_period,employee), as_dict=True)
    
    return leave_policy_assignment

# This method calls from leave application when the user choose a leave type for the leave and system
# checks the leave availability. If the leave allocation found for the employee with the leave type and leave
# period the method will return with the balance leaves available for the leave type
# and if not found system will check whether the leave_type is permissible based on some conditions
# The rules applicable are
#       1. No fully paid leaves allowed if leaves are not allocated and leave balance available
#       2. Compensatory leave is allowed if leave not found in the allocation
#       3. Leave without Pay is allowed if leave not found in the allocation
#       4. Partially paid leave is allowed if leave not found in the allocation
# 
# This logic will subject to change in future for accomodating more requirements in the market
# Eg: automation of allocating compensatory leave
@frappe.whitelist()
def get_system_approval_for_the_leaves_applied(employee, leave_period, leave_type, no_of_leaves_applied_for):
    
    elpa = get_employee_leave_policy_assignment(employee=employee, leave_period=leave_period)
    
    leave_allocations = frappe.db.sql("""
        SELECT leave_type, annual_allocation 
        FROM `tabLeave Policy Details` WHERE parent=%s
        """, (elpa[0]["name"]), as_dict=True)
    
    leave_type_doc = frappe.get_doc("Leave Type", leave_type)
    
    allocation_found = False
    leave_type_annual_allocation = 0
    for allocation in leave_allocations:
        # Allocation found for the leave type
        if allocation.leave_type == leave_type:
            
            allocation_found = True
            
            leave_type_annual_allocation = allocation.annual_allocation
            
            leaves_taken_already = 0
            
            leave_records = frappe.db.sql("""SELECT leave_type, COUNT(name) as leave_count 
                                            FROM `tabEmployee Leave Record` 
                                            WHERE employee=%s AND leave_period=%s 
                                            GROUP BY leave_type
                                            """, (employee, leave_period), as_dict=True)
            
            if leave_records:                
                leaves_taken_already = leave_records[0].leave_count
            
            
            
            if leave_type_doc.maximum_consecutive_leaves_allowed< no_of_leaves_applied_for:
                
                frappe.throw(f"You have reached the limit for this leave type. The maximum consecutive leaves allowed are {leave_type_doc.maximum_consecutive_leaves_allowed}.")

            
            leaves_balance = leave_type_annual_allocation - leaves_taken_already
            
            if leaves_balance < no_of_leaves_applied_for:
                frappe.throw("No available leave balance for the selected leave type.")
                
    if not allocation_found:
        leave_cannot_approve = True
        # When leave is not allocated
        if leave_type_doc.is_leave_without_pay:
            leave_cannot_approve = False
        if leave_type_doc.is_partially_paid_leave:
            leave_cannot_approve = False
        if leave_type_doc.is_compensatory_leave:
            leave_cannot_approve = False
        
        if(leave_cannot_approve):
            frappe.throw("The leave application cannot be approved.")


@frappe.whitelist()    
def get_employee_leave_statistics(employee, leave_period,leave_from_date, leave_to_date):
    
    validate_leave_period_dates(leave_period, leave_from_date, leave_to_date)
    
    elpa = get_employee_leave_policy_assignment(employee=employee, leave_period=leave_period)
        
    if not elpa:
        frappe.throw("No leave policy assignment exists for the selected leave period and employee.")
        
    frappe.msgprint(f"Found the leave policy {elpa[0].name} assigned to the employee.", alert=True)
    
    leave_allocations = frappe.db.sql("""
        SELECT leave_type, annual_allocation 
        FROM `tabLeave Policy Details` 
        WHERE parent=%s
    """, (elpa[0]["name"]), as_dict=True)
        
    leave_records = frappe.db.sql("""
        SELECT leave_type, COUNT(name) as leave_count 
        FROM `tabEmployee Leave Record` 
        WHERE employee=%s AND leave_period=%s 
        GROUP BY leave_type
    """, (employee, leave_period), as_dict=True)
    
    # Convert leave_allocations to a dictionary for easy lookup
    leave_allocations_dict = {allocation["leave_type"]: allocation["annual_allocation"] for allocation in leave_allocations}
    
    # Prepare the result collection
    result_collection = []
    
    # Add leave types from leave_allocations to the result collection
    for allocation in leave_allocations:
        leave_type = allocation["leave_type"]
        annual_allocation = allocation["annual_allocation"]
        leaves_taken = next((record["leave_count"] for record in leave_records if record["leave_type"] == leave_type), 0)
        result_collection.append({
            "leave_type": leave_type,
            "annual_allocation": annual_allocation,
            "leaves_taken": leaves_taken
        })
    
    # Add remaining leave types from leave_records not in leave_allocations
    for record in leave_records:
        leave_type = record["leave_type"]
        if leave_type not in leave_allocations_dict:
            result_collection.append({
                "leave_type": leave_type,
                "annual_allocation": 0,
                "leaves_taken": record["leave_count"]
            })
    
    frappe.msgprint("Successfully retrieved employee leave allocations..", alert=True)
    
    return result_collection

@frappe.whitelist()
def get_employee_holiday_list(employee, leave_period):
    
    holiday_list = frappe.db.sql("""Select holiday_list from `tabEmployee Holiday List` ehl where employee=%s and leave_period=%s and docstatus=1""",(employee,leave_period), as_dict = True)
    
    if holiday_list:
        return holiday_list[0].holiday_list
    else:
        default_holiday_list = frappe.db.sql("""select holiday_list_name as holiday_list from `tabHoliday List` where leave_period=%s and default_for_the_leave_period=1 and docstatus=1""",(leave_period), as_dict=True)
        if default_holiday_list:
            return default_holiday_list[0].holiday_list
        
@frappe.whitelist()
def get_leave_and_holiday_count(leave_type, holiday_list, from_date, to_date):
    
    from_date = getdate(from_date)
    to_date = getdate(to_date)

    # Calculate the total number of days between from_date and to_date
    total_days = (to_date - from_date).days + 1

    # Fetch the holidays within the date range
    holidays = frappe.get_all('Holiday', 
        filters={'parent': holiday_list, 'date': ['between', [from_date, to_date]]}, 
        fields=['date'])
    
    holiday_count = len(holidays)
    
    leave_type_doc = frappe.get_doc("Leave Type", leave_type)
    
    leave_days = total_days
    
    # If holidays in the leaves are not considering as leaves leave_days reduced with holiday count
    if not leave_type_doc.count_holidays_in_leaves_as_leaves:
        leave_days = total_days - holiday_count
    else:
        # Sicne holidays are considering as leaves holiday count =0
        holiday_count = 0

    return {
        'leave_count': leave_days,
        'holiday_count': holiday_count        
    }
    

@frappe.whitelist()
def get_leave_dates_excluding_holidays(leave_type, holiday_list, from_date, to_date):
    from_date = getdate(from_date)
    to_date = getdate(to_date)

    # Calculate the total number of days between from_date and to_date
    total_days = (to_date - from_date).days + 1

    # Fetch the holidays within the date range
    holidays = frappe.get_all('Holiday', 
        filters={'parent': holiday_list, 'date': ['between', [from_date, to_date]]}, 
        fields=['date'])
    
    holiday_dates = [holiday['date'] for holiday in holidays]

    leave_type_doc = frappe.get_doc("Leave Type", leave_type)

    leave_dates = []
    
    # Generate the list of leave dates
    for day in range(total_days):
        current_date = add_days(from_date, day)
        if not leave_type_doc.count_holidays_in_leaves_as_leaves and current_date in holiday_dates:
            continue
        leave_dates.append(current_date)
    
    return leave_dates
    
@frappe.whitelist()
def get_leave_type_details(leave_type):
    leave_type_doc = frappe.get_doc("Leave Type", leave_type)
    return leave_type_doc

@frappe.whitelist()
def get_leave_period(from_date,to_date):
    
    from_date = getdate(from_date)
    to_date = getdate(to_date)
    
    leave_period = frappe.db.sql("""
        SELECT name, from_date, to_date 
        FROM `tabLeave Period`
        WHERE from_date <= %s AND to_date >= %s
        LIMIT 1
    """, (from_date, to_date), as_dict=True)    
    
    if leave_period:
        return leave_period[0].name
    else:
        return {"message": "No leave period found for the given date." }
