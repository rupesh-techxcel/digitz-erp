# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime

class Budget(Document):

	def validate(self):
     
		self.check_for_overlapping_budget()     
    
	def before_insert(self):
     
		if not self.budget_name:
			self.generate_budget_name()		
  
	def generate_budget_name(self):
     
		if not self.budget_name:  # If the user manually input the name, skip this logic
			# Define prefixes for different `budget_against` types
			prefixes = {
				"Project": "PROJ",
				"Company": "COMP",
				"Cost Center": "CST-CTR"
			}

			# Determine the prefix based on the `budget_against` field
			prefix = prefixes.get(self.budget_against)
			if not prefix:
				frappe.throw("Invalid 'Budget Against' value for Budget.")

			# Extract the relevant entity based on the `budget_against` type
			if self.budget_against == "Project":
				entity = self.project_short_name  # Assuming `project_short_name` is set
			elif self.budget_against == "Company":
				entity = self.company  # Assuming `company` is set
			elif self.budget_against == "Cost Center":
				entity = self.cost_center  # Assuming `cost_center` is set

			# Handle date formatting only if `budget_against` is 'Company'
			if self.budget_against == "Company":
				# Convert from_date and to_date to datetime objects if needed
				if not self.from_date or not self.to_date:
					frappe.throw("For 'Company', both 'From Date' and 'To Date' are mandatory.")

				from_date = datetime.strptime(self.from_date, "%Y-%m-%d") if isinstance(self.from_date, str) else self.from_date
				to_date = datetime.strptime(self.to_date, "%Y-%m-%d") if isinstance(self.to_date, str) else self.to_date

				# Format dates in 'DD-MM-YYYY' format
				formatted_from_date = from_date.strftime("%d-%m-%Y")
				formatted_to_date = to_date.strftime("%d-%m-%Y")

				# Construct the name with dates
				self.name = f"{prefix}-{entity}-{formatted_from_date}-to-{formatted_to_date}"
			else:
				# Construct the name without dates for other `budget_against` types
				self.name = f"{prefix}-{entity}"

			# Log the generated name for debugging
			frappe.logger().debug(f"Generated custom name for Budget: {self.name}")
   
	def check_for_overlapping_budget(doc):
		"""
		Check for overlapping budget periods based on 'budget_against' type.
		"""
		# Get the budget's from_date and to_date
		from_date = getdate(doc.from_date)
		to_date = getdate(doc.to_date)

		# Construct a query to find overlapping budgets
		overlapping_budgets = frappe.db.sql("""
			SELECT name FROM `tabBudget`
			WHERE
				budget_against = %s
				AND name != %s
				AND (
					(from_date <= %s AND to_date >= %s) OR
					(from_date <= %s AND to_date >= %s) OR
					(from_date >= %s AND to_date <= %s)
				)
		""", (doc.budget_against, doc.name, to_date, from_date, from_date, to_date, from_date, to_date))

		# If any overlapping budget records are found, raise an error
		if overlapping_budgets:
			frappe.throw(f"An overlapping budget exists for {doc.budget_against} from {from_date} to {to_date}. "
							"Please adjust the date range to avoid conflicts.")
