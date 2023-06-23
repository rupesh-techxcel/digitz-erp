import frappe
from frappe import _
from frappe.utils.print_format import download_pdf
from digitz_erp.pdf_utils import *


@frappe.whitelist()
def create_pdf_attachment(doctype, docname, print_format):
    doctype_folder = create_folder(_(doctype), "Home")
    title_folder = create_folder(docname, doctype_folder)
    pdf_data = get_pdf_data(doctype, docname, print_format)
    file_ref = save_and_attach(pdf_data, doctype, docname, title_folder)
    pdf_link = file_ref.file_url
    return pdf_link
