# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils import now
from frappe.model.document import Document
from datetime import datetime,timedelta
from digitz_erp.api.settings_api import get_default_company
from digitz_erp.api.settings_api import add_seconds_to_time


class TabSales (Document):

    def Voucher_In_The_Same_Time(self):
        possible_invalid= frappe.db.count('Tab Sales', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time]})
        return possible_invalid
        
    def Set_Posting_Time_To_Next_Second(self):
		# Add 12 seconds to self.posting_time and update it
		self.posting_time = add_seconds_to_time(str(self.posting_time), seconds=12)

    def before_validate(self):

        # When duplicating the voucher user may not remember to change the date and time. So do not allow to save the voucher to be
        # posted on the same time with any of the existing vouchers. This also avoid invalid selection to calculate moving average value


        if(self.Voucher_In_The_Same_Time()):
            self.Set_Posting_Time_To_Next_Second()

            if(self.Voucher_In_The_Same_Time()):
                self.Set_Posting_Time_To_Next_Second()

                if(self.Voucher_In_The_Same_Time()):
                    self.Set_Posting_Time_To_Next_Second()

                    if(self.Voucher_In_The_Same_Time()):
                        frappe.throw("Voucher with same time already exists.")
        
        if not self.company:
            self.company = get_default_company()
        
        if self.is_new():
            self.paid_amount = 0
             # Remove existing ref for duplicate vouchers        
            self.sales_invoice_no_ref = None

        if self.credit_sale == 0:
            self.paid_amount = self.rounded_total
        else:
            self.paid_amount = 0

    def validate_item(self):

        posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))

        default_company = frappe.db.get_single_value("Global Settings",'default_company')

        company_info = frappe.get_value("Company",default_company,['allow_negative_stock'], as_dict = True)

        allow_negative_stock = company_info.allow_negative_stock

        if not allow_negative_stock:
            allow_negative_stock = False

        for docitem in self.items:

            #print(docitem.item)

            # previous_stocks = frappe.db.get_value('Stock Ledger', {'item':docitem.item,'warehouse': docitem.warehouse , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],order_by='posting_date desc', as_dict=True)

            previous_stock_balance = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
            , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
            order_by='posting_date desc', as_dict=True)

            if(not previous_stock_balance and  allow_negative_stock==False):
                frappe.throw("No stock exists for" + docitem.item  + " from sales invoice")

            if(allow_negative_stock== False and previous_stock_balance.balance_qty< docitem.qty_in_base_unit):
                frappe.throw("Sufficiant qty does not exists for the item " + docitem.item + " required Qty= " + str(docitem.qty_in_base_unit) +
                " " + docitem.base_unit + " and available Qty=" + str(previous_stock_balance.balance_qty) + " " + docitem.base_unit )

    def validate(self):
        self.validate_item()
        # self.validate_item_valuation_rates()
    
    def validate_item_valuation_rates(self):
        
        posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))
        for docitem in self.items:
                # previous_stocks = frappe.db.get_value('Stock Ledger', {'item':docitem.item,'warehouse': docitem.warehouse , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],order_by='posting_date desc', as_dict=True)

                previous_stock_balance = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
                , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
                order_by='posting_date desc', as_dict=True)

                if(not previous_stock_balance):                    
                    valuation_rate = frappe.get_value("Item", docitem.item, ['item_valuation_rate'])
                    if(valuation_rate == 0):
                        frappe.throw("Please provide a valuation rate for the item, as there is no existing purchase invoice for it.")
   

    def on_submit(self):
        self.submit_sales_invoice()

    def submit_sales_invoice(self):
        #  if self.docstatus == 1:
        sales_invoice = frappe.get_doc('Sales Invoice', {'tab_sales':self.name})
        # si_do = frappe.get_doc('Sales Invoice',self.sales_invoice_no_ref)
        sales_invoice.submit()

    @frappe.whitelist()
    def generate_sales_invoice(self):

        # Once submitted, this method need not run
        if(self.docstatus ==1):
            return

        sales_invoice_name = ""
        # do_exists = 0
        # if frappe.db.exists('Sales Invoice', {"against_sales_invoice": self.name}):
        #     sales_invoice_doc = frappe.get_doc(
        #         'Sales Invoice', {"against_sales_invoice": self.name})
        #     sales_invoice_name = sales_invoice_doc.name
        #     sales_invoice_doc.delete()
        #     do_exists = 1

        #print("self.name")
        #print(self.name)

        sales_invoice = frappe.db.get_value('Sales Invoice',{'tab_sales': self.name}, ['name'])

        #print("sales_invoice")
        #print(sales_invoice)

        if(sales_invoice):

        # if frappe.db.exists('Sales Invoice', {'tab_sales': self.name}):
            sales_invoice = frappe.get_doc('Sales Invoice', {'tab_sales':self.name})

            #print("sales invoice found")
            #print(sales_invoice)
            # sales_invoice = frappe.get_doc
            # delivery_note_doc.delete()
            # #print("delivery note deleted")

            sales_invoice.customer = self.customer
            sales_invoice.customer_name = self.customer_name
            sales_invoice.customer_display_name = self.customer_display_name
            sales_invoice.customer_address = self.customer_address
            sales_invoice.reference_no = self.reference_no
            sales_invoice.posting_date = self.posting_date
            sales_invoice.posting_time = self.posting_time
            sales_invoice.ship_to_location = self.ship_to_location
            sales_invoice.salesman = self.salesman
            sales_invoice.salesman_code = self.salesman_code
            sales_invoice.tax_id = self.tax_id
            sales_invoice.lpo_no = self.lpo_no
            sales_invoice.lpo_date = self.lpo_date
            sales_invoice.price_list = self.price_list
            sales_invoice.rate_includes_tax = self.rate_includes_tax
            sales_invoice.warehouse = self.warehouse
            sales_invoice.credit_sale = self.credit_sale
            sales_invoice.credit_days = self.credit_days
            sales_invoice.payment_terms = self.payment_terms
            sales_invoice.payment_mode = self.payment_mode
            sales_invoice.payment_account = self.payment_account
            sales_invoice.remarks = self.remarks
            sales_invoice.gross_total = self.gross_total
            sales_invoice.total_discount_in_line_items = self.total_discount_in_line_items
            sales_invoice.tax_total = self.tax_total
            sales_invoice.net_total = self.net_total
            sales_invoice.round_off = self.round_off
            sales_invoice.rounded_total = self.rounded_total
            sales_invoice.terms = self.terms
            sales_invoice.terms_and_conditions = self.terms_and_conditions
            sales_invoice.auto_generated_from_delivery_note = False
            sales_invoice.address_line_1 = self.address_line_1
            sales_invoice.address_line_2 = self.address_line_2
            sales_invoice.area_name = self.area_name
            sales_invoice.country = self.country
            sales_invoice.quotation = self.quotation
            sales_invoice.sales_order = self.sales_order

            # Remove existing child table values
            # frappe.db.sql("DELETE FROM `tabDelivery Note Item` where parent=%s", delivery_note_name)
            # Manually update the sales invoice details

            # Refresh document
            # delivery_note_doc = frappe.get_doc('Delivery Note', delivery_note_name)

            # target_items = []

            # for item in self.items:
            #     target_item = delivery_note_doc.append('items', {} )
            #     frappe.copy_doc(item, target_item)
            #     target_items.append(target_item)

            sales_invoice.save()
            # Remove existing child table values
            frappe.db.sql("DELETE FROM `tabSales Invoice Item` where parent=%s", sales_invoice.name)

            # target_items = []

            idx = 0

            for item in self.items:
                idx = idx + 1
                sales_invoice_item = frappe.new_doc("Sales Invoice Item")
                sales_invoice_item.warehouse = item.warehouse
                sales_invoice_item.item = item.item
                sales_invoice_item.item_name = item.item_name
                sales_invoice_item.display_name = item.display_name
                sales_invoice_item.qty =item.qty
                sales_invoice_item.unit = item.unit
                sales_invoice_item.rate = item.rate
                sales_invoice_item.base_unit = item.base_unit
                sales_invoice_item.qty_in_base_unit = item.qty_in_base_unit
                sales_invoice_item.rate_in_base_unit = item.rate_in_base_unit
                sales_invoice_item.conversion_factor = item.conversion_factor
                sales_invoice_item.rate_includes_tax = item.rate_includes_tax
                sales_invoice_item.rate_excluded_tax = item.rate_excluded_tax
                sales_invoice_item.gross_amount = item.gross_amount
                sales_invoice_item.tax_excluded = item.tax_excluded
                sales_invoice_item.tax = item.tax
                sales_invoice_item.tax_rate = item.tax_rate
                sales_invoice_item.tax_amount = item.tax_amount
                sales_invoice_item.discount_percentage = item.discount_percentage
                sales_invoice_item.discount_amount = item.discount_amount
                sales_invoice_item.net_amount = item.net_amount
                sales_invoice_item.unit_conversion_details = item.unit_conversion_details
                sales_invoice_item.idx = idx

                sales_invoice.append('items', sales_invoice_item)
                #  target_items.append(target_item)

                sales_invoice.save()

            frappe.msgprint("Sales Invoice for the Tab Sales updated successfully.", alert=True)

        else:
            tabSalesDocName =  self.name
            sales_invoice = self.__dict__
            sales_invoice['doctype'] = 'Sales Invoice'
            sales_invoice['name'] = sales_invoice_name
            sales_invoice['naming_series'] = ""
            sales_invoice['posting_date'] = self.posting_date
            sales_invoice['posting_time'] = self.posting_time
            sales_invoice['tab_sales'] =tabSalesDocName
            # Change the document status to draft to avoid error while submitting child table
            sales_invoice['docstatus'] = 0
            for item in sales_invoice['items']:
                item.doctype = "Sales Invoice Item"
                # item.delivery_note_item_reference_no = item.name
                item._meta = ""

            sales_invoice_doc = frappe.get_doc(
                sales_invoice).insert(ignore_permissions=True)

            frappe.db.commit()

            si =  frappe.get_doc('Tab Sales',tabSalesDocName)

            si.sales_invoice_no_ref = sales_invoice_doc.name

            si.save()

        frappe.msgprint("Sales Invoice created successfully, in draft mode.", alert =1)

    # def cancel_sales_invoice(self):

    #     sales_invoice = frappe.get_doc('Sales Invoice', {'tab_sales':self.name})
    #     #print("tab_sales=>sales_invoice")
    #     #print(sales_invoice)
    #     sales_invoice.cancel()

@frappe.whitelist()
def get_user_warehouse():
    user = frappe.session.user
    user_warehouse = frappe.db.get_value('User Warehouse', {'user': user}, 'warehouse')
    #print(user_warehouse)
    return user_warehouse
