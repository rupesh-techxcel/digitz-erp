import frappe
from datetime import datetime
from frappe.utils import getdate,add_days
from collections import defaultdict
from datetime import datetime, timedelta,date

@frappe.whitelist()
def get_ot_applicable():       
    return frappe.get_single('HR Settings').overtime_applicable

@frappe.whitelist()
def get_default_shift(): 
       
    shift = frappe.get_single('HR Settings').default_shift   
    
    if not shift:
        frappe.throw("The employee must have an assigned shift, or a default shift must be set in HR Settings. Please update the necessary settings accordingly.") 
        
    return frappe.get_doc("Shift", shift)

@frappe.whitelist()
def get_employee_shift_allocation(employee,shift_date):
     shift_allocation = frappe.db.sql("""
        SELECT name,shift
        FROM `tabShift Allocation`
        WHERE employee = %s
        AND shift_date <= %s and docstatus=1
        ORDER BY shift_date DESC
        LIMIT 1
    """, (employee, shift_date), as_dict=True)
     return shift_allocation
 
@frappe.whitelist()
def get_shift_allocation_count(shift_name):
    if not shift_name:
        frappe.throw("Shift name is required.")

    # Fetch count of shift allocations for the specified shift
    shift_count = frappe.db.count("Shift Allocation", filters={"shift": shift_name})

    return shift_count

@frappe.whitelist()
def get_employee_shift(employee, shift_date, show_alert=True):
    
    # Get the latest shift allocation for the employee that is less than or equal to the shift_date
    shift_allocation = frappe.db.sql("""
        SELECT name,shift
        FROM `tabShift Allocation`
        WHERE employee = %s
        AND shift_date <= %s and docstatus=1
        ORDER BY shift_date DESC
        LIMIT 1
    """, (employee, shift_date), as_dict=True)

    if shift_allocation:
        
        shift = shift_allocation[0]['shift']
        
        shift_allocation = frappe.get_doc("Shift Allocation", shift_allocation[0]['name'])
        
        if show_alert:
            frappe.msgprint(f"Shift allocation '{shift}' found for the employee and has been assigned.", indicator='green',alert=True)
        
        shift = frappe.get_doc("Shift", shift_allocation.shift)

        return shift, shift_allocation

    else:
        
        if show_alert:
            frappe.msgprint("No shift allocation found on or before the specified date. Default shift has been assigned.", indicator ='orange', alert=True)
       
        return get_default_shift(),None

@frappe.whitelist()
def validate_employee_shift(employee, shift_date):
    
    shift_allocation_mandatory = frappe.get_single('HR Settings').shift_allocation_mandatory
    shift_allocation =get_employee_shift_allocation(employee,shift_date)
    if shift_allocation_mandatory and not shift_allocation:        
        return False
    else:
        return True
    
@frappe.whitelist()
def get_employees_for_payroll(start_date, end_date):
    employee_list = frappe.db.sql(
        """
        SELECT DISTINCT 
            a.employee,
            e.employee_name,
            e.designation,
            e.d epartment 
        FROM 
            `tabAttendance` a 
        INNER JOIN 
            `tabEmployee` e 
        ON 
            e.employee_code = a.employee 
        WHERE 
            a.attendance_date >= %s 
            AND a.attendance_date <= %s 
            AND a.docstatus = 1
            AND a.employee NOT IN (
                SELECT sl.employee 
                FROM `tabSalary Slip` sl
                WHERE salary_from_date = %s 
                AND salary_to_date = %s
            )            
        """,
        (start_date, end_date, start_date, end_date),
        as_dict=True
    )
    
    if not employee_list:
        frappe.msgprint("No employees found in the given criteria.", alert=True )        
    else:        
        frappe.msgprint("Save the document, to get the 'Create Salary Slips' option.",indicator="Green", alert=True)
    
    return employee_list


    
@frappe.whitelist()
def validate_monthly_salary_errors(start_date,end_date):
    
    frappe.db.sql(""" """)
    
@frappe.whitelist()
def create_salary_slip(employee, payroll_date, start_date, end_date):
    
    try:
        
        records_to_delete = frappe.get_all(
            'Salary Report Record',
            filters={'payroll_date': payroll_date, 'employee':employee},
            fields=['name']
        )
        
        # Loop through each record and delete it
        for record in records_to_delete:
            frappe.delete_doc('Salary Report Record', record['name'], force=1)
        
        # Fetch the employee document
        employee_doc = frappe.get_doc("Employee", employee)
        
        # Fetch the salary structure assignment
        salary_structure_assignment = frappe.db.sql("""
            SELECT parent,ssa.overtime_rate,ssa.holiday_rate
            FROM `tabSalary Structure Assignment` ssa
            INNER JOIN `tabSalary Structure` ss
            ON ssa.parent = ss.name
            WHERE employee=%s 
            AND ssa.from_date<=%s 
            AND ss.docstatus = 1
            ORDER BY ssa.from_date DESC         
            LIMIT 1
        """, (employee, start_date), as_dict=True)
        
        if not salary_structure_assignment:
            frappe.msgprint(f"Salary structure not assigned for the employee {employee_doc.employee_name}", alert=True)
            return
        
        salary_structure_name = salary_structure_assignment[0].parent
        
        # Fetch the salary structure document
        salary_structure = frappe.get_doc("Salary Structure", salary_structure_name)
        
        earnings = salary_structure.earnings
        deductions = salary_structure.deductions
        
        month_name = get_month_year(start_date)
        
        overtime_rate = salary_structure_assignment[0].overtime_rate
        holiday_salary = salary_structure_assignment[0].holiday_rate
            
        salary_report_record = frappe.new_doc("Salary Report Record")
        salary_report_record.employee = employee
        salary_report_record.payroll_date = payroll_date   
        salary_report_record.salary_month = month_name 
        
        salary_slip = frappe.new_doc("Salary Slip")
        salary_slip.employee = employee
        salary_slip.employee_name = employee_doc.employee_name
        salary_slip.department = employee_doc.department
        salary_slip.designation = employee_doc.designation
        salary_slip.payroll_date = payroll_date
        salary_slip.salary_from_date = start_date
        salary_slip.salary_to_date = end_date
        
                    
        attendance = frappe.db.sql("""
            SELECT attendance_date,
                COALESCE(worked_hours, 0) AS worked_hours,
                COALESCE(effective_no_of_units, 0) AS effective_no_of_units,
                COALESCE(attendance_ot, 0) AS overtime,
                attendance_status,
                SUM(COALESCE(standard_working_hours, 0)) AS standard_working_hours,
                SUM(COALESCE(standard_no_of_units, 0)) AS standard_no_of_units,
                leave_record,is_a_holiday
            FROM `tabAttendance`
            WHERE employee = %s
            AND attendance_date >= %s
            AND attendance_date <= %s
            AND docstatus=1
            GROUP BY attendance_date
        """, (employee, start_date, end_date), as_dict=True)
        
        ot_amount = 0                        
        
        daily_hours = 0
        daily_units = 0
        daily_ot = 0
        
        total_standard_hrs = 0
        total_standard_units = 0
        
        deduction_amount_due_to_leave = 0
        
        count = 0        
        
        deduction_hours_due_to_leave = 0
        deduction_units_due_to_leave = 0
            
        # The validations are already happened and the data_status set to 'Completed'. Only 'Completed' records are considering in this scope. 
        
        standard_working_hours =0
        standard_units =0
        total_amount =0
        
        no_of_units_in_holiday = 0
        holiday_count = 0
        holiday_total_salary = 0
        holiday_salary_deduction =0
        holiday_overtime =0
            
        if attendance:    
                                        
            for attendance_daily in attendance:
                
                # shift_allocation = get_employee_shift_allocation(attendance_daily.employee,
                #                                                  attendance_daily.attendance_date)
                
                
                # In this implementation holiday treats different for unit based salary. For hours based salary holiday specific treatment is not available in the implementation
                # And No Leave or half day leaves are taking to consideration
                # Salary based on the number of units and holiday_rate
                if attendance_daily.is_a_holiday:  
                    
                    holiday_count = holiday_count + 1
                    
                    standard_units = attendance_daily.standard_no_of_units
                    effective_units = attendance_daily.effective_no_of_units
                    
                    if standard_units == effective_units:
                        holiday_total_salary = holiday_total_salary +  holiday_salary
                    elif standard_units> effective_units:
                        per_unit_amount_for_holiday = holiday_salary / standard_units
                        holiday_salary_deduction = holiday_salary_deduction + (standard_units-effective_units) * per_unit_amount_for_holiday
                        # Holiday Toal Salaryt is still assigned since holiday_deduction_amount is
                        # treated seperately and deduct
                        holiday_total_salary = holiday_total_salary +  holiday_salary
                    elif standard_units< effective_units:
                        holiday_total_salary = holiday_total_salary +  holiday_salary
                        holiday_overtime = holiday_overtime + ((effective_units - standard_units) * overtime_rate)
                else:
                
                    # Get Standard Working Hrs from any of the attendance            
                    if attendance_daily.standard_working_hours>0 and standard_working_hours ==0:
                        standard_working_hours= attendance_daily.standard_working_hours
                    
                    if attendance_daily.standard_no_of_units>0 and standard_units ==0:
                        standard_units = attendance_daily.standard_no_of_units
                    
                    if attendance_daily.attendance_status == "Half Day Morning":
                        leave_record = frappe.db.sql("""
                            SELECT leave_duration, is_leave_without_pay, is_partially_paid_leave, is_compensatory_leave
                            FROM `tabEmployee Leave Record`
                            WHERE date=%s AND employee=%s
                        """, (attendance_daily.attendance_date, employee), as_dict=True)
                        
                        if not leave_record:
                            # Not likely to happen becauase the data_status changed to "Completed" already after validations
                            frappe.msgprint(f"Attendance marked as 'Half Day Morning' detected. No leave record found for the other half of the day for employee {employee_doc.employee_name} on {attendance_daily.attendance_date}.")
                            return False
                        elif leave_record[0].leave_duration != "Half Day Afternoon":
                            # Not likely to happen becauase the data_status changed to "Completed" already after validations
                            frappe.msgprint(f"Attendance marked as 'Half Day Morning' detected. No leave record found with 'Half Day Afternoon' for the other half of the day for employee {employee_doc.employee_name} on {attendance_daily.attendance_date}.")
                            return False
                        else:
                            if leave_record[0].is_leave_without_pay:
                                if attendance_daily.standard_working_hours and attendance_daily.standard_working_hours > 0:
                                    deduction_hours_due_to_leave += (attendance_daily.standard_working_hours / 2)
                                elif  attendance_daily.standard_no_of_units and attendance_daily.standard_no_of_units > 0:
                                    deduction_units_due_to_leave += attendance_daily.standard_no_of_units / 2
                                    
                            elif leave_record[0].is_partially_paid_leave:
                                pass
                            elif leave_record[0].is_compensatory_leave:
                                pass
                        
                    elif attendance_daily.attendance_status == "Half Day Afternoon":
                        leave_record = frappe.db.sql("""
                            SELECT leave_duration, is_leave_without_pay, is_partially_paid_leave, is_compensatory_leave
                            FROM `tabEmployee Leave Record`
                            WHERE date=%s AND employee=%s
                        """, (attendance_daily.attendance_date, employee), as_dict=True)
                        
                        if not leave_record:
                            frappe.msgprint(f"Attendance marked as 'Half Day Afternoon' detected. No leave record found for the other half of the day for employee {employee_doc.employee_name} on {attendance_daily.attendance_date}.")
                            return False
                        elif leave_record[0].leave_duration != "Half Day Morning":
                            frappe.msgprint(f"Attendance marked as 'Half Day Afternoon' detected. No leave record found with 'Half Day Morning' for the other half of the day for employee {employee_doc.employee_name} on {attendance_daily.attendance_date}.")
                            return False
                        else:
                            if leave_record[0].is_leave_without_pay:
                                if attendance_daily.standard_working_hours and attendance_daily.standard_working_hours > 0:
                                    deduction_hours_due_to_leave += (attendance_daily.standard_working_hours / 2)
                                elif  attendance_daily.standard_no_of_units and attendance_daily.standard_no_of_units > 0:
                                    deduction_units_due_to_leave += attendance_daily.standard_no_of_units / 2
                                
                            elif leave_record[0].is_partially_paid_leave:
                                pass
                            elif leave_record[0].is_compensatory_leave:
                                pass
                        
                    elif attendance_daily.attendance_status == "Leave":  
                        
                        if attendance_daily.leave_record:
                            leave_record = frappe.get_doc("Employee Leave Record", attendance_daily.leave_record)
                            
                            if leave_record.is_leave_with_out_pay:     
                                if attendance_daily.standard_working_hours and attendance_daily.standard_working_hours > 0:
                                        deduction_hours_due_to_leave += attendance_daily.standard_working_hours  
                                elif  attendance_daily.standard_no_of_units and attendance_daily.standard_no_of_units > 0:
                                        deduction_units_due_to_leave += attendance_daily.standard_no_of_units
                                        
                            elif leave_record.is_partially_paid_leave:
                                deduction_hours_due_to_leave += attendance_daily.standard_working_hours - (attendance_daily.standard_working_hours * leave_record.fraction_of_salary)
                            elif leave_record.is_compensatory_leave:
                                pass
                    elif (attendance_daily.attendance_status == "Present" or attendance_daily.attendance_status == "Work From Home"):              
                            daily_ot += (attendance_daily.overtime or 0)
            
            salary_payable_amount = 0
            
            salary_payable_amount += holiday_total_salary - holiday_salary_deduction + holiday_overtime
            
            # Earning component
            for earning_component in earnings:   
                
                salary_slip.append("earnings_and_deductions", {
                    "salary_component": earning_component.component,
                    "type": "Earning",
                    "amount": earning_component.amount
                })
                
                total_amount += earning_component.amount
                salary_payable_amount += earning_component.amount
                
            if deductions:
            
                for deduction_component in deductions:                
                    
                    salary_slip.append("earnings_and_deductions", {
                        "salary_component": deduction_component.component,
                        "type": "Deduction",
                        "amount": deduction_component.amount
                    })
                    total_amount -= deduction_component.amount
                    salary_payable_amount -= deduction_component.amount
            
            salary_report_record.basic_salary = total_amount

            no_of_standard_days = 30        
            
            per_day_amount = total_amount/no_of_standard_days
            
            per_unit_amount = 0
                    
            if standard_working_hours>0:
                per_hour_amount = per_day_amount/ standard_working_hours
                ot_amount = daily_ot * per_hour_amount
                salary_payable_amount+= ot_amount
                
                deduction_amount_due_to_leave =  deduction_hours_due_to_leave * per_hour_amount
                salary_payable_amount -= deduction_amount_due_to_leave
            else:            
                ot_amount = daily_ot * overtime_rate
                salary_payable_amount+= ot_amount
                
                deduction_amount_due_to_leave =  deduction_units_due_to_leave * per_unit_amount
                salary_payable_amount -= deduction_amount_due_to_leave
            
            salary_report_record.deductions_for_leave = deduction_amount_due_to_leave
            salary_report_record.overtime_trips = daily_ot
            salary_report_record.overtime_rate = overtime_rate
            salary_report_record.overtime_amount = ot_amount
            
            if holiday_count>0:
            
                salary_report_record.holiday_days = holiday_count
                # holiday_rate is the holiday salary
                salary_report_record.holiday_rate = holiday_total_salary/ holiday_count
                salary_report_record.holiday_salary = holiday_total_salary/ holiday_count        
                salary_report_record.holiday_overtime = holiday_overtime
                salary_report_record.holiday_deductions = holiday_salary_deduction
                salary_report_record.holiday_amount = holiday_total_salary + holiday_overtime - holiday_salary_deduction
            
                    
            # Get Additional Salary 
            additional_salary_list = get_additional_salary(employee, start_date, end_date)
            
            print("additional salary")
            print(additional_salary_list)
        
            shutdown_total = 0
            others_total = 0
            shutdown_count  =0
            others_count = 0
        
            for additional_salary in additional_salary_list:
                
                print(additional_salary)
                
                salary_slip.append("earnings_and_deductions", {
                    "salary_component": additional_salary.additional_salary_component,
                    "type": "Earning",
                    "amount": additional_salary.amount
                })
                
                if additional_salary.additional_salary_component =="Shutdown":
                    shutdown_count += additional_salary.qty if additional_salary.qty>0 else 1
                    shutdown_total += additional_salary.amount
                # elif additional_salary.additional_salary_component =="Others":
                else: 
                    #include all other additional salaries to Others
                    others_count += additional_salary.qty  if additional_salary.qty>0 else 1
                    others_total += additional_salary.amount
                    
                salary_payable_amount += additional_salary.amount  
                    
            if shutdown_total>0:
                salary_report_record.shutdown_nos  = shutdown_count
                salary_report_record.shutdown_amount  = shutdown_total
                salary_report_record.shutdown_rate  = shutdown_total/ shutdown_count if shutdown_count>0 else 0
            
            if others_total>0:    
                salary_report_record.others_hrs  = others_count
                salary_report_record.others_amount  = others_total
                salary_report_record.others_rate  = others_total/ others_count if others_count>0 else 0
        
            print("salary report record")
            print(salary_report_record)
            
            if ot_amount> 0:               
                
                salary_slip.append("earnings_and_deductions", {
                    "salary_component": "Overtime",
                    "type": "Earning",
                    "amount": ot_amount
                })  
            
            if holiday_total_salary>0:
                salary_slip.append("earnings_and_deductions", {
                    "salary_component": "Compensation for Holiday Work",
                    "type": "Earning",
                    "amount": holiday_total_salary
                })            
                
            if holiday_overtime>0:
                salary_slip.append("earnings_and_deductions", {
                    "salary_component": "Holiday Work Overtime",
                    "type": "Earning",
                    "amount": holiday_overtime
                })    
               
            
            if holiday_salary_deduction>0:
                salary_slip.append("earnings_and_deductions", {
                    "salary_component": "Deductions for Holiday",
                    "type": "Deduction",
                    "amount": holiday_salary_deduction
                })    
               
                
            if deduction_amount_due_to_leave>0:
                salary_slip.append("earnings_and_deductions", {
                    "salary_component": "Leave without Pay",
                    "type": "Deduction",
                    "amount": deduction_amount_due_to_leave * -1
                })
            
            loan_deduction_record = get_loan_recovery_deduction(employee, payroll_date)
            
            loan_deduction_amount = 0
            
            salary_report_record.gross_salary = salary_payable_amount
            
            if loan_deduction_record:
                salary_slip.append("earnings_and_deductions", {
                    "salary_component": "Loan deduction",
                    "type": "Deduction",
                    "amount": loan_deduction_record[0].deduction_amount * -1
                })
                
                loan_deduction_amount = loan_deduction_record[0].deduction_amount
                
                salary_payable_amount -= loan_deduction_amount
            
            salary_slip.salary_payable_amount = salary_payable_amount        
            
            salary_report_record.advance_deduction = loan_deduction_amount
            salary_report_record.net_salary = salary_payable_amount 
            
            # salary_report_record.total_deductions = deduction_amount_due_to_leave + loan_deduction_amount        
            
            salary_slip.insert()
            
            # frappe.msgprint(f"Salary slip created successfully for {employee_doc.employee_name}", alert=True)
            
            salary_report_record.insert()
            
            return salary_slip.name
        else:
            frappe.msgprint("No attendance records found for the specified period.", alert=True)
            return False
    except Exception as e:
        # Log the error
        frappe.log_error(frappe.get_traceback(), 'Error in create_salary_slip')
        # Optionally, show a message to the user
        frappe.msgprint(f"An error occurred: {str(e)}", alert=True)
        return None

def get_month_year(input_date):
       
    # Check if the input is a string
    if isinstance(input_date, str):
        # Parse the date string into a datetime object
        date_obj = datetime.strptime(input_date, '%Y-%m-%d').date()
    elif isinstance(input_date, date):
        date_obj = input_date
    else:
        raise TypeError("input_date must be a date object or a string in 'yyyy-mm-dd' format")

    # Format the date object into the desired string format
    formatted_date = date_obj.strftime('%b-%y')

    return formatted_date
    
    
def get_loan_recovery_deduction(employee, payroll_date):
    
    recovery_record = frappe.db.sql("""Select eldr.date,eldr.deduction_amount,eldr.status from `tabEmployee Loan Deduction Record` eldr inner join `tabEmployee Loan` el where eldr.parent=el.name and el.employee=%s and eldr.status='Pending' and (el.loan_status='Approved' or el.loan_status='On Going') and el.docstatus=1 and eldr.date>=%s Order by eldr.date LIMIT 1""",(employee, payroll_date), as_dict=True)
    
    print("recovery_record")
    print(recovery_record)
    
    return recovery_record

def get_additional_salary(employee,start_date, end_date):    
    
    additional_salary_list = frappe.db.sql("""Select date, additional_salary_component,qty,amount from `tabAdditional Salary` where employee=%s and date >=%s and date<=%s and docstatus=1""",(employee,start_date,end_date), as_dict=True)
    
    return additional_salary_list

@frappe.whitelist()
def get_employees_in_designation(designation):
    
    employee_list = frappe.db.sql(
        """
        SELECT DISTINCT 
            e.employee_code as employee,
            e.employee_name,
            e.designation,
            e.department 
        FROM 
            `tabEmployee` e
        WHERE 
            e.status != 'Resigned' and e.status!='Terminated' and e.designation=%s
            
        AND e.employee_code NOT IN (
                SELECT 
                    employee 
                FROM 
                `tabSalary Structure Assignment`
            )         
        """,
        (designation),
        as_dict=True
    )
    
    if not employee_list:
        frappe.msgprint("No employees found in the given criteria." ) 
    
    return employee_list

@frappe.whitelist()
def get_leave_policy_details(leave_policy):
    
    return frappe.db.sql("""Select leave_type,annual_allocation from `tabLeave Policy Details` where parent=%s""",leave_policy, as_dict=True)

@frappe.whitelist()
def get_employees_for_leave_policy(designation, leave_period):
    
    employee_list = frappe.db.sql(
        """
        SELECT DISTINCT 
            e.employee_code as employee,
            e.employee_name,
            e.designation,
            e.department 
        FROM 
             `tabEmployee` e
        WHERE 
            e.status != 'Resigned' and e.status!='Terminated' and e.designation=%s
            
        AND e.employee_code NOT IN (
                SELECT 
                    d.employee 
                FROM 
                `tabLeave Policy Employee` d inner join `tabLeave Policy Assignment` a on d.parent=a.name and a.leave_period=%s
            )         
        """,
        (designation,leave_period),
        as_dict=True
    )
    
    if not employee_list:
        frappe.msgprint("No employees found with leave policy unassigned in the given criteria." ) 
    
    return employee_list
    
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

@frappe.whitelist()
def get_employee_holiday_list_for_the_date(employee, date):
    # Query to get the holiday list assigned to the employee for the given date
    
    holiday_list = frappe.db.sql("""
        SELECT holiday_list as name
        FROM `tabEmployee Holiday List` 
        WHERE leave_period_from_date <= %s 
        AND leave_period_to_date >= %s 
        AND employee = %s
        AND docstatus = 1
    """, (date, date, employee), as_dict=True)
    
    # If an employee has a holiday list assigned, return it
    if holiday_list:
        return holiday_list[0]

    # Otherwise, get the default holiday list for the leave period that includes the given date
    default_holiday_list = frappe.db.sql("""
        SELECT name 
        FROM `tabHoliday List` 
        WHERE default_for_the_leave_period = 1 
        AND from_date <= %s 
        AND to_date >= %s
        AND docstatus=1
    """, (date, date), as_dict=True)

    # Return the default holiday list if found
    if default_holiday_list:
        return default_holiday_list[0]

    # If no holiday list is found, return None or handle the case as needed
    return None    

@frappe.whitelist()
def check_holiday_date_in_holiday_list(holiday_list, date):
    # Debugging output  
    
    try:
        holiday_date = frappe.db.sql("""
            SELECT h.date 
            FROM `tabHoliday` h 
            INNER JOIN `tabHoliday List` hl 
            ON h.parent = hl.name  
            WHERE h.date = %s 
            AND hl.name = %s 
            AND hl.docstatus = 1
        """, (date, holiday_list), as_dict=True)
                
        # Return the holiday date if found, otherwise return None
        if holiday_date:            
            return holiday_date[0]
        else:            
            return None
    except Exception as e:
        return None
    
@frappe.whitelist()
def check_employee_holiday_exception(employee, date):
    # Query to check if there is an approved holiday exception for the given employee and date
    holiday_exception = frappe.db.sql("""
        SELECT date_for_exception 
        FROM `tabEmployee Holiday Exception` 
        WHERE employee = %s 
        AND date_for_exception = %s 
        AND status = 'Approved' 
        AND docstatus = 1
    """, (employee, date), as_dict=True)
    
    # Return the holiday exception if found, otherwise return None
    if holiday_exception:
        return holiday_exception[0]
    else:
        return None

@frappe.whitelist()
def verify_attendances(from_date, to_date):
    from datetime import datetime
    
    # Convert from_date and to_date to datetime objects
    start_date = datetime.strptime(from_date, '%Y-%m-%d')
    end_date = datetime.strptime(to_date, '%Y-%m-%d')

    # Fetch employee list
    employee_list = frappe.db.sql("""SELECT employee_code,employee_name FROM `tabEmployee` WHERE status='On Job'""", as_dict=True)

    # Initialize an empty dictionary to accumulate exception counts for all employees
    total_exception_counts = {}

    # Loop through each employee and accumulate their exception counts
    for employee in employee_list:
        employee_code = employee['employee_code']
        employee_exceptions = get_employee_exception_counts(employee_code, start_date, end_date)

        for date_str, count in employee_exceptions.items():
            if date_str not in total_exception_counts:
                total_exception_counts[date_str] = 0
            total_exception_counts[date_str] += count

    return total_exception_counts

def get_employee_exception_counts(employee_code, start_date, end_date):
    from datetime import timedelta

    exception_counts = {}

    current_date = start_date
    while current_date <= end_date:
        # Perform your logic for each date for the employee
        holiday_list = get_employee_holiday_list_for_the_date(employee_code, current_date)
        holiday = check_holiday_date_in_holiday_list(holiday_list.name, current_date)
        verify_attendance_and_leave = False

        if holiday:
            holiday_exception = check_employee_holiday_exception(employee_code, current_date)
            if holiday_exception:
                verify_attendance_and_leave = True
        else:
            verify_attendance_and_leave = True

        if verify_attendance_and_leave:
            
            # Check for attendance records
            attendance = frappe.db.sql("""SELECT name, attendance_status FROM `tabAttendance` WHERE attendance_date=%s AND employee=%s and docstatus=1""", (current_date, employee_code), as_dict=True)
            
            exception = False

            # No Attendance found, so it's an exception
            if not attendance:
                exception = True
            elif attendance[0].attendance_status in ["Present", "Work From Home", "Leave"]:
                current_date += timedelta(days=1)
                continue
            elif attendance[0].attendance_status == "Half Day Morning":
                leave_record = frappe.db.sql("""SELECT name FROM `tabEmployee Leave Record` WHERE date=%s AND employee=%s AND leave_duration='Half Day Afternoon'""", (current_date, employee_code), as_dict=True)
                if not leave_record:
                    exception = True
            elif attendance[0].attendance_status == "Half Day Afternoon":
                leave_record = frappe.db.sql("""SELECT name FROM `tabEmployee Leave Record` WHERE date=%s AND employee=%s AND leave_duration='Half Day Morning'""", (current_date, employee_code), as_dict=True)
                if not leave_record:
                    exception = True
            elif attendance[0].attendance_status == "Absent":
                exception = True

            if exception:
                date_str = current_date.strftime('%Y-%m-%d')
                if date_str not in exception_counts:
                    exception_counts[date_str] = 0
                exception_counts[date_str] += 1

        current_date += timedelta(days=1)

    return exception_counts
@frappe.whitelist()
def get_date_range(reference_date=None, start_date=None, last_date=None):
    from datetime import datetime, timedelta
    
    if reference_date:
        reference_date = datetime.strptime(reference_date, '%Y-%m-%d')
        year = reference_date.year
        month = reference_date.month
        start_date = datetime(year, month, 1)
        last_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:
        if start_date and last_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            last_date = datetime.strptime(last_date, '%Y-%m-%d')
        else:
            raise ValueError("Either reference_date or both start_date and last_date must be provided")

    return start_date, last_date

@frappe.whitelist()
def get_employee_monthly_attendance_for_calendar(employee_code, reference_date=None, start_date=None, last_date=None):
    from datetime import datetime, timedelta
    
    # Get the date range
    start_date, last_date = get_date_range(reference_date, start_date, last_date)

    # Initialize an empty dictionary to store attendance statuses
    attendance_statuses = {}

    # Iterate through each day of the month
    current_date = start_date
    while current_date <= last_date:
        date_str = current_date.strftime('%Y-%m-%d')
        attendance_statuses[date_str] = None  # Default to None, will update based on logic below

        # Check if the current day is a holiday
        holiday_list = get_employee_holiday_list_for_the_date(employee_code, current_date)
        
        if holiday_list:
            holiday = check_holiday_date_in_holiday_list(holiday_list.name, current_date)
            if holiday:
                holiday_exception = check_employee_holiday_exception(employee_code, current_date)
                if not holiday_exception:
                    attendance_statuses[date_str] = 'Holiday'  # Mark as holiday if no exception
                    current_date += timedelta(days=1)
                    continue
        
        # Check for attendance records
        attendance = frappe.db.sql("""SELECT attendance_status FROM `tabAttendance` WHERE attendance_date=%s AND employee=%s and docstatus=1""", (current_date, employee_code), as_dict=True)
        
        if attendance:
            status = attendance[0].attendance_status
            if status == "Present":
                attendance_statuses[date_str] = 'P'
            elif status == "Leave":
                attendance_statuses[date_str] = 'L'
            elif status == "Half Day Morning":
                attendance_statuses[date_str] = 'HM'
            elif status == "Half Day Afternoon":
                attendance_statuses[date_str] = 'HA'
            elif status == "Absent":
                attendance_statuses[date_str] = 'A'
        else:
            # If no attendance record, mark as 'Not Entered'
            attendance_statuses[date_str] = 'NE'

        current_date += timedelta(days=1)

    return attendance_statuses

@frappe.whitelist()
def get_all_employees_monthly_attendance(start_date, end_date):
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Fetch the list of employees
    employee_list = frappe.db.sql("""SELECT employee_code, employee_name FROM `tabEmployee` WHERE status='On Job'""", as_dict=True)

    # Initialize an empty dictionary to store attendance statuses
    attendance_summary = defaultdict(lambda: {   
        'Employee Code':'',
        'Employee Name': '',
        'Leave Count': 0,
        'Present Count': 0,
        'Not Entered Count': 0,
        'Absent Count': 0
    })

    for employee in employee_list:
        employee_code = employee['employee_code']
        employee_name = employee['employee_name']
        
        attendance_summary[employee_code]['Employee Code'] = employee_code
        
        # Set the employee name in the summary        
        attendance_summary[employee_code]['Employee Name'] = employee_name

        # Iterate through each day of the month
        current_date = start_date
        while current_date <= end_date:
            
            date_str = current_date.strftime('%Y-%m-%d')

            # Check if the current day is a holiday
            holiday_list = get_employee_holiday_list_for_the_date(employee_code, current_date)
            
            if holiday_list:
                holiday = check_holiday_date_in_holiday_list(holiday_list.name, current_date)
                if holiday:
                    holiday_exception = check_employee_holiday_exception(employee_code, current_date)
                    if not holiday_exception:
                        # Skip processing if it's a holiday
                        current_date += timedelta(days=1)
                        continue

            # Check for attendance records
            attendance = frappe.db.sql("""SELECT attendance_status FROM `tabAttendance` WHERE attendance_date=%s AND employee=%s and docstatus=1""", (current_date, employee_code), as_dict=True)
            
            if attendance:
                status = attendance[0].attendance_status
                
                if status == "Present":
                    attendance_summary[employee_code]['Present Count'] += 1
                elif status == "Leave":
                    attendance_summary[employee_code]['Leave Count'] += 1
                elif status == "Half Day Morning" or status == "Half Day Afternoon":
                    attendance_summary[employee_code]['Leave Count'] += 0.5
                    
                    if frappe.db.exists("""Select name from `tabEmployee Leave Record` where employee=%s and date=%s  and (leave_duration='Half Day Morning' or leave_duration='Half Day Afternoon') and docstatus=1 """,(employee_code,current_date)):
                        pass
                    else:
                        attendance_summary[employee_code]['Not Entered Count'] += 0.5        
                    
                elif status == "Absent":
                    attendance_summary[employee_code]['Absent Count'] += 1
            else:
                # If no attendance record, mark as 'Not Entered'
                attendance_summary[employee_code]['Not Entered Count'] += 1

            current_date += timedelta(days=1)

    return dict(attendance_summary)

@frappe.whitelist()
def get_employee_monthly_attendance_status(employee, start_date, end_date):
    
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    invalid_data_count = 0
    current_date = start_date

    while current_date <= end_date:
        
        # Check if the current day is a holiday
        holiday_list = get_employee_holiday_list_for_the_date(employee, current_date)
        
        if holiday_list:
            is_holiday = check_holiday_date_in_holiday_list(holiday_list.name, current_date)
            
            if is_holiday:
                
                # Check if there is a holiday exception for the employee
                holiday_exception = check_employee_holiday_exception(employee, current_date)
                if not holiday_exception:
                    # Skip processing if it's a holiday and no exception is found
                    current_date += timedelta(days=1)                    
                    continue

        # Check for attendance records
        attendance = frappe.db.sql("""
            SELECT attendance_status 
            FROM `tabAttendance` 
            WHERE attendance_date=%s AND employee=%s AND docstatus=1
        """, (current_date, employee), as_dict=True)
        
                
        if attendance:
            status = attendance[0].attendance_status
            if status in ["Present", "Leave"]:
                pass  # Valid attendance statuses
            elif status in ["Half Day Morning", "Half Day Afternoon"]:
                # Check if there is a corresponding leave record for half-day
                if not frappe.db.exists("""
                    SELECT name 
                    FROM `tabEmployee Leave Record` 
                    WHERE employee=%s AND date=%s 
                    AND (leave_duration='Half Day Morning' OR leave_duration='Half Day Afternoon') 
                    AND docstatus=1
                """, (employee, current_date)):
                    invalid_data_count += 1  # Invalid if no corresponding leave record
            elif status == "Absent":
                invalid_data_count += 1  # Invalid if absent
        else:
            # If no attendance record, mark as 'Not Entered'
            invalid_data_count += 1

        current_date += timedelta(days=1)

    return invalid_data_count > 0
@frappe.whitelist()
def get_distinct_years():
    years = frappe.db.sql("""
        SELECT DISTINCT YEAR(payroll_date) as year
        FROM `tabSalary Slip`
        ORDER BY year DESC
    """, as_list=True)
    
    # Flatten the list of tuples
    return [str(year[0]) for year in years]

@frappe.whitelist()
def get_default_salary_group():
    default_salary_group = frappe.db.get_value('Salary Group', {'is_default': 1}, 'name')
    return default_salary_group


    