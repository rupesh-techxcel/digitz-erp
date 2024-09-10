# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Timesheet(Document):
	pass

# @frappe.whitelist
# def create_Attendance(employee, shift):
# 	attendance= frappe.new_doc('Attendance')
# 	attendance.employee= employee
# 	attendance.shift= shift
# 	attendance.save()
# 	return True