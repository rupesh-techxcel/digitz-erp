# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils import now
from frappe.model.document import Document
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_stock_balance_in_item
from frappe.www.printview import get_html_and_style
from digitz_erp.utils import *
from frappe.model.mapper import *
from digitz_erp.api.item_price_api import update_item_price,update_customer_item_price
from digitz_erp.api.settings_api import get_default_currency, get_gl_narration
from datetime import datetime,timedelta
from digitz_erp.api.document_posting_status_api import init_document_posting_status, update_posting_status
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type
from digitz_erp.api.bank_reconciliation_api import create_bank_reconciliation, cancel_bank_reconciliation
from frappe.utils import money_in_words
from digitz_erp.api.sales_order_api import check_and_update_sales_order_status,update_sales_order_quantities_on_update
from digitz_erp.api.settings_api import add_seconds_to_time
from frappe import _

class SalesInvoice(Document):

    def Voucher_In_The_Same_Time(self):
        possible_invalid= frappe.db.count('Sales Invoice', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time]})
        return possible_invalid
        
    def Set_Posting_Time_To_Next_Second(self):
        # Add 12 seconds to self.posting_time and update it
        self.posting_time = add_seconds_to_time(str(self.posting_time), seconds=12)

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

        if self.tab_sales:
            self.update_stock = True
            self.created_from_tab_sale = True

        self.update_delivery_note_references()
        
        if not frappe.db.exists("Customer Delivery Location", self.ship_to_location):
            self.ship_to_location = ""
        
        for item in self.items:
            # Format the values to two decimal places and assign them to the print fields
            item.rate_print = "{:.2f}".format(item.rate)  
            item.amount_print = "{:.2f}".format(item.gross_amount)
            item.tax_amount_print = "{:.2f}".format(item.tax_amount)
            item.total_amount_print = "{:.2f}".format(item.net_amount)  
        
        # Ship to location is a child table reference for customer and cannot have acess 
        # from Sales Invoice. So adding a duplicate field for printing purpose
        self.location_to_print = self.ship_to_location
        
        self.update_advance_received_with_sales_order()
        
    def validate_for_sales_order(self):
        # Ensure the Sales Invoice is linked to a Sales Order
        if not (self.sales_order) or self.for_advance_payment or self.for_retention_recovery :
            return

        # Fetch the Sales Order document
        sales_order_doc = frappe.get_doc("Sales Order", self.sales_order)

        # Get the list of allowed item codes from the Sales Order
        allowed_items = [item.item for item in sales_order_doc.items]

        # Validate each item in the Sales Invoice
        for item in self.items:
            if item.item not in allowed_items:
                frappe.throw(
                    _("Item '{0}' is not part of the Sales Order '{1}'. If this is an for advance payment check the 'for advnce payment' option to proceed further.")
                    .format(item.item, self.sales_order)
                )
    def validate_for_advance_for_progress_entries(self):
        
        if self.for_advance_payment:
            progress_entry_exists = frappe.db.exists("Progress Entry", {"project": self.project})
            if progress_entry_exists:
                frappe.throw(f"Project '{self.project}' already has progress entries. Advance amount will not be updated.")
                return 

    def validate_duplicate_advance_entry_for_project(self):
        existing_invoice = frappe.db.exists(
                        "Sales Invoice",
                        {
                            "project": self.project,
                            "for_advance_payment": 1,
                            "name": ["!=", self.name],  # Exclude the current document in case it's being updated
                            "docstatus": ["<", 2]  # Consider only Draft or Submitted documents
                        }
                        )
        if existing_invoice:
            frappe.throw(("An advance payment invoice already exists for the project '{0}'. Please review and update the existing invoice instead.").format(doc.project),
            title=("Duplicate Advance Payment"))

    def validate(self):
        self.validate_item()
        self.validate_for_sales_order()
        self.validate_for_advance_for_progress_entries()
        self.validate_duplicate_advance_entry_for_project()
        # self.validate_item_valuation_rates()
    
    def update_advance_received_with_sales_order(self):
        """
        Checks if the linked Sales Order of this Sales Invoice has an allocation
        in any Receipt Entry and updates the 'advance_received_with_sales_order' field.
        """
        # Ensure this Sales Invoice is linked to a Sales Order
        if not self.sales_order:
            return  # No linked Sales Order, nothing to check

        # Check if there is an allocation in Receipt Entry for this Sales Order
        allocation_exists = frappe.db.exists(
            "Receipt Entry Allocation",  # Doctype name
            {
                "reference_type": "Sales Order",
                "reference_name": self.sales_order
            }
        )

        # Update the 'advance_received_with_sales_order' field based on the allocation
        self.advance_received_with_sales_order = 1 if allocation_exists else 0


    def on_update(self):

        self.update_item_prices()

        if not self.tab_sales and not self.for_advance_payment:
            update_sales_order_quantities_on_update(self)
            check_and_update_sales_order_status(self.name, "Sales Invoice")

        self.update_customer_last_transaction_date()
        self.update_receipt_schedules()
        self.update_project_advance_amount()        
        
    def update_project_advance_amount(self,for_cancel=False):
        if self.for_advance_payment:
            frappe.db.set_value("Project", self.project, "advance_amount", self.gross_total if not for_cancel else 0)
            frappe.db.set_value("Project", self.project, "advance_percentage", self.advance_percentage if not for_cancel else 0)
            frappe.msgprint("Advance amount updated in the project", alert=1)

    def on_submit(self):

        init_document_posting_status(self.doctype, self.name)

        turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

        # if(frappe.session.user == "Administrator" and turn_off_background_job):
        #     self.do_postings_on_submit()
        # else:
            # frappe.enqueue(self.do_postings_on_submit, queue="long")
            # frappe.msgprint("The relevant postings for this document are happening in the background. Changes may take a few seconds to reflect.", alert=1)
        self.do_postings_on_submit()
        self.update_project_billed_amounts()
        

        # if(self.auto_generate_delivery_note):
        #     #print("submitting DO from sales_invoice")
        #     self.submit_delivery_note()

    def do_postings_on_submit(self):

        self.do_stock_posting()
        self.insert_gl_records()
        self.insert_payment_postings()
        create_bank_reconciliation("Sales Invoice", self.name)

        update_accounts_for_doc_type('Sales Invoice',self.name)
        self.update_customer_prices()

        update_posting_status(self.doctype, self.name, 'posting_status','Completed')
        self.update_customer_last_transaction_date()
        

    def update_customer_last_transaction_date(self):

        frappe.set_value('Customer',self.customer,{'last_transaction_date':self.posting_date})

    def update_delivery_note_references(self):

        delivery_note_item_reference_nos = [
            item.delivery_note_item_reference_no for item in self.items if item.delivery_note_item_reference_no
        ]

        # Avoid repeated database queries by fetching all parent delivery notes in one go
        if delivery_note_item_reference_nos:
            query = """
            SELECT DISTINCT parent
            FROM `tabDelivery Note Item`
            WHERE name IN (%s)
            """
            # Formatting query string for multiple items
            format_strings = ','.join(['%s'] * len(delivery_note_item_reference_nos))
            query = query % format_strings

            parent_delivery_notes = frappe.db.sql(query, tuple(delivery_note_item_reference_nos), as_dict=True)
            parent_delivery_notes = [dn['parent'] for dn in parent_delivery_notes if dn['parent']]
        else:
            parent_delivery_notes = []

        # Clear existing entries in the 'delivery_notes' child table
        self.set('delivery_notes', [])  # Assuming 'delivery_notes' is the correct child table field name

        # Append new entries to the 'delivery_notes' child table
        for delivery_note in parent_delivery_notes:
            self.append('delivery_notes', {  # Ensure the fieldname is correct as per your doctype structure
                'delivery_note': delivery_note
            })


    def update_item_prices(self):

        if(self.update_rates_in_price_list):
            currency = get_default_currency()
            
            for docitem in self.items:

                item = docitem.item
                rate = docitem.rate_in_base_unit

                update_item_price(item, self.price_list,currency,rate, self.posting_date)

    def update_customer_prices(self):#

        for docitem in self.items:
                item = docitem.item
                rate = docitem.rate_in_base_unit
                update_customer_item_price(item, self.customer,rate,self.posting_date)

    def validate_item(self):

        posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))

        default_company = frappe.db.get_single_value("Global Settings",'default_company')

        company_info = frappe.get_value("Company",default_company,['allow_negative_stock'], as_dict = True)

        allow_negative_stock = company_info.allow_negative_stock

        if not allow_negative_stock:
            allow_negative_stock = False

        for docitem in self.items:

            # previous_stocks = frappe.db.get_value('Stock Ledger', {'item':docitem.item,'warehouse': docitem.warehouse , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],order_by='posting_date desc', as_dict=True)

            previous_stock_balance = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
            , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
            order_by='posting_date desc', as_dict=True)

            if(not previous_stock_balance and  allow_negative_stock==False):
                frappe.throw("No stock exists for" + docitem.item  + " from sales invoice")

            if(allow_negative_stock== False and previous_stock_balance.balance_qty< docitem.qty_in_base_unit):
                frappe.throw("Sufficiant qty does not exists for the item " + docitem.item + " required Qty= " + str(docitem.qty_in_base_unit) +
                " " + docitem.base_unit + " and available Qty=" + str(previous_stock_balance.balance_qty) + " " + docitem.base_unit )

    def validate_item_valuation_rates(self):

        if not self.update_stock:
            return

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


    def on_cancel(self):
        cancel_bank_reconciliation("Sales Invoice", self.name)
        # frappe.enqueue(self.cancel_sales_invoice, queue="long")

        if not self.tab_sales:
            update_sales_order_quantities_on_update(self,forDeleteOrCancel=True)
            check_and_update_sales_order_status(self.name, "Sales Invoice")
        self.cancel_sales_invoice()
        self.update_project_advance_amount(for_cancel=True)
        self.update_project_billed_amounts(cancel=True)

    def on_trash(self):

        cancel_bank_reconciliation("Sales Invoice", self.name)

        if not self.tab_sales:
            update_sales_order_quantities_on_update(self,forDeleteOrCancel=True)
            check_and_update_sales_order_status(self.name, "Sales Invoice")
        
        self.update_project_advance_amount(for_cancel=True)


    def cancel_sales_invoice(self):

        # To serve the old records before the feature is disabled, keeping the cancel_delivery_note logic , for new reocrds its not applilcable. Means self.auto_save_delivery_note only false for new records
        if self.auto_save_delivery_note:

            self.cancel_delivery_note_for_sales_invoice()

        # When correspdonding tab_sales cancelled, it hits here.
        if self.tab_sales or self.update_stock:
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

                update_stock_balance_in_item(docitem.item)

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
        
    def get_narration(self):
        
        # Assign supplier, invoice_no, and remarks
        customer_name = self.customer_name		
        remarks = self.remarks if self.remarks else ""
        payment_mode = ""
        if self.credit_sale:
            payment_mode = "Credit"
        else:
            payment_mode = self.payment_mode
        
        # Get the gl_narration which might be empty
        gl_narration = get_gl_narration('Sales Invoice')  # This could return an empty string

        # Provide a default template if gl_narration is empty
        if not gl_narration:
            gl_narration = "Sales to {customer_name}"

        # Replace placeholders with actual values
        narration = gl_narration.format(payment_mode=payment_mode, customer_name=customer_name)

        # Append remarks if they are available
        if remarks:
            narration += f", {remarks}"

        return narration    

    def insert_gl_records(self):
        
        if self.for_retention_recovery:
            self.insert_gl_records_for_retention_recovery() 
            return
        
        if self.for_advance_payment:
            self.insert_gl_records_for_advance()
            return

        remarks = self.get_narration()

        default_company = frappe.db.get_single_value(
            "Global Settings", "default_company")

        default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                            'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account','retention_receivable_account'], as_dict=1)
        
        print("default_accounts")
        print(default_accounts)

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
        gl_doc.remarks = remarks
        gl_doc.project = self.project
        gl_doc.cost_center = self.cost_center
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
        gl_doc.remarks = remarks
        gl_doc.project = self.project
        gl_doc.cost_center = self.cost_center
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
            gl_doc.remarks = remarks
            gl_doc.project = self.project
            gl_doc.cost_center = self.cost_center
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
            
            gl_doc.remarks = remarks
            gl_doc.project = self.project
            gl_doc.cost_center = self.cost_center
            gl_doc.insert()
            idx +=1

        if self.tab_sales or self.update_stock:

            cost_of_goods_sold = self.get_cost_of_goods_sold()

            if(cost_of_goods_sold!=0):

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
                gl_doc.is_for_cogs = True
                gl_doc.remarks = remarks
                gl_doc.project = self.project
                gl_doc.cost_center = self.cost_center
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
                gl_doc.is_for_cogs = True
                gl_doc.remarks = remarks
                gl_doc.project = self.project
                gl_doc.cost_center = self.cost_center
                gl_doc.insert()
                idx +=1

        update_posting_status(self.doctype,self.name, 'gl_posted_time',None)
        
    def insert_gl_records_for_retention_recovery(self):
        
        remarks = self.get_narration()

        default_company = frappe.db.get_single_value(
            "Global Settings", "default_company")

        default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                            'default_income_account', 'cost_of_goods_sold_account', 
                                                                            'round_off_account', 'tax_account','retention_receivable_account','default_advance_billed_but_received_account'], as_dict=1)
        
        print("default_accounts")
        print(default_accounts)

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
        gl_doc.against_account = default_accounts.retention_receivable_account
        gl_doc.remarks = remarks
        gl_doc.project = self.project
        gl_doc.cost_center = self.cost_center
        gl_doc.insert()
        idx +=1

        # Retention Receivable Account - Credit
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Sales Invoice"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.retention_receivable_account
        gl_doc.credit_amount = self.net_total - self.tax_total
        gl_doc.against_account = default_accounts.default_receivable_account
        gl_doc.remarks = remarks
        gl_doc.project = self.project
        gl_doc.cost_center = self.cost_center
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
            gl_doc.remarks = remarks
            gl_doc.project = self.project
            gl_doc.cost_center = self.cost_center
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
            
            gl_doc.remarks = remarks
            gl_doc.project = self.project
            gl_doc.cost_center = self.cost_center
            gl_doc.insert()
            idx +=1

        update_posting_status(self.doctype,self.name, 'gl_posted_time',None)
    
    def insert_gl_records_for_advance(self):
        
        remarks = self.get_narration()

        default_company = frappe.db.get_single_value(
            "Global Settings", "default_company")

        default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                            'default_income_account', 'cost_of_goods_sold_account',
                                                                            'round_off_account', 'tax_account','retention_receivable_account',
                                                                            'project_advance_received_account','default_advance_billed_but_not_received_account'], as_dict=1)
        
        print("default_accounts")
        print(default_accounts)

        idx = 1

        # Trade Receivable - Debit
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Sales Invoice"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.default_advance_billed_but_not_received_account 
        gl_doc.debit_amount = self.rounded_total
        gl_doc.party_type = "Customer"
        gl_doc.party = self.customer
        gl_doc.against_account = default_accounts.project_advance_received_account
        gl_doc.remarks = remarks
        gl_doc.project = self.project
        gl_doc.cost_center = self.cost_center
        gl_doc.insert()
        idx +=1

        # Retention Receivable Account - Credit
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Sales Invoice"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.project_advance_received_account
        gl_doc.credit_amount = self.net_total - self.tax_total
        gl_doc.against_account = default_accounts.default_advance_billed_but_not_received_account
        gl_doc.remarks = remarks
        gl_doc.project = self.project
        gl_doc.cost_center = self.cost_center
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
            gl_doc.against_account = default_accounts.default_advance_billed_but_not_received_account
            gl_doc.remarks = remarks
            gl_doc.project = self.project
            gl_doc.cost_center = self.cost_center
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
            
            gl_doc.remarks = remarks
            gl_doc.project = self.project
            gl_doc.cost_center = self.cost_center
            gl_doc.insert()
            idx +=1

        update_posting_status(self.doctype,self.name, 'gl_posted_time',None)

    def insert_payment_postings(self):
        
        remarks = self.get_narration()

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
            gl_doc.account = default_accounts.default_receivable_account if not self.for_retention_recovery else default_accounts.retention_receivable_account
            gl_doc.credit_amount = self.rounded_total
            gl_doc.party_type = "Customer"
            gl_doc.party = self.customer
            gl_doc.against_account = payment_mode.account
            gl_doc.remarks = remarks
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
            gl_doc.against_account = default_accounts.default_receivable_account if not self.for_retention_recovery else default_accounts.retention_receivable_account
            gl_doc.remarks = remarks
            gl_doc.insert()

            update_posting_status(self.doctype,self.name, 'payment_posted_time',None)

    @frappe.whitelist()
    def submit_delivery_note(self):
        
        if self.docstatus == 1:
            
            if self.auto_save_delivery_note:
                
                result = frappe.db.sql("""SELECT * FROM `tabSales Invoice Delivery Notes` WHERE `parent` = %s""", (self.name,), as_dict=True)
                
                if result:
                    si_do = frappe.get_doc('Sales Invoice Delivery Notes', result[0].name)

                    do_no = si_do.delivery_note
                    do = frappe.get_doc('Delivery Note',do_no)
                    do.submit()
                    frappe.msgprint("A Delivery Note corresponding to the sales invoice is also submitted.", indicator="green", alert=True)
                return
            
    @frappe.whitelist()
    def generate_delivery_note(self):

        # if self.docstatus == 1:
        #     # Submission happening in the submit_delivery_note method
        #     return

        delivery_note_name = ""

        doNo = ""

        si_name = self.name

        do_exists = False

        if self.auto_save_delivery_note:

            if frappe.db.exists('Sales Invoice Delivery Notes', {'parent': self.name}):
                do_exists = True

                delivery_note_name =  frappe.db.get_value('Sales Invoice Delivery Notes',{'parent':self.name},['delivery_note'] )

                # Remove the reference first before deleting the actual document
                # frappe.db.delete('Sales Invoice Delivery Notes',{'parent':self.name})
                delivery_note_doc = frappe.get_doc('Delivery Note', delivery_note_name)
                doNo = delivery_note_doc.name

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

                delivery_note = self.__dict__
                delivery_note['doctype'] = 'Delivery Note'
                # delivery_note['against_sales_invoice'] = delivery_note['name']
                # delivery_note['name'] = delivery_note_name
                delivery_note['naming_series'] = ""
                delivery_note['posting_date'] = self.posting_date
                delivery_note['posting_time'] = self.posting_time
                delivery_note['amended_from'] = ""

                delivery_note['auto_generated_from_sales_invoice'] = 0

                for item in delivery_note['items']:
                    item.doctype = "Delivery Note Item"
                    item._meta = ""

                delivery_note_doc = frappe.get_doc(delivery_note).insert()
                frappe.db.commit()

                delivery_note_name = delivery_note_doc.name

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

        # delivery_notes = frappe.db.get_all('Sales Invoice Delivery Notes', {'parent': ['=', si_name]},{'delivery_note'})
        delivery_notes = frappe.db.get_all('Sales Invoice Delivery Notes',
                                    filters={'parent': si_name},
                                    fields=['delivery_note'])

        # It is likely that there will be only one delivery note for the sales invoice for this method.
        index = 0
        maxIndex = 3
        doNos = ""

        for delivery_note_saved in delivery_notes:
            do_created = frappe.get_doc('Delivery Note',delivery_note_saved.delivery_note )

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

    def cancel_delivery_note_for_sales_invoice(self):

        delivery_note = frappe.get_value("Sales Invoice Delivery Notes",{'parent': self.name}, ['delivery_note'])
        do = frappe.get_doc('Delivery Note',delivery_note)
        do.cancel()
        frappe.msgprint("Sales invoice and delivery note cancelled successfully", alert= True)

            # frappe.msgprint("Delivery Note cancelled")
    def do_stock_posting(self):

            if not self.update_stock and not self.tab_sales:
                return

            stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
            stock_recalc_voucher.voucher = 'Sales Invoice'
            stock_recalc_voucher.voucher_no = self.name
            stock_recalc_voucher.voucher_date = self.posting_date
            stock_recalc_voucher.voucher_time = self.posting_time
            stock_recalc_voucher.status = 'Not Started'
            stock_recalc_voucher.source_action = "Insert"

            more_records = 0

            default_company = frappe.db.get_single_value("Global Settings", "default_company")
            company_info = frappe.get_value("Company",default_company,['allow_negative_stock'], as_dict = True)

            allow_negative_stock = company_info.allow_negative_stock

            if not allow_negative_stock:
                allow_negative_stock = False

            # Create a dictionary for handling duplicate items. In stock ledger posting it is expected to have only one stock ledger per item per voucher.
            item_stock_ledger = {}

            for docitem in self.items:
                maintain_stock = frappe.db.get_value('Item', docitem.item , 'maintain_stock')
                
                if(maintain_stock == 1):

                    posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))

                    # Check for more records after this date time exists. This is mainly for deciding whether stock balance needs to update
                    # in this flow itself. If more records, exists stock balance will be udpated lateer
                    more_records_count_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
                        'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})

                    more_records = more_records + more_records_count_for_item

                    # Check available qty
                    previous_stock_balance = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
                    , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
                    order_by='posting_date desc', as_dict=True)

                    previous_stock_balance_value = 0

                    if previous_stock_balance:

                        new_balance_qty = previous_stock_balance.balance_qty - docitem.qty_in_base_unit
                        valuation_rate = previous_stock_balance.valuation_rate
                        previous_stock_balance_value = previous_stock_balance.balance_value
                    else:
                        
                        new_balance_qty = 0 - docitem.qty_in_base_unit
                        valuation_rate = frappe.get_value("Item", docitem.item, ['standard_buying_price'])

                    new_balance_value = previous_stock_balance_value - (docitem.qty_in_base_unit * valuation_rate)

                    if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
                        frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse})

                    change_in_stock_value = new_balance_value - previous_stock_balance_value


                    # Allows to post the item only once to the stock ledger.
                    if docitem.item not in item_stock_ledger:
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

                        sl = frappe.get_doc("Stock Ledger", new_stock_ledger.name)

                        item_stock_ledger[docitem.item] = sl.name

                    else:
                        stock_ledger_name = item_stock_ledger.get(docitem.item)
                        stock_ledger = frappe.get_doc('Stock Ledger', stock_ledger_name)

                        stock_ledger.qty_out = stock_ledger.qty_out + docitem.qty_in_base_unit
                        stock_ledger.balance_qty = stock_ledger.balance_qty - docitem.qty_in_base_unit
                        stock_ledger.balance_value = stock_ledger.balance_qty * stock_ledger.valuation_rate
                        stock_ledger.change_in_stock_value = stock_ledger.change_in_stock_value - (stock_ledger.balance_qty * stock_ledger.valuation_rate)
                        new_balance_qty = stock_ledger.balance_qty
                        stock_ledger.save()

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
                        update_stock_balance_in_item(docitem.item)
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


    def get_cost_of_goods_sold(self):

            cost_of_goods_sold_in_stock_ledgers_query = """select sum(qty_out*valuation_rate) as cost_of_goods_sold from `tabStock Ledger` where voucher='Sales Invoice' and voucher_no=%s"""

            cog_data = frappe.db.sql(cost_of_goods_sold_in_stock_ledgers_query,(self.name), as_dict = True)

            cost_of_goods_sold = 0

            if(cog_data):
                cost_of_goods_sold = cog_data[0].cost_of_goods_sold

            return cost_of_goods_sold

    def update_receipt_schedules(self):
        existing_entries = frappe.get_all("Receipt Schedule", filters={"receipt_against": "Sales", "document_no": self.name})
        for entry in existing_entries:
            try:
                frappe.delete_doc("Receipt Schedule", entry.name)
            except Exception as e:
                frappe.log_error("Error deleting receipt schedule: " + str(e))
                
        if self.credit_sale and self.receipt_schedule:
            for schedule in self.receipt_schedule:
                new_receipt_schedule = frappe.new_doc("Receipt Schedule")
                new_receipt_schedule.receipt_against = "Sales"
                new_receipt_schedule.customer = self.customer
                new_receipt_schedule.document_no = self.name
                new_receipt_schedule.document_date = self.posting_date
                new_receipt_schedule.scheduled_date = schedule.date
                new_receipt_schedule.amount = schedule.amount
                try:
                    new_receipt_schedule.insert()
                except Exception as e:
                    frappe.log_error("Error creating receipt schedule: " + str(e))
                    
    def update_project_billed_amounts(self, cancel=False):
            
        if self.project:
            # Define filters to fetch submitted invoices excluding the current document
            filters = {
                "project": self.project,
                "name": ["!=", self.name],  # Exclude the current document
                "docstatus": 1  # Include only submitted documents
            }

            total_billed_amount = 0
            total_billed_amount_gross = 0

            # Fetch all submitted Sales Invoices related to the project
            sales_invoices = frappe.get_all(
                "Sales Invoice",
                filters=filters,
                fields=["gross_total", "rounded_total"]
            )

            # Fetch all submitted Progressive Sales Invoices related to the project
            progressive_sales_invoices = frappe.get_all(
                "Progressive Sales Invoice",
                filters=filters,
                fields=["gross_total", "rounded_total"]
            )

            # Iterate through Sales Invoices
            for invoice in sales_invoices:
                total_billed_amount += invoice.get("rounded_total", 0)
                total_billed_amount_gross += invoice.get("gross_total", 0)

            # Iterate through Progressive Sales Invoices
            for invoice in progressive_sales_invoices:
                total_billed_amount += invoice.get("rounded_total", 0)
                total_billed_amount_gross += invoice.get("gross_total", 0)

            # If not cancelling, add the current document's contribution
            if not cancel:
                # Add the current document's gross_total and rounded_total
                total_billed_amount += self.rounded_total or 0
                total_billed_amount_gross += self.gross_total or 0

            # Update the 'total_billed_amount' and 'total_billed_amount_gross' fields in the Project
            frappe.db.set_value(
                "Project",
                self.project,
                {
                    "total_billed_amount": total_billed_amount,
                    "total_billed_amount_gross": total_billed_amount_gross
                }
            )

            # Optional: Feedback or logging
            frappe.msgprint(
                f"The 'total_billed_amount' and 'total_billed_amount_gross' fields of project {self.project} "
                f"have been updated to {total_billed_amount} and {total_billed_amount_gross}, respectively.", alert= True
            )

    @frappe.whitelist()
    def generate_sales_invoice(self):

        sales_invoice = frappe.new_doc('Sales Invoice')

        sales_invoice.customer = self.customer
        sales_invoice.customer_name = self.customer_name
        sales_invoice.customer_display_name = self.customer_display_name
        sales_invoice.customer_address = self.customer_address        
        sales_invoice.posting_date = self.posting_date
        sales_invoice.posting_time = self.posting_time
        sales_invoice.ship_to_location = self.ship_to_location
        sales_invoice.salesman = self.salesman
        sales_invoice.salesman_code = self.salesman_code
        sales_invoice.tax_id = self.tax_id        
        sales_invoice.price_list = self.price_list
        sales_invoice.rate_includes_tax = self.rate_includes_tax
        sales_invoice.warehouse = self.warehouse
        sales_invoice.update_stock = self.update_stock
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
        sales_invoice.company = self.company

        sales_invoice.save()

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

            sales_invoice.save()

        frappe.msgprint("Sales Invoice duplicated successfully.",indicator="green", alert=True)
        
        return sales_invoice.name


    @frappe.whitelist()
    def get_default_payment_mode():
        default_payment_mode = frappe.db.get_value('Company', filters={'name'},fieldname='default_payment_mode_for_sales')

        return default_payment_mode

    @frappe.whitelist()
    def get_delivery_note_items(delivery_notes):
        if isinstance(delivery_notes, str):
            delivery_notes = frappe.parse_json(delivery_notes)
        items = []
        for delivery_note in delivery_notes:
            delivery_note_items = frappe.get_all('Delivery Note Item',
                                                filters={'parent': delivery_note},
                                                fields=['name', 'item', 'qty', 'warehouse', 'item_name', 'display_name', 'unit', 'rate', 'base_unit',
                                                'qty_in_base_unit', 'rate_in_base_unit', 'conversion_factor', 'rate_includes_tax', 'gross_amount',
                                                'tax_excluded', 'tax_rate', 'tax_amount', 'discount_percentage', 'discount_amount', 'net_amount'
                                                ])
            for dn_item in delivery_note_items:
                dn_item['delivery_note_item_reference_no'] = dn_item['name']
                items.append(dn_item)

        return items

   
    @frappe.whitelist()
    def get_stock_ledgers(sales_invoice):
        stock_ledgers = frappe.get_all("Stock Ledger",
                                        filters={"voucher_no": sales_invoice},
                                        fields=["name", "item", "warehouse", "qty_in", "qty_out", "valuation_rate", "balance_qty", "balance_value"])
        formatted_stock_ledgers = []
        for ledgers in stock_ledgers:
            formatted_stock_ledgers.append({
                "stock_ledger": ledgers.name,
                "item": ledgers.item,
                "warehouse": ledgers.warehouse,
                "qty_in": ledgers.qty_in,
                "qty_out": ledgers.qty_out,
                "valuation_rate": ledgers.valuation_rate,
                "balance_qty": ledgers.balance_qty,
                "balance_value": ledgers.balance_value
            })

        return formatted_stock_ledgers
    
