# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document

class EmployeeLoan(Document):
	
	def before_validate(self):
     
		self.balance_to_be_deducted = self.loan_amount
  
	def validate(self):
     
		self.validation_permission_for_approval()
    
		try:
			loan_exists = frappe.db.sql("""
				SELECT name FROM `tabEmployee Loan` 
				WHERE employee=%s 
				AND (loan_status='Approved' OR loan_status='On Going') 
				AND name!=%s
			""", (self.employee, self.name))

			if loan_exists:
				frappe.msgprint(f"There is already another open loan ({loan_exists}) for this employee.")

		except Exception as e:
			frappe.log_error(f"Error checking for existing loan: {str(e)}", "Loan Check Error")
			frappe.throw("An error occurred while checking for existing loans. Please try again or contact support.")
   
	def validation_permission_for_approval(self):
		
		if self.loan_status  == "Approved":
			user_roles = frappe.get_roles(frappe.session.user)
			if 'Management' not in user_roles :
				frappe.throw("You do not have the necessary privileges to approve this leave application.")
		
	def on_submit(self):     
		if self.loan_status == "Requested":
			frappe.throw("The loan request must be approved prior to submission.")

@frappe.whitelist()
def get_employee_loan_history(employee, date):
    
   return frappe.db.sql("""
        SELECT name, loan_date, loan_amount, loan_status, total_deducted_amount, balance_to_be_deducted
        FROM `tabEmployee Loan`
        WHERE employee=%s AND date<%s
    """, (employee, date), as_dict=True)

