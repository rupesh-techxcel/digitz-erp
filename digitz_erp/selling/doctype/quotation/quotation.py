# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Quotation(Document):

	@frappe.whitelist()
	def generate_sale_invoice(self, auto_generate_delivery_note):
		sales_invoice_name = ""  
		
		quotationName =  self.name
		sales_invoice = self.__dict__
		sales_invoice['doctype'] = 'Sales Invoice'
		sales_invoice['name'] = sales_invoice_name
		sales_invoice['naming_series'] = ""
		sales_invoice['posting_date'] = self.posting_date
		sales_invoice['posting_time'] = self.posting_time
		sales_invoice['quotation'] = quotationName
		sales_invoice['auto_save_delivery_note'] = auto_generate_delivery_note
		# Change the document status to draft to avoid error while submitting child table
		sales_invoice['docstatus'] = 0
		for item in sales_invoice['items']:            
			item.doctype = "Sales Invoice Item"
			item.delivery_note_item_reference_no = item.name
			item._meta = ""       
			
		sales_invoice_doc = frappe.get_doc(
			sales_invoice).insert(ignore_permissions=True)               
		
		frappe.db.commit()

		# si =  frappe.get_doc('Sales Invoice',sales_invoice_doc.name)
  
		if auto_generate_delivery_note:
			delivery_note_name = ""
        
			si_name = sales_invoice_doc.name        
			
			
			do_exists = False
			
			if frappe.db.exists('Sales Invoice Delivery Notes', {'parent': si_name}):    
					do_exists = True
					delivery_note_name =  frappe.db.get_value('Sales Invoice Delivery Notes',{'parent':si_name},['delivery_note'] )
					# Remove the reference first before deleting the actual document
					frappe.db.delete('Sales Invoice Delivery Notes',{'parent':si_name})
					delivery_note_doc = frappe.get_doc('Delivery Note', delivery_note_name)
					delivery_note_name = delivery_note_doc.name
					delivery_note_doc.delete()
					print("delivery note deleted")
			
			delivery_note = self.__dict__
			delivery_note['doctype'] = 'Delivery Note'
			# delivery_note['against_sales_invoice'] = delivery_note['name']
			# delivery_note['name'] = delivery_note_name        
			delivery_note['naming_series'] = ""
			delivery_note['posting_date'] = self.posting_date
			delivery_note['posting_time'] = self.posting_time

			delivery_note['auto_generated_from_sales_invoice'] = 1

			for item in delivery_note['items']:
				item.doctype = "Delivery Note Item"    
				item._meta = ""        

			doNo = frappe.get_doc(delivery_note).insert()
			frappe.db.commit()
			
			if(not do_exists):
				delivery_note_name = doNo.name
				
			# Rename the delivery note to the original dnoNo which is deleted
			if(do_exists):
				frappe.rename_doc('Delivery Note', doNo.name, delivery_note_name)
			
			# do = frappe.get_doc('Delivery Note', delivery_note_name)
			si = frappe.get_doc('Sales Invoice',si_name)

			row = si.append('delivery_notes', {'delivery_note': delivery_note_name})

			si.save()

			delivery_notes = frappe.db.get_list('Sales Invoice Delivery Notes', {'parent': ['=', si_name]},['delivery_note'], as_list=True)
			
			# It is likely that there will be only one delivery note for the sales invoice for this method.
			index = 0
			maxIndex = 3
			doNos = ""

			for delivery_noteName in delivery_notes:     
				delivery_note = frappe.get_doc('Delivery Note',delivery_noteName )   
				doNos = doNos + delivery_note.name + "   "
				index= index + 1
				if index == maxIndex:
					break     

			si = frappe.get_doc('Sales Invoice',si_name)

			si.delivery_notes_to_print = doNos
			
			index = 0        

			for item in si.items:            
				item.delivery_note_item_reference_no = doNo.items[index].name
				index = index + 1

			# Need to remove the next line to set auto_save_delivery_note
			si.auto_save_delivery_note = True
			si.save()
			print("From end of auto gen delivery note")
			
			frappe.msgprint("Sales Invoice created successfully with draft mode.")