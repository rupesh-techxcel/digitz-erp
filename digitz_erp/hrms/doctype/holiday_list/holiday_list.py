# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta

class HolidayList(Document):
    
	def before_validate(self):
     
		# Check if there are other holiday lists for the same leave period
		other_holiday_list_for_the_period = frappe.db.exists(
			"Holiday List",
			{
				"leave_period": self.leave_period,
				"name": ("!=", self.name),
				"docstatus": 1
			}
		)

		# If no other holiday lists exist for the leave period, assign the current holiday list as default
		if not other_holiday_list_for_the_period:
			self.default_for_the_leave_period = True
			frappe.msgprint("The Holiday List has been set as the default for the leave period.", alert=True)
   
		self.add_weekly_off_to_holidays()
   
	def on_submit(self):
		self.reset_other_default_holiday_list_for_the_period()

	def reset_other_default_holiday_list_for_the_period(self):
		
		# If the current holiday list is set as default, check for other default holiday lists
		if self.default_for_the_leave_period:
			other_default_holiday_list = frappe.db.sql(
				"""SELECT name FROM `tabHoliday List`
				WHERE leave_period=%s AND default_for_the_leave_period=1 AND name!=%s AND docstatus=1""",
				(self.leave_period, self.name),
				as_dict=True
			)

			# If another default holiday list exists, set its default status to 0
			if other_default_holiday_list:
				frappe.db.set_value(
					"Holiday List", 
					other_default_holiday_list[0].name, 
					'default_for_the_leave_period', 
					0
				)
				frappe.msgprint(f"Reverted the holiday list {other_default_holiday_list[0].name} from being the default for the period.", alert=True)
    
	def add_weekly_off_to_holidays(self):
     
		if not self.weekly_off or not self.from_date or not self.to_date:
			frappe.throw("Please select Weekly Off, From Date, and To Date")

		weekly_off_map = {
			'Sunday': 6,
			'Monday': 0,
			'Tuesday': 1,
			'Wednesday': 2,
			'Thursday': 3,
			'Friday': 4,
			'Saturday': 5
		}

		from_date = frappe.utils.getdate(self.from_date)
		to_date = frappe.utils.getdate(self.to_date)
		selected_weekly_off = weekly_off_map[self.weekly_off]

		# Get existing dates in holidays
		existing_dates = {str(holiday.date) for holiday in self.holidays}

		current_date = from_date
		while current_date <= to_date:
			if current_date.weekday() == selected_weekly_off:
				if str(current_date) not in existing_dates:
					self.append('holidays', {
						'date': current_date,
						'holiday_name': 'Weekly Off',
						'weekly_off': self.weekly_off
					})
					existing_dates.add(str(current_date))
			current_date += timedelta(days=1)