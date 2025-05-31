# Copyright (c) 2024, Techxcel Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SalarySlip(Document):
	
 
	def on_update(self):
     
		payroll_detail =	frappe.db.sql("""Select ped.name from `tabPayroll Entry Detail` ped inner join `tabPayroll Entry` pe on pe.name=ped.parent and ped.employee=%s and pe.start_date=%s and pe.end_date=%s and ped.data_status='Completed'""",(self.employee, self.salary_from_date,self.salary_to_date), as_dict=True)
  
		if payroll_detail:
			payroll_detail_doc =  frappe.get_doc("Payroll Entry Detail", payroll_detail[0].name)
			payroll_detail_doc.salary_slip_generated = True
			payroll_detail_doc.salary_slip = self.name
			payroll_detail_doc.save()
			frappe.msgprint(f"A salary slip has been created in draft mode for {self.employee}. Please review and submit the salary slip.",alert=True,indicator='green'
)
