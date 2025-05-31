# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime
class SalaryStructure(Document):
	
	def validate(self):
		# Iterate through the child table 'salary_structure_assignment'
		for assignment in self.salary_structure_assignment:
			# Check if there is any other 'Salary Structure' with the same employee
			# and with from_date greater than or equal to the current assignment's from_date
			other_salary_structures = frappe.db.sql("""
				SELECT ss.name
				FROM `tabSalary Structure Assignment` ssa
				INNER JOIN `tabSalary Structure` ss ON ss.name = ssa.parent
				WHERE ss.name != %s
				AND ssa.employee = %s
				AND ssa.from_date >= %s
				AND ss.docstatus < 2
			""", (self.name, assignment.employee, assignment.from_date))

			# If such a 'Salary Structure' exists, raise a validation error
			if other_salary_structures:
				formatted_date = datetime.strptime(assignment.from_date, '%Y-%m-%d').strftime('%d-%m-%Y')
				frappe.throw("Salary Structure '{0}' already exists for Employee '{1}' with a 'from_date' greater than or equal to '{2}'"
							.format(other_salary_structures[0][0], assignment.employee, formatted_date))

	