# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now
from frappe.model.document import Document
from datetime import datetime,timedelta
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_stock_balance_in_item
from digitz_erp.api.document_posting_status_api import init_document_posting_status, update_posting_status
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type
from frappe import throw, _


class StockReconciliation(Document):

    def validate(self):
        self.validate_items()

    def validate_items(self):
        items = set()
        for item in self.items:
            if item.item in items:
                frappe.throw(_("Item {0} is already added in the list").format(item.item))
            items.add(item.item)

    def Voucher_In_The_Same_Time(self):
        possible_invalid= frappe.db.count('Stock Reconciliation', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time]})
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


    def on_submit(self):

        init_document_posting_status(self.doctype, self.name)

        turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

        # if(frappe.session.user == "Administrator" and turn_off_background_job):
        #     self.do_postings_on_submit()
        # else:
            # frappe.enqueue(self.do_postings_on_submit, queue="long")
        self.do_postings_on_submit()

    def do_postings_on_submit(self):

        stock_adjustment_value =  self.add_stock_reconciliation()

        if(stock_adjustment_value !=0):
            self.insert_gl_records(stock_adjustment_value = stock_adjustment_value)

        update_posting_status(self.doctype,self.name, 'posting_status','Completed')

        update_accounts_for_doc_type('Stock Reconciliation', self.name)

    def add_stock_reconciliation(self):

        more_records = 0

        stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
        stock_recalc_voucher.voucher = 'Stock Reconciliation'
        stock_recalc_voucher.voucher_no = self.name
        stock_recalc_voucher.voucher_date = self.posting_date
        stock_recalc_voucher.voucher_time = self.posting_time
        stock_recalc_voucher.status = 'Not Started'
        stock_recalc_voucher.source_action = "Insert"

        stock_adjustment_value = 0

        for docitem in self.items:
            maintain_stock = frappe.db.get_value('Item', docitem.item , 'maintain_stock')
            print('MAINTAIN STOCK :', maintain_stock)
            if(maintain_stock == 1):

                change_in_stock_value_for_item = 0

                new_balance_qty = docitem.qty_in_base_unit
                # Default valuation rate
                valuation_rate = docitem.rate_in_base_unit

                posting_date_time = get_datetime(
                    str(self.posting_date) + " " + str(self.posting_time))

                # Default balance value calculating withe the current row only
                new_balance_value = new_balance_qty * valuation_rate

                # posting_date<= consider because to take the dates with in the same minute
                # dbCount = frappe.db.count('Stock Ledger',{'item_code': ['=', docitem.item_code],'warehouse':['=', docitem.warehouse], 'posting_date':['<=', posting_date_time]})
                dbCount = frappe.db.count('Stock Ledger', {'item': ['=', docitem.item], 'warehouse': [
                                          '=', docitem.warehouse], 'posting_date': ['<', posting_date_time]})

                # In case opening stock entry, assign the qty as qty_in
                qty_in = docitem.qty_in_base_unit
                qty_out =0

                if (dbCount > 0):

                    # Find out the balance value and valuation rate. Here recalculates the total balance value and valuation rate
                    # from the balance qty in the existing rows x actual incoming rate

                    last_stock_ledger = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse': ['=', docitem.warehouse], 'posting_date': [
                                                            '<', posting_date_time]}, ['balance_qty', 'balance_value', 'valuation_rate'], order_by='posting_date desc', as_dict=True)

                    previous_stock_balance_qty = last_stock_ledger.balance_qty

                    if(previous_stock_balance_qty> new_balance_qty):
                        qty_out = previous_stock_balance_qty - new_balance_qty
                        qty_in = 0
                    else:
                        qty_in = new_balance_qty - previous_stock_balance_qty
                        qty_out = 0

                    previous_stock_value = last_stock_ledger.balance_value

                    if(new_balance_value> previous_stock_value): # stock value raised
                        stock_adjustment_value = stock_adjustment_value + (new_balance_value - previous_stock_value)
                        change_in_stock_value_for_item = (new_balance_value - previous_stock_value)
                    elif(previous_stock_value>new_balance_value): # stock value diminished:
                        stock_adjustment_value = stock_adjustment_value - (previous_stock_value -new_balance_value)
                        change_in_stock_value_for_item = new_balance_value - previous_stock_value
                else:
                    stock_adjustment_value = stock_adjustment_value + new_balance_value
                    change_in_stock_value_for_item = new_balance_value

                new_stock_ledger = frappe.new_doc("Stock Ledger")
                new_stock_ledger.item = docitem.item
                new_stock_ledger.item_name = docitem.item_name
                new_stock_ledger.warehouse = docitem.warehouse
                new_stock_ledger.posting_date = posting_date_time
                new_stock_ledger.change_in_stock_value = change_in_stock_value_for_item

                new_stock_ledger.qty_in = qty_in

                print("qty_in")
                print(qty_in)

                new_stock_ledger.qty_out = qty_out
                new_stock_ledger.unit = docitem.base_unit

                if(qty_in >0):
                    new_stock_ledger.incoming_rate = valuation_rate

                if(qty_out >0):
                    new_stock_ledger.outgoing_rate = valuation_rate

                new_stock_ledger.valuation_rate = valuation_rate
                new_stock_ledger.balance_qty = new_balance_qty
                new_stock_ledger.balance_value = new_balance_value
                new_stock_ledger.voucher = "Stock Reconciliation"
                new_stock_ledger.voucher_no = self.name
                new_stock_ledger.source = "Stock Reconciliation Item"
                new_stock_ledger.source_document_id = docitem.name
                new_stock_ledger.insert()

                more_records_count_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
    				'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})

                more_records = more_records + more_records_count_for_item

                if(more_records_count_for_item>0):

                    stock_recalc_voucher.append('records',{'item': docitem.item,
                                                                'warehouse': docitem.warehouse,
                                                                'base_stock_ledger': new_stock_ledger.name
                                                                })

                else:
                    if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
                        frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse} )

                    new_stock_balance = frappe.new_doc('Stock Balance')
                    new_stock_balance.item = docitem.item
                    new_stock_balance.unit = docitem.base_unit
                    new_stock_balance.warehouse = docitem.warehouse
                    new_stock_balance.stock_qty = new_balance_qty
                    new_stock_balance.stock_value = new_balance_value
                    new_stock_balance.valuation_rate = valuation_rate

                    new_stock_balance.insert()

                    # item_name = frappe.get_value("Item", docitem.item,['item_name'])
                    update_stock_balance_in_item(docitem.item)

        update_posting_status(self.doctype,self.name,'stock_posted_time')

        if(more_records>0):

            update_posting_status(self.doctype,self.name,'stock_recalc_required', True)

            stock_recalc_voucher.insert()
            recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)

            update_posting_status(self.doctype,self.name,'stock_recalc_time')

        print(stock_adjustment_value)
        return stock_adjustment_value

    def on_cancel(self):

        turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

        # if(frappe.session.user == "Administrator" and turn_off_background_job):
        #     self.cancel_stock_reconciliation()
        # else:
            # frappe.enqueue(self.cancel_stock_reconciliation, queue="long")
        self.cancel_stock_reconciliation()

    def cancel_stock_reconciliation(self):

        # Insert record to 'Stock Recalculate Voucher' doc
        stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
        stock_recalc_voucher.voucher = 'Purchase Invoice'
        stock_recalc_voucher.voucher_no = self.name
        stock_recalc_voucher.voucher_date = self.posting_date
        stock_recalc_voucher.voucher_time = self.posting_time
        stock_recalc_voucher.status = 'Not Started'
        stock_recalc_voucher.source_action = "Cancel"

        posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))

        more_records = 0

        # Iterate on each item from the cancelling purchase invoice
        for docitem in self.items:
            more_records_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
                'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})

            more_records = more_records + more_records_for_item

            previous_stock_ledger_name = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
                        , 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)

            # If any items in the collection has more records
            if(more_records_for_item>0):

                stock_ledger_items = frappe.get_list('Stock Ledger',{'item':docitem.item,
                'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]}, ['name','qty_in','qty_out','voucher','balance_qty','voucher_no'],order_by='posting_date')

                # if(stock_ledger_items):

                #     qty_cancelled = docitem.qty_in_base_unit
                #     # Loop to verify the sufficiant quantity
                #     for sl in stock_ledger_items:
                #         # On each line if outgoing qty + balance_qty (qty before outgonig) is more than the cancelling qty
                #         if(sl.qty_out>0 and qty_cancelled> sl.qty_out+ sl.balance_qty):
                #             frappe.throw("Cancelling the stock reconciliation is prevented due to sufficiant quantity not available for " + docitem.item +
                #         " to fulfil the voucher " + sl.voucher_no)

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
                stock_balance_for_item = frappe.new_doc("Stock Balance")
                stock_balance_for_item.item = docitem.item
                stock_balance_for_item.unit = unit
                stock_balance_for_item.warehouse = docitem.warehouse
                stock_balance_for_item.stock_qty = balance_qty
                stock_balance_for_item.stock_value = balance_value
                stock_balance_for_item.valuation_rate = valuation_rate
                stock_balance_for_item.insert()

                # item_name = frappe.get_value("Item", docitem.item,['item_name'])
                update_stock_balance_in_item(docitem.item)

        update_posting_status(self.doctype, self.name, 'stock_posted_on_cancel_time')

        if(more_records>0):
            update_posting_status(self.doctype, self.name, 'stock_recalc_required_on_cancel', True)

            stock_recalc_voucher.insert()
            recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)

            update_posting_status(self.doctype, self.name, 'stock_recalc_on_cancel_time')

        frappe.db.delete("Stock Ledger",
                {"voucher": "Stock Reconciliation",
                    "voucher_no":self.name
                })

        delete_gl_postings_for_cancel_doc_type('Stock Reconciliation', self.name)

        update_posting_status(self.doctype,self.name, 'posting_status','Completed')

    def insert_gl_records(self, stock_adjustment_value):

        default_company = frappe.db.get_single_value(
            "Global Settings", "default_company")

        default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account','default_income_account', 'stock_adjustment_account', 'round_off_account', 'tax_account'], as_dict=1)

        idx = 1

        if self.purpose == "Stock Reconciliation":
            # Inventory account Eg: Stock In Hand
            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Stock Reconciliation"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = default_accounts.default_inventory_account
            if stock_adjustment_value > 0: # Value Raised
                gl_doc.debit_amount = stock_adjustment_value
            else:
                gl_doc.credit_amount = stock_adjustment_value

            gl_doc.against_account = default_accounts.stock_adjustment_account
            gl_doc.insert()

            # Cost Of Goods Sold
            idx = 2
            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Stock Reconciliation"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = default_accounts.stock_adjustment_account

            if stock_adjustment_value > 0: # Value diminished
                gl_doc.credit_amount = stock_adjustment_value
            else:
                gl_doc.debit_amount = stock_adjustment_value

            gl_doc.against_account = default_accounts.default_inventory_account
            gl_doc.insert()
            update_posting_status(self.doctype,self.name,'gl_posted')

        elif self.purpose == "Opening Stock":

            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Stock Reconciliation"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = default_accounts.default_inventory_account
            gl_doc.debit_amount = self.net_total
            gl_doc.against_account = default_accounts.stock_adjustment_account
            gl_doc.insert()

            # Cost Of Goods Sold
            idx = 2
            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Stock Reconciliation"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = self.account
            gl_doc.credit_amount = self.net_total
            gl_doc.against_account = default_accounts.default_inventory_account
            gl_doc.insert()
            update_posting_status(self.doctype,self.name,'gl_posted')

@frappe.whitelist()
def get_gl_postings(stock_reconciliation):
    gl_postings = frappe.get_all("GL Posting",
                                  filters={"voucher_no": stock_reconciliation},
                                  fields=["name", "debit_amount", "credit_amount", "against_account", "remarks"])
    formatted_gl_postings = []
    for posting in gl_postings:
        formatted_gl_postings.append({
            "gl_posting": posting.name,
            "debit_amount": posting.debit_amount,
            "credit_amount": posting.credit_amount,
            "against_account": posting.against_account,
            "remarks": posting.remarks
        })

    return formatted_gl_postings

@frappe.whitelist()
def get_stock_ledgers(stock_reconciliation):
    stock_ledgers = frappe.get_all("Stock Ledger",
                                    filters={"voucher_no": stock_reconciliation},
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
    print(formatted_stock_ledgers)
    return formatted_stock_ledgers
