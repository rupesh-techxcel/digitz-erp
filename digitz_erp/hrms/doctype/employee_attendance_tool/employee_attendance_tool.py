# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

import datetime
import json

import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from digitz_erp.api.employee_api import get_employee_holiday_list_for_the_date,check_holiday_date_in_holiday_list,check_employee_holiday_exception
from digitz_erp.api.employee_api import get_employee_shift
from frappe.utils import get_time


class EmployeeAttendanceTool(Document):
	pass

@frappe.whitelist()
def get_employees(
    date: str | datetime.date,
    department: str = None,
    designation:str= None
    
) -> dict[str, list]:
    filters = {"date_of_joining": ["<=", date],"status":"On Job"}

    for field, value in {"department": department}.items():
        if value:
            filters[field] = value
            
    for field, value in {"designation": designation}.items():
        if value:
            filters[field] = value


    employee_list = frappe.get_list(
        "Employee",
        fields=["employee_code", "employee_name"],
        filters=filters,
        order_by="employee_code",
    )
    
    attendance_list = frappe.get_list(
    "Attendance",
    fields=["name", "employee", "employee_name", "attendance_status", "docstatus","leave_record"],
    filters={
        "attendance_date": date,
        "docstatus": ["in", [1, 0]]
    },
    order_by="attendance_status, employee_name",
    )

    unmarked_attendance = _get_unmarked_attendance(date,employee_list, attendance_list)
    
    return {"marked": attendance_list, "unmarked": unmarked_attendance}

def _get_unmarked_attendance(date,employee_list: list[dict], attendance_list: list[dict]) -> list[dict]:
    marked_employee_codes = [entry.employee for entry in attendance_list]
    unmarked_attendance = []
    
    for entry in employee_list:
        
        if entry.employee_code not in marked_employee_codes:
            
            employee_holiday_list = get_employee_holiday_list_for_the_date(entry.employee_code,date)
                
            holiday= check_holiday_date_in_holiday_list(employee_holiday_list.name,date)
                        
            
            if holiday:
                
                holiday_exception = check_employee_holiday_exception(entry.employee_code,date)
                
                if holiday_exception:                    
                    unmarked_attendance.append(entry)                      
            else:   
                unmarked_attendance.append(entry)

    return unmarked_attendance



@frappe.whitelist()
def mark_employee_attendance(
    employee_list: list | str,
    status: str,
    date: str | datetime.date,
    leave_type: str = None,
    show_alert=True,
) -> None:
    
    if isinstance(employee_list, str):
        employee_list = json.loads(employee_list)

    for employee in employee_list:
        
        attendance_exist = frappe.db.exists("Attendance", {"employee": employee, "attendance_date": date})
        
        if attendance_exist and show_alert:
            frappe.msgprint(f"Attendance already exists for {employee}", indicator="orange", alert=True)
            continue
            
        holiday = verify_holiday(employee,date)
        
        if holiday:
            continue
        
        employee_name = frappe.get_value("Employee", {"name": employee}, "employee_name")
        shift_doc, shift_allocation_doc = get_employee_shift(employee, date, show_alert=False)

        ot_applicable = frappe.get_single('HR Settings').overtime_applicable
        employee_doc = frappe.get_doc("Employee", employee)
        ot_applicable = ot_applicable and employee_doc.ot_applicable and shift_doc.ot_applicable
                
        attendance = frappe.get_doc({
            "doctype": "Attendance",
            "employee": employee,
            "employee_name": employee_name,
            "attendance_date": getdate(date),
            "status": status,
            "leave_type": leave_type,
            "shift": shift_doc.name,
            "shift_payment_unit": shift_doc.shift_payment_unit,
            "shift_start_time": shift_doc.start_time,
            "shift_end_time": shift_doc.end_time,
            "break_in_mins": shift_doc.break_in_minutes,
            "standard_working_hours": shift_doc.standard_working_hours,
            "standard_no_of_units": shift_doc.no_of_units_per_day,
            "ot_applicable": ot_applicable,
            "attendance_start_time": shift_doc.start_time,
            "attendance_end_time": shift_doc.end_time,
            "actual_no_of_units": shift_doc.no_of_units_per_day,
            "effective_no_of_units": shift_doc.no_of_units_per_day
        })
        
        if shift_allocation_doc:
            attendance.attendance_end_time = shift_allocation_doc.expected_end_time
            attendance.actual_no_of_units = shift_allocation_doc.expected_no_of_units
            attendance.effective_no_of_units = shift_allocation_doc.expected_no_of_units
            attendance.attendance_ot = shift_allocation_doc.expected_ot if ot_applicable else 0        
        
        attendance.insert()
        if show_alert:
            frappe.msgprint(f"Successfully marked attendance for {employee_name}.", indicator="green", alert=True)

@frappe.whitelist()
def mark_employee_attendance_for_whole_month(
    employee_list: list | str,
    status: str,
    date: str | datetime.date,
    leave_type: str = None
) -> None:
    
    import calendar
    import datetime
    
    # Ensure the date is in datetime.date format
    if isinstance(date, str):
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    
    # Get the first and last day of the month
    first_day = date.replace(day=1)
    last_day = date.replace(day=calendar.monthrange(date.year, date.month)[1])    
    current_date = first_day
    while current_date <= last_day:
        
        mark_employee_attendance(employee_list, status, current_date, leave_type)
        current_date += datetime.timedelta(days=1)    


def verify_holiday(employee_code,date):
    employee_holiday_list = get_employee_holiday_list_for_the_date(employee_code,date)

    holiday= check_holiday_date_in_holiday_list(employee_holiday_list.name,date)
    
    if holiday:
        holiday_exception = check_employee_holiday_exception(employee_code,date)
        if holiday_exception:
            return False
        else:
            return True
    else:
        return False

    