# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from datetime import datetime
from frappe.utils import get_time

class Shift(Document):

	def before_validate(self):
		# Convert start_time and end_time to datetime objects
		from_time_obj = datetime.combine(datetime.min, get_time(self.start_time))
		to_time_obj = datetime.combine(datetime.min, get_time(self.end_time))

		# Calculate break time in seconds if defined, otherwise 0
		total_break_in_seconds = self.break_in_minutes * 60 if self.break_in_minutes and self.break_in_minutes > 0 else 0

		# Calculate pickup time in seconds if defined, otherwise 0
		total_pickup_in_seconds = self.pickup_time_in_minutes * 60 if self.pickup_time_in_minutes and self.pickup_time_in_minutes > 0 else 0

		# Calculate total seconds between from_time and to_time, subtracting both break and pickup times
		total_seconds = (to_time_obj - from_time_obj).total_seconds() - total_break_in_seconds - total_pickup_in_seconds

		# Calculate total hours and minutes
		total_hours, remainder = divmod(total_seconds, 3600)
		minutes, seconds = divmod(remainder, 60)

		# Convert remaining minutes to hours
		mins_to_hours = minutes / 60
		total_hours += mins_to_hours

		# Assign the result to standard_working_hours with two decimal precision
		self.standard_working_hours = round(total_hours, 2)

