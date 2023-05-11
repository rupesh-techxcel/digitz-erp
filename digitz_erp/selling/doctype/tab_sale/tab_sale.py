# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils import now
from frappe.model.document import Document


class TabSale(Document):
    """if need of autoupdate of delivery note in case of any update in Tab Sale then uncomment the before_save controller"""
    @frappe.whitelist()
    def generate_sale_invoice(self):
        sales_invoice_name = ""
        deliveryNoteName = self.name
        sales_invoice = self.__dict__
        sales_invoice['doctype'] = 'Sales Invoice'
        sales_invoice['name'] = sales_invoice_name
        sales_invoice['naming_series'] = ""
        sales_invoice['posting_date'] = self.posting_date
        sales_invoice['posting_time'] = self.posting_time
        sales_invoice['delivery_note'] = deliveryNoteName
        sales_invoice['docstatus'] = 0
        for item in sales_invoice['items']:
            item.doctype = "Sales Invoice Item"
            item.delivery_note_item_reference_no = item.name
            item._meta = ""

        sales_invoice_doc = frappe.get_doc(
            sales_invoice).insert(ignore_permissions=True)

        frappe.db.commit()

        print(sales_invoice_doc.name)

        si = frappe.get_doc('Sales Invoice', sales_invoice_doc.name)

        # Add reference link to the 'Sales Invoice Delivery NOtes' child doctype

        si.append('delivery_notes', {'delivery_note': deliveryNoteName})

        # si.docstatus = 1

        si.save()

        frappe.msgprint(
            "Sales Invoice created successfully, in draft mode.")

# frappe.msgprint("Delivery Note cancelled")

    # def before_save(self):
    # for i in self.items:
    #     if i.delivery_note:
    #         frappe.db.set_value(
    #             'Delivery Note', i.delivery_note, 'against_sales_invoice', self.name)
    #         frappe.db.commit()

    # if not self.is_new() and self.auto_save_delivery_note:

    # if self.auto_save_delivery_note:
    #     self.auto_generate_sales_invoice()
    # frappe.msgprint("before save event")
    # print("before save")

    def before_submit(self):

        # When duplicating the voucher user may not remember to change the date and time. So do not allow to save the voucher to be
        # posted on the same time with any of the existing vouchers. This also avoid invalid selection to calculate moving average value

        # Store the current document name to the variable to use it after delete the variable

        # possible_invalid = frappe.db.count('Tab Sale', {'posting_date': [
        #                                    '=', self.posting_date], 'posting_time': ['=', self.posting_time], 'docstatus': ['=', 1]})

        # if (possible_invalid > 0):
        #     frappe.throw(
        #         "There is another Tab Sale exist with the same date and time. Please correct the date and time.")

        # Checking needed whether Delivery Note is creating automatically, if yes, then only stock availability need to check
        # otherwise it could be done with in the delivery note itself.

        self.validate_item()

        self.insert_gl_records()
        self.insert_payment_postings()
        if (self.auto_generate_sales_invoice):
            self.submit_delivery_note()

    def validate_item(self):

        posting_date_time = get_datetime(
            str(self.posting_date) + " " + str(self.posting_time))

        default_company = frappe.db.get_single_value(
            "Global Settings", 'default_company')

        company_info = frappe.get_value("Company", default_company, [
                                        'allow_negative_stock'], as_dict=True)

        allow_negative_stock = company_info.allow_negative_stock

        if not allow_negative_stock:
            allow_negative_stock = False

        for docitem in self.items:

            print(docitem.item)

            # previous_stocks = frappe.db.get_value('Stock Ledger', {'item':docitem.item,'warehouse': docitem.warehouse , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],order_by='posting_date desc', as_dict=True)

            previous_stock_balance = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse': ['=', docitem.warehouse], 'posting_date': ['<', posting_date_time]}, ['name', 'balance_qty', 'balance_value', 'valuation_rate'],
                                                         order_by='posting_date desc', as_dict=True)

            if (not previous_stock_balance and allow_negative_stock == False):
                frappe.throw("No stock exists for" +
                             docitem.item + " from Tab Sale")

            if (allow_negative_stock == False and previous_stock_balance.balance_qty < docitem.qty_in_base_unit):
                frappe.throw("Sufficiant qty does not exists for the item " + docitem.item + " required Qty= " + str(docitem.qty_in_base_unit) +
                             " " + docitem.base_unit + " and available Qty=" + str(previous_stock_balance.balance_qty) + " " + docitem.base_unit)

    def on_cancel(self):

        if self.auto_save_delivery_note:
            # delivery_note_name = frappe.get_value("Tab Sale Delivery Notes",{'parent': self.name}, ['delivery_note'])
            # delivery_note = frappe.get_doc('Delivery Note', delivery_note_name)

            self.cancel_delivery_note_for_sales_invoice()

        frappe.db.delete("GL Posting",
                         {"Voucher_type": "Tab Sale",
                          "voucher_no": self.name
                          })

    # def before_cancel(self):

    # def on_trash(self):
        # if self.auto_save_delivery_note:
        # delivery_note = frappe.get_value("Tab Sale Delivery Notes",{'parent': self.name}, ['delivery_note'])
        # frappe.delete_doc('Delivery Note', delivery_note)

    # def after_delete(self):

        # print("after delete SI event")

        # if self.auto_save_delivery_note:
        #     delivery_note = frappe.get_value("Tab Sale Delivery Notes",{'parent': self.doc_name}, ['delivery_note'])
        #     print(delivery_note)
        #     frappe.delete_doc('Delivery Note', delivery_note)

    # def after_save():
    #     frappe.msgprint("after save")
    #     print("after save")

    def insert_gl_records(self):

        print("From insert gl records")

        default_company = frappe.db.get_single_value(
            "Global Settings", "default_company")

        default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                         'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)

        idx = 1

        # Trade Receivable - Debit
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Tab Sale"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.default_receivable_account
        gl_doc.debit_amount = self.rounded_total
        gl_doc.party_type = "Customer"
        gl_doc.party = self.customer
        gl_doc.aginst_account = default_accounts.default_income_account
        gl_doc.insert()

        # Income account - Credot
        idx = 2
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Tab Sale"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.default_income_account
        gl_doc.credit_amount = self.net_total - self.tax_total
        gl_doc.aginst_account = default_accounts.default_receivable_account
        gl_doc.insert()

        # Tax - Credit
        idx = 3
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Tab Sale"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.tax_account
        gl_doc.credit_amount = self.tax_total
        gl_doc.aginst_account = default_accounts.default_receivable_account
        gl_doc.insert()

        # Round Off

        if self.round_off != 0.00:
            idx = 4
            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Tab Sale"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = default_accounts.round_off_account

            if self.rounded_total > self.net_total:
                gl_doc.credit_amount = self.round_off
            else:
                gl_doc.debit_amount = self.round_off

            gl_doc.insert()

    def insert_payment_postings(self):

        if self.credit_sale == 0:

            gl_count = frappe.db.count(
                'GL Posting', {'voucher_type': 'Tab Sale', 'voucher_no': self.name})

            default_company = frappe.db.get_single_value(
                "Global Settings", "default_company")

            default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                             'stock_received_but_not_billed', 'round_off_account', 'tax_account'], as_dict=1)

            payment_mode = frappe.get_value(
                "Payment Mode", self.payment_mode, ['account'], as_dict=1)

            idx = gl_count + 1

            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Tab Sale"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = default_accounts.default_receivable_account
            gl_doc.credit_amount = self.rounded_total
            gl_doc.party_type = "Customer"
            gl_doc.party = self.customer
            gl_doc.aginst_account = payment_mode.account
            gl_doc.insert()

            idx = idx + 1

            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Tab Sale"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = payment_mode.account
            gl_doc.debit_amount = self.rounded_total
            gl_doc.aginst_account = default_accounts.default_receivable_account
            gl_doc.insert()
        else:
            pass
