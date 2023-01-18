# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.data import now


class DeliveryNote(Document):
    # frappe.get_all("Delivery Note Item", fields="*", filters={
    #                "docstatus": 1, "against_sales_invoice": None, "for_sales_invoice": None})

    @frappe.whitelist()
    def generate_sale_invoice(self):
        sales_invoice_name = ""
        # do_exists = 0
        # if frappe.db.exists('Sales Invoice', {"against_sales_invoice": self.name}):
        #     sales_invoice_doc = frappe.get_doc(
        #         'Sales Invoice', {"against_sales_invoice": self.name})
        #     sales_invoice_name = sales_invoice_doc.name
        #     sales_invoice_doc.delete()
        #     do_exists = 1
        delivery_note_doc = frappe.get_doc('Delivery Note', self.name)

        sales_invoice = self.__dict__
        sales_invoice['doctype'] = 'Sales Invoice'
        sales_invoice['name'] = sales_invoice_name
        sales_invoice['naming_series'] = 'SINV-.YYYY.-'
        sales_invoice['posting_date'] = now()
        del sales_invoice['against_sales_invoice']
        for item in sales_invoice['items']:
            item.doctype = "Sales Invoice Item"

        sales_invoice_doc = frappe.get_doc(
            sales_invoice).insert(ignore_permissions=True)
        delivery_note_doc.for_sales_invoice = sales_invoice_doc.name
        delivery_note_doc.save(ignore_permissions=True)
        frappe.db.commit()
        # if do_exists:
        #     frappe.msgprint("Sales Invoice updated successfully.")
        # else:
        frappe.msgprint("Sales Invoice created successfully.")
