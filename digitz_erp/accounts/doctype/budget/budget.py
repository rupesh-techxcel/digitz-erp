# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime
from frappe.utils import getdate

class Budget(Document):

	def validate(self):
     
		self.validate_budget()     
  
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
   
   
	def validate_budget(self):
		"""
		Check for overlapping budget periods based on 'budget_against' type.
		"""
		from frappe.utils import getdate

		# Get the budget's from_date and to_date
		from_date = getdate(self.from_date)
		to_date = getdate(self.to_date)

		if self.budget_against == "Company":
			# Construct a query to find overlapping budgets for "Company"
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
			""", (self.budget_against, self.name, to_date, from_date, from_date, to_date, from_date, to_date))

			# If any overlapping budget records are found, raise an error
			if overlapping_budgets:
				frappe.throw(f"An overlapping budget exists for {self.budget_against} from {from_date} to {to_date}. "
							"Please adjust the date range to avoid conflicts.")

		elif self.budget_against in ["Project", "Cost Center"]:
			# Determine the field for budget_against value
			budget_against_field = "project" if self.budget_against == "Project" else "cost_center"

			# Check for an existing budget for the same project or cost center
			duplicate_budget = frappe.db.sql(f"""
				SELECT name FROM `tabBudget`
				WHERE
					budget_against = %s
					AND {budget_against_field} = %s
					AND name != %s
			""", (self.budget_against, getattr(self, budget_against_field), self.name))

			# If a duplicate budget is found, raise an error
			if duplicate_budget:
				frappe.throw(f"A budget already exists for {self.budget_against} '{getattr(self, budget_against_field)}'. "
							"Only one budget is allowed for the same Project or Cost Center.")

