# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document	
from datetime import datetime
from frappe.utils import get_time

from digitz_erp.api.employee_api import get_employee_holiday_list_for_the_date, check_holiday_date_in_holiday_list,check_employee_holiday_exception
from digitz_erp.api.employee_api import get_employee_shift_allocation

class Attendance(Document):
    
	def validate(self):
     
		# Leave status cannot be upadted directly but only with a leave application. While submitting the leave application, Attendance with status 'Leave' is getting created.

		if self.attendance_status == "Leave" and not self.created_via_leave:
			frappe.throw("Leave cannot be marked via Attendance. Please use the Leave Application instead.")
     
		# Check if attendance for the employee on the specified date already exists
		if frappe.db.exists("Attendance", {"employee": self.employee, "attendance_date": self.attendance_date, "docstatus":1, "name": ["!=", self.name]}):
			frappe.throw("Attendance for the employee on the specified date already exists.")

		# Check if shift allocation is mandatory
		shift_allocation_mandatory = frappe.get_single("HR Settings").shift_allocation_mandatory

		# Get employee shift allocation
		shift_allocation = get_employee_shift_allocation(self.employee, self.attendance_date)

		# If shift allocation is mandatory and not allocated, throw an error
		if not shift_allocation and shift_allocation_mandatory:
			frappe.throw(f"Shift not allocated for {self.employee}. Shift Allocation mandatory as per HR Settings.")

		# Get the salary structure assignment
		salary_structure = frappe.get_value("Salary Structure Assignment", {"employee": self.employee}, ["parent"])

		# If salary structure is not assigned, throw an error
		if not salary_structure:
			frappe.throw(f"Salary Structure not assigned for the employee {self.employee_name}")
   
		if self.shift_payment_unit != "HRS" and (self.attendance_status == "Half Day Morning" or self.attendance_status =="Half Day Afternoon"):
			frappe.throw("Half Day attendance is allowed only for HRS unit payment.")
   
		self.validate_holiday()   
	
	def validate_holiday(self):
		
		employee_holiday_list = get_employee_holiday_list_for_the_date(self.employee,self.attendance_date)

		if not employee_holiday_list:
			frappe.throw("Holiday List not found for the period.")
		else:
			holiday = check_holiday_date_in_holiday_list(employee_holiday_list.name, self.attendance_date)
   
			if holiday:
				holiday_exception = check_employee_holiday_exception(self.employee, self.attendance_date)

				if not holiday_exception:
					frappe.throw("Attendance cannot be marked on a holiday.")
				else:
					if(self.attendance_status != "Present" and self.attendance_status != "Work From Home"):
						frappe.throw("Holiday exception found. Attendance status must be 'Present' Or 'Work From Home'")
     
	def assign_holiday(self):
		
		self.is_a_holiday = False
  
		employee_holiday_list = get_employee_holiday_list_for_the_date(self.employee,self.attendance_date)

		if employee_holiday_list:			
		
			holiday = check_holiday_date_in_holiday_list(employee_holiday_list.name, self.attendance_date)

			if holiday:
				self.is_a_holiday = True

				
    
	def assign_effective_no_of_units(self):
		
		if not self.effective_no_of_units:
			self.effective_no_of_units = self.actual_no_of_units
         
     
	def before_validate(self):
		
		self.assign_holiday()
		
		if self.shift_payment_unit != "HRS" and (self.attendance_status == "Half Day Morning" or self.attendance_status =="Half Day Afternoon"):
			# Not a valid case
			pass
		
		elif( self.attendance_status != "Absent" and self.attendance_status != "Leave"):
		
			if self.shift_payment_unit == "HRS":
				self.calculate_attendance_for_hrs()    		
			else:
				self.calculate_attendence_for_unit()

		employee_doc = frappe.get_doc("Employee",self.employee)

		if employee_doc:
			self.employee_name = employee_doc.employee_name
		
		self.assign_effective_no_of_units()

		if self.standard_no_of_units and int(self.effective_no_of_units)> int(self.standard_no_of_units):
			self.attendance_ot = int(self.effective_no_of_units) - int(self.standard_no_of_units)

		# Commented the below code for Timesheet   
		if self.standard_working_hours and int(self.worked_hours) > int(self.standard_working_hours):
			self.attendance_ot = int(self.worked_hours) - int(self.standard_working_hours)
  
	def on_submit(self):
		if self.attendance_status == "Absent":
			frappe.throw("Cannot submit the attendance with Absent status. Mark leave for the employee to continue")
    
	def calculate_attendance_for_hrs(self):
     
		attendance_from_time_obj = datetime.combine(datetime.min, get_time(self.attendance_start_time))
		attendance_to_time_obj = datetime.combine(datetime.min, get_time(self.attendance_end_time))

		shift_from_time_obj = datetime.combine(datetime.min, get_time(self.shift_start_time))
		shift_to_time_obj = datetime.combine(datetime.min, get_time(self.shift_end_time))

		# Convert self.break_in_mins to an integer if possible, else set to 0
		try:
			break_in_mins = int(self.break_in_mins)
			total_break_in_seconds = break_in_mins * 60 if break_in_mins > 0 else 0
		except (TypeError, ValueError):
			total_break_in_seconds = 0

		# Calculate the total hours between from_time and to_time
		total_seconds_worked = (attendance_to_time_obj - attendance_from_time_obj).total_seconds() - total_break_in_seconds

		# Do not consider early entries for overtime. So get time from shift_from_time_obj only
		if attendance_from_time_obj < shift_from_time_obj:
			total_seconds_worked = (attendance_to_time_obj - shift_from_time_obj).total_seconds() - total_break_in_seconds  

		total_hours_worked, remainder = divmod(total_seconds_worked, 3600)
		minutes_worked, seconds_worked = divmod(remainder, 60)

		total_mins_to_hours = minutes_worked / 60
		total_hours_worked += total_mins_to_hours

		# Format total_hours with the decimal part
		total_hours_worked = round(total_hours_worked, 2)

		self.worked_hours = total_hours_worked    
		
		ot_applicable = self.get_ot_applicable()
  
		if ot_applicable and total_hours_worked > float(self.standard_working_hours):
			self.attendance_ot = total_hours_worked - float(self.standard_working_hours)
		else:
			self.attendance_ot = 0

		self.late_entry = attendance_from_time_obj > shift_from_time_obj
		self.early_exit = attendance_to_time_obj < shift_to_time_obj
  
	def get_ot_applicable(self):
    
		ot_applicable =frappe.get_single('HR Settings').overtime_applicable
  
		employee_doc = frappe.get_doc("Employee",self.employee)
  
		shift_doc = frappe.get_doc("Shift",self.shift)
		return ot_applicable and employee_doc.ot_applicable and shift_doc.ot_applicable

	def calculate_attendence_for_unit(self):
  
		standard_no_of_units = self.standard_no_of_units
		effective_no_of_units = self.effective_no_of_units
  
		ot_applicable = self.get_ot_applicable()
  
		if ot_applicable:
      	
			if float(effective_no_of_units)> float(standard_no_of_units):
				self.attendance_ot = float(effective_no_of_units) - float(standard_no_of_units)
    
			if self.is_a_holiday:
			    
				# Verify the following line works for default shift (if shift not allocated)
				shift_allocation = get_employee_shift_allocation(self.employee, self.attendance_date)
    
				if shift_allocation:

					# Only if the standard_no_of_units_per_holiday is assigned and having a value greater than zero
					# is considered otherwise it overtime is keeping as the same
					if shift_allocation[0].standard_no_of_units_per_holiday and shift_allocation[0].standard_no_of_units_per_holiday>0:

						self.standard_no_of_units = shift_allocation[0].standard_no_of_units_per_holiday
      
						if self.effective_no_of_units > self.standard_no_of_units:
							self.attendance_ot = self.effective_no_of_units - self.standard_no_of_units
       