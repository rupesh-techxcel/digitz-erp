# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils import now
from frappe.model.document import Document
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_item_stock_balance
from frappe.www.printview import get_html_and_style
from digitz_erp.utils import *
from frappe.model.mapper import *
from digitz_erp.api.item_price_api import update_item_price
from digitz_erp.api.settings_api import get_default_currency
from datetime import datetime,timedelta
from digitz_erp.api.document_posting_status_api import init_document_posting_status, update_posting_status
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type
from digitz_erp.api.bank_reconciliation_api import create_bank_reconciliation, cancel_bank_reconciliation
from frappe.utils import money_in_words

class SalesInvoice(Document):

    def Voucher_In_The_Same_Time(self):
        possible_invalid= frappe.db.count('Sales Invoice', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time]})
        return possible_invalid

    def Set_Posting_Time_To_Next_Second(self):
        datetime_object = datetime.strptime(str(self.posting_time), '%H:%M:%S')

        # Add one second to the datetime object
        new_datetime = datetime_object + timedelta(seconds=1)

        # Extract the new time as a string
        self.posting_time = new_datetime.strftime('%H:%M:%S')

    def before_validate(self):

        if(self.Voucher_In_The_Same_Time()):

                self.Set_Posting_Time_To_Next_Second()

                if(self.Voucher_In_The_Same_Time()):
                    self.Set_Posting_Time_To_Next_Second()

                    if(self.Voucher_In_The_Same_Time()):
                        self.Set_Posting_Time_To_Next_Second()

                        if(self.Voucher_In_The_Same_Time()):
                            frappe.throw("Voucher with same time already exists.")

        # Fix for paid_amount copies while duplicating the document
        if self.is_new():
            self.paid_amount = 0

        if self.credit_sale == 0:
            self.paid_amount = self.rounded_total
            self.payment_status = "Cheque" if self.payment_mode == "Bank" else self.payment_mode
        else:
            self.payment_status = "Credit"
            self.payment_mode = ""
            self.payment_account = ""
            self.meta.get_field("payment_mode").hidden = 1
            self.meta.get_field("payment_account").hidden = 1
            # For submitted invoice only paid_amount is filling up with allocation.
            # So its safe to make paid_amount 0 to avoid the issue below
            # Issue - First save the invoie not as credit sale, it will fill up the paid_amount
            # equal to rounded_total. Make it as credit sale in the draft mode and then save.
            # In this case its required to make the paid_amount zero
            self.paid_amount = 0
        self.in_words = money_in_words(self.rounded_total,"AED")

    def validate(self):
        self.validate_item()

    def on_update(self):
        self.update_item_prices()

    def on_submit(self):

        init_document_posting_status(self.doctype, self.name)

        turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

        if(frappe.session.user == "Administrator" and turn_off_background_job):
            self.do_postings_on_submit()
        else:
            # frappe.enqueue(self.do_postings_on_submit, queue="long")
            # frappe.msgprint("The relevant postings for this document are happening in the background. Changes may take a few seconds to reflect.", alert=1)
            self.do_postings_on_submit()

        if(self.auto_generate_delivery_note):
            print("submitting DO from sales_invoice")
            self.submit_delivery_note()

    def do_postings_on_submit(self):

        cost_of_goods_sold = 0

        if self.tab_sales :
            cost_of_goods_sold = self.deduct_stock_for_tab_sales()

        print("cost_of_goods_sold")
        print(cost_of_goods_sold)

        self.insert_gl_records(cost_of_goods_sold=cost_of_goods_sold)
        self.insert_payment_postings()
        create_bank_reconciliation("Sales Invoice", self.name)

        update_accounts_for_doc_type('Sales Invoice',self.name)

        update_posting_status(self.doctype, self.name, 'posting_status','Completed')

    def update_item_prices(self):

        if(self.update_rates_in_price_list):
            currency = get_default_currency()
            print(self.items)
            for docitem in self.items:
                print("docitem to update price")
                print(docitem)
                item = docitem.item
                rate = docitem.rate_in_base_unit
                print("update_item_price arguments")
                print(item)
                print(self.price_list)
                print(currency)
                print(rate)
                print(self.posting_date)

                update_item_price(item, self.price_list,currency,rate, self.posting_date)

    def validate_item(self):

        posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))

        default_company = frappe.db.get_single_value("Global Settings",'default_company')

        company_info = frappe.get_value("Company",default_company,['allow_negative_stock'], as_dict = True)

        allow_negative_stock = company_info.allow_negative_stock

        if not allow_negative_stock:
            allow_negative_stock = False

        for docitem in self.items:

            print(docitem.item)

            # previous_stocks = frappe.db.get_value('Stock Ledger', {'item':docitem.item,'warehouse': docitem.warehouse , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],order_by='posting_date desc', as_dict=True)

            previous_stock_balance = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
            , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
            order_by='posting_date desc', as_dict=True)

            if(not previous_stock_balance and  allow_negative_stock==False):
                frappe.throw("No stock exists for" + docitem.item  + " from sales invoice")

            if(allow_negative_stock== False and previous_stock_balance.balance_qty< docitem.qty_in_base_unit):
                frappe.throw("Sufficiant qty does not exists for the item " + docitem.item + " required Qty= " + str(docitem.qty_in_base_unit) +
                " " + docitem.base_unit + " and available Qty=" + str(previous_stock_balance.balance_qty) + " " + docitem.base_unit )

    def on_cancel(self):
        cancel_bank_reconciliation("Sales Invoice", self.name)
        turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

        if(frappe.session.user == "Administrator" and turn_off_background_job):
            self.cancel_sales_invoice()
        else:
            # frappe.enqueue(self.cancel_sales_invoice, queue="long")
            self.cancel_sales_invoice()

    def cancel_sales_invoice(self):

        if self.auto_save_delivery_note:

            self.cancel_delivery_note_for_sales_invoice()

        # When correspdonding tab_sales cancelled, it hits here.
        if self.tab_sales:
            self.cancel_stock_postings_for_tab_sales()

        delete_gl_postings_for_cancel_doc_type('Sales Invoice',self.name)

        # frappe.db.delete("GL Posting",
        #                  {"Voucher_type": "Sales Invoice",
        #                   "voucher_no": self.name
        #                   })

    def cancel_stock_postings_for_tab_sales(self):

         # Insert record to 'Stock Recalculate Voucher' doc
        stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
        stock_recalc_voucher.voucher = 'Sales Invoice'
        stock_recalc_voucher.voucher_no = self.name
        stock_recalc_voucher.voucher_date = self.posting_date
        stock_recalc_voucher.voucher_time = self.posting_time
        stock_recalc_voucher.status = 'Not Started'
        stock_recalc_voucher.source_action = "Cancel"

        posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))

        more_records = 0

        # Iterate on each item from the cancelling sales invoice
        for docitem in self.items:
            more_records_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
                'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})

            more_records = more_records + more_records_for_item

            previous_stock_ledger_name = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
                        , 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)

            # If any items in the collection has more records
            if(more_records_for_item>0):

                # stock_ledger_items = frappe.get_list('Stock Ledger',{'item':docitem.item,
                # 'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]}, ['name','qty_in','qty_out','voucher','balance_qty','voucher_no'],order_by='posting_date')

                # if(stock_ledger_items):

                #     qty_cancelled = docitem.qty_in_base_unit
                    # Loop to verify the sufficiant quantity
                    # for sl in stock_ledger_items:
                    #     # On each line if outgoing qty + balance_qty (qty before outgonig) is more than the cancelling qty
                    #     if(sl.qty_out>0 and qty_cancelled> sl.qty_out+ sl.balance_qty):
                    #         frappe.throw("Cancelling the purchase is prevented due to sufficiant quantity not available for " + docitem.item +
                    #     " to fulfil the voucher " + sl.voucher_no)

                if(previous_stock_ledger_name):
                    stock_recalc_voucher.append('records',{'item': docitem.item,
                                                            'warehouse': docitem.warehouse,
                                                            'base_stock_ledger': previous_stock_ledger_name
                                                            })
                else:
                    stock_recalc_voucher.append('records',{'item': docitem.item,
                                                            'warehouse': docitem.warehouse,
                                                            'base_stock_ledger': "No Previous Ledger"
                                                            })

            else:

                balance_qty =0
                balance_value =0
                valuation_rate  = 0

                if(previous_stock_ledger_name):
                    previous_stock_ledger = frappe.get_doc('Stock Ledger',previous_stock_ledger_name)
                    balance_qty = previous_stock_ledger.balance_qty
                    balance_value = previous_stock_ledger.balance_value
                    valuation_rate = previous_stock_ledger.valuation_rate


                if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
                    frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse} )

                unit = frappe.get_value("Item", docitem.item,['base_unit'])

                new_stock_balance = frappe.new_doc('Stock Balance')
                new_stock_balance.item = docitem.item
                new_stock_balance.item_name = docitem.item_name
                new_stock_balance.unit = unit
                new_stock_balance.warehouse = docitem.warehouse
                new_stock_balance.stock_qty = balance_qty
                new_stock_balance.stock_value = balance_value
                new_stock_balance.valuation_rate = valuation_rate

                new_stock_balance.insert()

                # stock_balance_for_item = frappe.get_doc('Stock Balance',stock_balance)
                # # Add qty because of balance increasing due to cancellation of delivery note
                # stock_balance_for_item.stock_qty = balance_qty
                # stock_balance_for_item.stock_value = balance_value
                # stock_balance_for_item.valuation_rate = valuation_rate
                # stock_balance_for_item.save()

                update_item_stock_balance(docitem.item)

        # posting_status_doc = frappe.get_doc("Document Posting Status",{'document_type':'Purchase Invoice','document_name':self.name})
        # posting_status_doc.stock_posted_on_cancel_time = datetime.now()
        # posting_status_doc.save()

        update_posting_status(self.doctype, self.name, 'stock_posted_on_cancel_time', None)

        if(more_records>0):
            # posting_status_doc = frappe.get_doc("Document Posting Status",{'document_type':'Purchase Invoice','document_name':self.name})
            # posting_status_doc.stock_recalc_required_on_cancel = True
            # posting_status_doc.save()

            update_posting_status(self.doctype, self.name, 'stock_recalc_required_on_cancel', True)

            stock_recalc_voucher.insert()
            recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)

            # posting_status_doc = frappe.get_doc("Document Posting Status",{'document_type':'Purchase Invoice','document_name':self.name})
            # posting_status_doc.stock_recalc_on_cancel_time = datetime.now()
            # posting_status_doc.save()
            update_posting_status(self.doctype, self.name, 'stock_recalc_on_cancel_time', None)

        frappe.db.delete("Stock Ledger",
                {"voucher": "Sales Invoice",
                    "voucher_no":self.name
                })

        update_posting_status(self.doctype, self.name, 'posting_status', 'Completed')

    def insert_gl_records(self, cost_of_goods_sold):

        print("From insert gl records")

        default_company = frappe.db.get_single_value(
            "Global Settings", "default_company")

        default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                         'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)

        idx = 1

        # Trade Receivable - Debit
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Sales Invoice"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.default_receivable_account
        gl_doc.debit_amount = self.rounded_total
        gl_doc.party_type = "Customer"
        gl_doc.party = self.customer
        gl_doc.against_account = default_accounts.default_income_account
        gl_doc.insert()
        idx +=1

        # Income account - Credit
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Sales Invoice"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.default_income_account
        gl_doc.credit_amount = self.net_total - self.tax_total
        gl_doc.against_account = default_accounts.default_receivable_account
        gl_doc.insert()
        idx +=1


        if self.tax_total >0:

            # Tax - Credit

            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Sales Invoice"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = default_accounts.tax_account
            gl_doc.credit_amount = self.tax_total
            gl_doc.against_account = default_accounts.default_receivable_account
            gl_doc.insert()
            idx +=1

        # Round Off

        if self.round_off != 0.00:
            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Sales Invoice"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = default_accounts.round_off_account

            if self.rounded_total > self.net_total:
                gl_doc.credit_amount = abs(self.round_off)
            else:
                gl_doc.debit_amount = abs(self.round_off)

            gl_doc.insert()
            idx +=1

        if self.tab_sales:

            default_company = frappe.db.get_single_value("Global Settings", "default_company")

            default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                         'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)



            # Cost Of Goods Sold
            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Sales Invoice"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = default_accounts.cost_of_goods_sold_account
            gl_doc.debit_amount = cost_of_goods_sold
            gl_doc.against_account = default_accounts.default_inventory_account
            gl_doc.insert()
            idx +=1

            # Inventory account Eg: Stock In Hand
            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Sales Invoice"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = default_accounts.default_inventory_account
            gl_doc.credit_amount = cost_of_goods_sold
            gl_doc.against_account = default_accounts.cost_of_goods_sold_account
            gl_doc.insert()
            idx +=1

        update_posting_status(self.doctype,self.name, 'gl_posted_time',None)

    def insert_payment_postings(self):

        if self.credit_sale == 0:

            gl_count = frappe.db.count(
                'GL Posting', {'voucher_type': 'Sales Invoice', 'voucher_no': self.name})

            default_company = frappe.db.get_single_value(
                "Global Settings", "default_company")

            default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                             'stock_received_but_not_billed', 'round_off_account', 'tax_account'], as_dict=1)

            payment_mode = frappe.get_value(
                "Payment Mode", self.payment_mode, ['account'], as_dict=1)

            idx = gl_count + 1

            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Sales Invoice"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = default_accounts.default_receivable_account
            gl_doc.credit_amount = self.rounded_total
            gl_doc.party_type = "Customer"
            gl_doc.party = self.customer
            gl_doc.against_account = payment_mode.account
            gl_doc.insert()

            idx = idx + 1

            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Sales Invoice"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = payment_mode.account
            gl_doc.debit_amount = self.rounded_total
            gl_doc.against_account = default_accounts.default_receivable_account
            gl_doc.insert()

            update_posting_status(self.doctype,self.name, 'payment_posted_time',None)

    @frappe.whitelist()
    def submit_delivery_note(self):

        print("from submit delivery note")
        if self.docstatus == 1:
            print("logic_test-102")
            if self.auto_save_delivery_note:
                print("logic_test-103")
                result = frappe.db.sql("""SELECT * FROM `tabSales Invoice Delivery Notes` WHERE `parent` = %s""", (self.name,), as_dict=True)
                print("result")
                print(result)
                if result:
                    si_do = frappe.get_doc('Sales Invoice Delivery Notes', result[0].name)

                    print("so_do")
                    print(si_do)
                    do_no = si_do.delivery_note
                    do = frappe.get_doc('Delivery Note',do_no)
                    do.submit()
                    frappe.msgprint("A Delivery Note corresponding to the sales invoice is also submitted.", indicator="green", alert=True)
                return
        else:
            print("logic_test-101")

    @frappe.whitelist()
    def auto_generate_delivery_note(self):

        if self.docstatus == 1:
            # Submission happening in the submit_delivery_note method
            return

        delivery_note_name = ""

        doNo = ""

        si_name = self.name

        print("si_name")
        print(si_name)

        # Before delete the existing Delivery Note to insert it again, remove the link in the Sales Invoice
        # to avoid the reference error

        # si = frappe.get_doc('Sales Invoice',si_name)
        # Remove Reference first to avoid reference error when trying to delete before recreating
        # si.delivery_note =""
        # si.save()

        do_exists = False

        if self.auto_save_delivery_note:

            if frappe.db.exists('Sales Invoice Delivery Notes', {'parent': self.name}):
                do_exists = True

                delivery_note_name =  frappe.db.get_value('Sales Invoice Delivery Notes',{'parent':self.name},['delivery_note'] )

                # Remove the reference first before deleting the actual document
                # frappe.db.delete('Sales Invoice Delivery Notes',{'parent':self.name})
                delivery_note_doc = frappe.get_doc('Delivery Note', delivery_note_name)
                doNo = delivery_note_doc.name
                # delivery_note_doc.delete()
                # print("delivery note deleted")

                delivery_note_doc.customer = self.customer
                delivery_note_doc.customer_name = self.customer_name
                delivery_note_doc.customer_display_name = self.customer_display_name
                delivery_note_doc.customer_address = self.customer_address
                delivery_note_doc.reference_no = self.reference_no
                delivery_note_doc.posting_date = self.posting_date
                delivery_note_doc.posting_time = self.posting_time
                delivery_note_doc.ship_to_location = self.ship_to_location
                delivery_note_doc.salesman = self.salesman
                delivery_note_doc.salesman_code = self.salesman_code
                delivery_note_doc.tax_id = self.tax_id
                delivery_note_doc.lpo_no = self.lpo_no
                delivery_note_doc.lpo_date = self.lpo_date
                delivery_note_doc.price_list = self.price_list
                delivery_note_doc.rate_includes_tax = self.rate_includes_tax
                delivery_note_doc.warehouse = self.warehouse
                delivery_note_doc.credit_sale = self.credit_sale
                delivery_note_doc.credit_days = self.credit_days
                delivery_note_doc.payment_terms = self.payment_terms
                delivery_note_doc.payment_mode = self.payment_mode
                delivery_note_doc.payment_account = self.payment_account
                delivery_note_doc.remarks = self.remarks
                delivery_note_doc.gross_total = self.gross_total
                delivery_note_doc.total_discount_in_line_items = self.total_discount_in_line_items
                delivery_note_doc.tax_total = self.tax_total
                delivery_note_doc.net_total = self.net_total
                delivery_note_doc.round_off = self.round_off
                delivery_note_doc.rounded_total = self.rounded_total
                delivery_note_doc.terms = self.terms
                delivery_note_doc.terms_and_conditions = self.terms_and_conditions
                delivery_note_doc.auto_generated_from_delivery_note = True
                delivery_note_doc.address_line_1 = self.address_line_1
                delivery_note_doc.address_line_2 = self.address_line_2
                delivery_note_doc.area_name = self.area_name
                delivery_note_doc.country = self.country
                delivery_note_doc.quotation = self.quotation
                delivery_note_doc.sales_order = self.sales_order

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

                delivery_note_doc.save()
                # Remove existing child table values
                frappe.db.sql("DELETE FROM `tabDelivery Note Item` where parent=%s", delivery_note_name)

                # target_items = []

                idx = 0

                for item in self.items:
                    idx = idx + 1
                    delivery_note_item = frappe.new_doc("Delivery Note Item")
                    delivery_note_item.warehouse = item.warehouse
                    delivery_note_item.item = item.item
                    delivery_note_item.item_name = item.item_name
                    delivery_note_item.display_name = item.display_name
                    delivery_note_item.qty =item.qty
                    delivery_note_item.unit = item.unit
                    delivery_note_item.rate = item.rate
                    delivery_note_item.base_unit = item.base_unit
                    delivery_note_item.qty_in_base_unit = item.qty_in_base_unit
                    delivery_note_item.rate_in_base_unit = item.rate_in_base_unit
                    delivery_note_item.conversion_factor = item.conversion_factor
                    delivery_note_item.rate_includes_tax = item.rate_includes_tax
                    delivery_note_item.rate_excluded_tax = item.rate_excluded_tax
                    delivery_note_item.gross_amount = item.gross_amount
                    delivery_note_item.tax_excluded = item.tax_excluded
                    delivery_note_item.tax = item.tax
                    delivery_note_item.tax_rate = item.tax_rate
                    delivery_note_item.tax_amount = item.tax_amount
                    delivery_note_item.discount_percentage = item.discount_percentage
                    delivery_note_item.discount_amount = item.discount_amount
                    delivery_note_item.net_amount = item.net_amount
                    delivery_note_item.unit_conversion_details = item.unit_conversion_details
                    delivery_note_item.idx = idx

                    delivery_note_doc.append('items', delivery_note_item )
                    #  target_items.append(target_item)

                delivery_note_doc.save()

                frappe.msgprint("Delivery Note for the Sales Invoice updated successfully.", alert=True)

            else:

                if(self.amended_from):
                    frappe.msgprint("Corresponding Delivery cannot amend automatically. System generates a new delivery note instead.")

                print("create delivery note")

                delivery_note = self.__dict__
                delivery_note['doctype'] = 'Delivery Note'
                # delivery_note['against_sales_invoice'] = delivery_note['name']
                # delivery_note['name'] = delivery_note_name
                delivery_note['naming_series'] = ""
                delivery_note['posting_date'] = self.posting_date
                delivery_note['posting_time'] = self.posting_time
                delivery_note['amended_from'] = ""

                delivery_note['auto_generated_from_sales_invoice'] = 1

                for item in delivery_note['items']:
                    item.doctype = "Delivery Note Item"
                    item._meta = ""

                delivery_note_doc = frappe.get_doc(delivery_note).insert()
                frappe.db.commit()

                print("delivery note created")

                delivery_note_name = delivery_note_doc.name

                print("delivery note name")
                print(delivery_note_name)
                frappe.msgprint("A Delivery Note corresponding to the  Sales invoice created successfully", alert = True)


        # Rename the delivery note to the original dnoNo which is deleted
        # if(do_exists):
        #     frappe.rename_doc('Delivery Note', doNo.name, delivery_note_name)

        # do = frappe.get_doc('Delivery Note', delivery_note_name)
        si = frappe.get_doc('Sales Invoice',si_name)

        # if frappe.db.exists('Sales Invoice Delivery Notes', {'parent': self.name}):
        if(not do_exists):
            si.append('delivery_notes', {'delivery_note': delivery_note_name})

        si.save()

        print("si saved")

        # delivery_notes = frappe.db.get_all('Sales Invoice Delivery Notes', {'parent': ['=', si_name]},{'delivery_note'})
        delivery_notes = frappe.db.get_all('Sales Invoice Delivery Notes',
                                   filters={'parent': si_name},
                                   fields=['delivery_note'])


        print("delivery notes")
        print(delivery_notes)

        # It is likely that there will be only one delivery note for the sales invoice for this method.
        index = 0
        maxIndex = 3
        doNos = ""

        for delivery_note_saved in delivery_notes:
            do_created = frappe.get_doc('Delivery Note',delivery_note_saved.delivery_note )

            print(doNo)
            if(doNos == ""):
                doNos = do_created.name
            else:
                doNos = doNos + ", " + do_created.name

            index= index + 1
            if index == maxIndex:
                break

        si = frappe.get_doc('Sales Invoice',si_name)

        si.delivery_notes_to_print = doNos

        index = 0

        for item in si.items:
            item.delivery_note_item_reference_no = delivery_note_doc.items[index].name
            index = index + 1

        # Need to remove the next line to set auto_save_delivery_note
        si.auto_save_delivery_note = True
        si.save()

        print("From end of auto gen delivery note")

    def cancel_delivery_note_for_sales_invoice(self):
        print("cancel delivbery note for sales invoice")
        delivery_note = frappe.get_value("Sales Invoice Delivery Notes",{'parent': self.name}, ['delivery_note'])
        do = frappe.get_doc('Delivery Note',delivery_note)
        do.cancel()
        frappe.msgprint("Sales invoice and delivery note cancelled successfully", alert= True)

        # frappe.msgprint("Delivery Note cancelled")
    def deduct_stock_for_tab_sales(self):

        stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
        stock_recalc_voucher.voucher = 'Sales Invoice'
        stock_recalc_voucher.voucher_no = self.name
        stock_recalc_voucher.voucher_date = self.posting_date
        stock_recalc_voucher.voucher_time = self.posting_time
        stock_recalc_voucher.status = 'Not Started'
        stock_recalc_voucher.source_action = "Insert"

        print("from deduct_stock")

        cost_of_goods_sold = 0

        more_records = 0

        default_company = frappe.db.get_single_value("Global Settings", "default_company")
        company_info = frappe.get_value("Company",default_company,['allow_negative_stock'], as_dict = True)

        allow_negative_stock = company_info.allow_negative_stock

        if not allow_negative_stock:
            allow_negative_stock = False

        for docitem in self.items:

            posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))

     		# Check for more records after this date time exists. This is mainly for deciding whether stock balance needs to update
	    	# in this flow itself. If more records, exists stock balance will be udpated lateer
            more_records_count_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
				'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})

            more_records = more_records + more_records_count_for_item

            # required_qty = docitem.qty_in_base_unit

            # Check available qty
            previous_stock_balance = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
            , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
            order_by='posting_date desc', as_dict=True)

            print("previous stock balance")
            print(previous_stock_balance)

            # if(allow_negative_stock == False and not previous_stock_balance):
            #     frappe.throw("No stock exists for" + docitem.item )
            #     return

            # if(allow_negative_stock == False and previous_stock_balance and previous_stock_balance.balance_qty < required_qty ):
            #     frappe.throw("Sufficiant qty does not exists for the item " + docitem.item + " Required Qty= " + str(required_qty) + " " +
            #         docitem.base_unit + "and available Qty= " + str(previous_stock_balance.balance_qty) + " " + docitem.base_unit)
            #     return

            previous_stock_balance_value = 0

            if previous_stock_balance:

                print("previous_stock_balance.valuation_rate")
                print(previous_stock_balance.valuation_rate)

                new_balance_qty = previous_stock_balance.balance_qty - docitem.qty_in_base_unit
                valuation_rate = previous_stock_balance.valuation_rate
                previous_stock_balance_value = previous_stock_balance.balance_value
            else:
                print("no previous stock balance")
                new_balance_qty = 0 - docitem.qty_in_base_unit
                valuation_rate = frappe.get_value("Item", docitem.item, ['standard_buying_price'])

            print("docitem.qty_in_base_unit")
            print(docitem.qty_in_base_unit)
            print("valuation_rate")
            print(valuation_rate)

            new_balance_value = previous_stock_balance_value - (docitem.qty_in_base_unit * valuation_rate)
            cost_of_goods_sold = cost_of_goods_sold + (docitem.qty_in_base_unit * valuation_rate)

            if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
                frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse})

            change_in_stock_value = new_balance_value - previous_stock_balance_value
            print("change in stock value")
            print(change_in_stock_value)

            print("new_balanmce_value")
            print(new_balance_value)

            print("previous_stock_balance_value")
            print(previous_stock_balance_value)
            default_company = frappe.db.get_single_value("Global Settings", "default_company")
            maintain_stock = frappe.db.get_value("Company", default_company,['maintain_stock'])
            print("Maintain Stock :",maintain_stock)
            if(maintain_stock == 1):
                new_stock_ledger = frappe.new_doc("Stock Ledger")
                new_stock_ledger.item = docitem.item
                new_stock_ledger.item_name = docitem.item_name
                new_stock_ledger.warehouse = docitem.warehouse
                new_stock_ledger.posting_date = posting_date_time
                new_stock_ledger.qty_out = docitem.qty_in_base_unit
                new_stock_ledger.outgoing_rate = docitem.rate_in_base_unit
                new_stock_ledger.unit = docitem.base_unit
                new_stock_ledger.valuation_rate = valuation_rate
                new_stock_ledger.balance_qty = new_balance_qty
                new_stock_ledger.balance_value = new_balance_value
                new_stock_ledger.change_in_stock_value = change_in_stock_value
                new_stock_ledger.voucher = "Sales Invoice"
                new_stock_ledger.voucher_no = self.name
                new_stock_ledger.source = "Sales Invoice Item"
                new_stock_ledger.source_document_id = docitem.name
                new_stock_ledger.insert()

                # If no more records for the item, update balances. otherwise it updates in the flow
                if more_records_count_for_item==0:
                    if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
                        frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse} )

                    unit = frappe.get_value("Item", docitem.item,['base_unit'])

                    new_stock_balance = frappe.new_doc('Stock Balance')
                    new_stock_balance.item = docitem.item
                    new_stock_balance.item_name = docitem.item_name
                    new_stock_balance.unit = unit
                    new_stock_balance.warehouse = docitem.warehouse
                    new_stock_balance.stock_qty = new_balance_qty
                    new_stock_balance.stock_value = new_balance_value
                    new_stock_balance.valuation_rate = valuation_rate

                    new_stock_balance.insert()

                    # item_name = frappe.get_value("Item", docitem.item,['item_name'])
                    update_item_stock_balance(docitem.item)
                else:
                    stock_recalc_voucher.append('records',{'item': docitem.item,
                                                                'warehouse': docitem.warehouse,
                                                                'base_stock_ledger': new_stock_ledger.name
                                                                })
        update_posting_status(self.doctype,self.name,'stock_posted')
        if(more_records>0):
            update_posting_status(self.doctype,self.name,'stock_recalc_required', True)
            stock_recalc_voucher.insert()
            recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)
            update_posting_status(self.doctype,self.name,'stock_recalc_time')

        return cost_of_goods_sold

@frappe.whitelist()
def get_default_payment_mode():
    default_payment_mode = frappe.db.get_value('Company', filters={'name'},fieldname='default_payment_mode_for_sales')
    print(default_payment_mode)
    return default_payment_mode
