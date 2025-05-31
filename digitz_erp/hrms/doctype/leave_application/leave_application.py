# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from datetime import datetime

from digitz_erp.api.leave_application_api import get_employee_leave_policy_assignment, validate_leave_period_dates,get_employee_holiday_list,get_leave_period,get_leave_dates_excluding_holidays,get_leave_and_holiday_count,get_system_approval_for_the_leaves_applied
from digitz_erp.api.employee_api import get_employee_holiday_list_for_the_date, check_holiday_date_in_holiday_list,check_employee_holiday_exception
from digitz_erp.api.employee_api import get_employee_shift, validate_employee_shift

class LeaveApplication(Document):	
    
	def before_validate(self):
		pass        

	def validate(self):
     
		self.validation_permission_for_approval()
  
		# Validate the leave period. Whether the correct leave period has been assigned based on the leave from_date and leave to_date. Also check if any overlaping is there in the leave_period
		self.validate_leave_period()
  
		self.validate_leave_type()
  
  		# Check employee has a valid leave_policy assigned for the selected leave_period (leave_period retrieved for the leave from_date and leave to_date)
		self.validate_employee_leave_policy()		
  
		self.validate_half_day_full_day()
		
		self.validate_holiday()
  
		leave_dates = get_leave_dates_excluding_holidays(self.leave_type,self.holiday_list, self.leave_from_date, self.leave_to_date)
		self.validate_leave_dates(leave_dates)
  
		# Verify leave with existing attendance entry 
		self.verify_leave_date_with_attendance(leave_dates)
	
 
	def validation_permission_for_approval(self):
     
		if self.leave_status  == "Approved":
			user_roles = frappe.get_roles(frappe.session.user)
			if 'Management' not in user_roles :
				frappe.throw("You do not have the necessary privileges to approve this leave application.")
    	
	def validate_holiday(self):
     
		holiday_list = get_employee_holiday_list(self.employee, self.leave_period)

		if holiday_list != self.holiday_list:
			frappe.throw("Incorrect Holiday List.")
		
		holiday = check_holiday_date_in_holiday_list(holiday_list, self.date)

		if holiday:
			holiday_exception = check_employee_holiday_exception(self.employee, self.date)

			if not holiday_exception:				
				frappe.throw("Leave application cannot be added on a holiday.")    
	
	def validate_leave_type(self):
     
		leave_type_doc = frappe.get_doc("Leave Type",self.leave_type)
		if leave_type_doc.is_partially_paid_leave and self.leave_duration != "Full Day":
			frappe.throw("Only 'Full Day' leave can be assigned for partially paid leave types.")
	
	def validate_leave_balance(self):
		
		leaves_data = get_leave_and_holiday_count(self.leave_type,self.holiday_list, self.leave_from_date,self.leave_to_date)
		
		no_of_leaves_applied = leaves_data.get('leave_count')
		get_system_approval_for_the_leaves_applied(self.employee,self.leave_period, self.leave_type, no_of_leaves_applied)
     
	def validate_half_day_full_day(self):
		
		if((self.leave_duration == "Half Day Morning" or self.leave_duration == "Half Day Afternoon") and self.no_of_leaves>1):
			frappe.throw("For half-day leaves, please select only one day.")

	def validate_employee_leave_policy(self):
		
		lpa= get_employee_leave_policy_assignment(self.employee,self.leave_period)
		
		if not lpa:
			frappe.throw("No leave policy assignment exists for the selected leave period and employee.")
   
	def validate_leave_period(self):
		
		leave_period= get_leave_period(self.leave_from_date, self.leave_to_date)

		if (leave_period != self.leave_period):
			frappe.throw("Invalid leave period.")
  
		validate_leave_period_dates(self.leave_period, self.leave_from_date, self.leave_to_date)
  
	def validate_leave_dates(self, leave_dates):
     
		for leave_date in leave_dates:
			# Check if attendance for the employee on the specified date already exists
			if frappe.db.exists("Employee Leave Record", {"employee": self.employee, "date": leave_date, "name": ["!=", self.name]}):
       
				formatted_date = datetime.strptime(leave_date, '%Y-%m-%d').strftime('%d-%m-%Y')
				frappe.throw(f"Leave Application for the employee already exists for {formatted_date}.")
     
   
	def on_submit(self):
		
		if self.leave_status != "Approved":
			frappe.throw("The Leave Application must be approved prior to submission.")

		self.validate_shifts_for_the_leave_dates()
  
		self.validate_leave_balance()
   
		self.insert_leave_records()
  
  
	def verify_leave_date_with_attendance(self,leave_dates):
     
		for leave_date in leave_dates:
      
			# Check for submitted attendance for the day. Note that same kind of checking exists in Attendance also whether a submitted Leave Application exists for the day

			attendance_for_the_date = frappe.db.sql("""Select attendance_status from `tabAttendance` where employee=%s and attendance_date=%s and docstatus=1""", (self.employee, leave_date), as_dict=True )
		
			if attendance_for_the_date:
		
				# Generic case , leave (for all leave_durations) cannot be added when there is an attendance entry exists
				if 	attendance_for_the_date[0].attendance_status == "Present" or attendance_for_the_date[0].attendance_status == "Work From Home":
					frappe.throw(f"An attendance entry exists for {leave_date}. Leave cannot be applied for this day.")

				# When user attempt for a leave_duration as "Half Day Morning". There should not be an Attendance as "Half Day Morning"
				if self.leave_duration  == "Full Day" and (attendance_for_the_date[0].	attendance_status=="Half Day Morning" or attendance_for_the_date[0].attendance_status=="Half DayAfternoon"):
    
					frappe.throw(f"Leave mismatch with Attendance Entry on {leave_date}.")     
     	
				# When user attempt for a leave_duration as "Half Day Morning". There should not be an Attendance as "Half Day Morning"
				if self.leave_duration  == "Half Day Morning" and attendance_for_the_date[0].	attendance_status=="Half Day Morning":
					frappe.throw(f"'Half Day Morning' Attendance Entry exists on {leave_date}. ")     
					
				# When user attempt for a leave_duration as "Half Day Afternoon". There should not be an Attendance as "Half Day Afternoon"
				if self.leave_duration  == "Half Day Afternoon" and attendance_for_the_date[0].	attendance_status=="Half Day Afternoon":
					frappe.throw(f"'Half Day Afternoon' Attendance Entry exists on {leave_date}. ")     
		
    # This method checks whether shift allocation is mandatory and shift not allocated for the leave date.
	def validate_shifts_for_the_leave_dates(self):
		
		leave_dates = get_leave_dates_excluding_holidays(self.leave_type,self.holiday_list, self.leave_from_date, self.leave_to_date)
		for leave_date in leave_dates:
			if not validate_employee_shift(self.employee,leave_date):
				frappe.throw("Shift not allocated for the employee. Shift Allocation mandatory as per HR Settings.");	

	def change_attendance_status_to_leave_and_link_leave_record(self,attendance, leave_record):
		
		frappe.db.set_value("Attendance",attendance, {"Status": "Leave", "Leave Record": leave_record})
  
	def on_cancel(self):
		self.delete_leave_record_for_the_leave_application()
  
  
	def delete_leave_record_for_the_leave_application(self):
		
		employee_leave_records = frappe.get_all('Employee Leave Record', 
												filters={'leave_application': self.name}, 
												fields=['name'])

		# Delete each related Employee Leave Record document
		for record in employee_leave_records:
			frappe.delete_doc('Employee Leave Record', record.name)
		
		frappe.msgprint('Related Employee Leave Record documents have been deleted.')
		
	def insert_leave_records(self):
			
		leave_dates = get_leave_dates_excluding_holidays(self.leave_type,self.holiday_list, self.leave_from_date, self.leave_to_date)

		# Make sure there is no Attendance entries conflicting with the leave
		self.verify_leave_date_with_attendance(leave_dates)

		for leave_date in leave_dates:
		
			new_leave_record = frappe.new_doc('Employee Leave Record')
			new_leave_record.employee =  self.employee
			new_leave_record.leave_type= self.leave_type
			new_leave_record.date = leave_date
			new_leave_record.leave_application = self.name
			new_leave_record.leave_period = self.leave_period
			
			new_leave_record.status = self.leave_duration
			new_leave_record.insert()

			attendance_for_the_date = frappe.db.sql("""Select name,status from `tabAttendance` where employee=%s and attendance_date=%s and docstatus=1""", (self.employee, leave_date), as_dict=True )

			if attendance_for_the_date:
				if attendance_for_the_date[0].status == "Absent":
					self.change_attendance_status_to_leave_and_link_leave_record(attendance_for_the_date, new_leave_record.name)
			else:				
				self.insert_attendance_for_the_leave_date(leave_date,new_leave_record.name)
    
	def insert_attendance_for_the_leave_date(self, leave_date, leave_record_name):     
		
		shift,shift_allocation = get_employee_shift(self.employee, leave_date, False)

		attendance= frappe.new_doc("Attendance")
		attendance.employee = self.employee
		attendance.attendance_date = leave_date

		if self.leave_duration == "Full Day":
		
			attendance.attendance_status = "Leave"
			attendance.leave_record = leave_record_name
			self.fill_shift_information(attendance,shift,True)			
			attendance.created_via_leave = True

			if shift_allocation:
				attendance.attendance_end_time = shift_allocation.end_time
				attendance.actual_no_of_units = shift_allocation.expected_no_of_units
				attendance.attendance_ot = shift_allocation.expected_ot

			attendance.insert()
			attendance.submit()
   
		elif self.leave_duration  == "Half Day Morning" and self.mark_attendance_for_the_other_half_of_the_day:      
			attendance.attendance_status = "Half Day Afternoon"
			attendance.leave_record = leave_record_name
			attendance.shift = shift.name
			self.fill_shift_information(attendance,shift, False)			
			attendance.created_via_leave = True
			attendance.insert()
			attendance.submit()
   
		elif self.leave_duration  == "Half Day Afternoon" and self.mark_attendance_for_the_other_half_of_the_day:
      
			attendance.attendance_status = "Half Day Morning"
			attendance.leave_record = leave_record_name
			attendance.shift = shift.name
			self.fill_shift_information(attendance,shift,False)
			attendance.created_via_leave = True
			attendance.insert()
			attendance.submit()
   
	def fill_shift_information(self,attendance, shift, fill_units):
		attendance.shift = shift.name
		attendance.shift_start_time = shift.start_time
		attendance.shift_end_time = shift.end_time
		attendance.break_in_mins = shift.break_in_minutes
		attendance.standard_working_hours = shift.standard_working_hours
		attendance.standard_no_of_units = shift.no_of_units_per_day

		if fill_units:
			attendance.attendance_start_time = shift.start_time
			attendance.attendance_end_time = shift.end_time
			attendance.actual_no_of_units = shift.no_of_units_per_day
		