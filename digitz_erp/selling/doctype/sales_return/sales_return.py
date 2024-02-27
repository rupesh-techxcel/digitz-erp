# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils import now
from frappe.model.document import Document
from digitz_erp.utils import *
from frappe.model.mapper import *
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_stock_balance_in_item
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type
from digitz_erp.api.bank_reconciliation_api import create_bank_reconciliation, cancel_bank_reconciliation
class SalesReturn(Document):

    def validate(self):
        self.validate_sales()

    def validate_sales(self):

        for docitem in self.items:
            if(docitem.si_item_reference):

                pi = frappe.get_doc("Sales Invoice Item", docitem.si_item_reference)

                total_returned_qty_not_in_this_sr = frappe.db.sql(""" SELECT SUM(qty) as total_returned_qty from `tabSales Return Item` sreti inner join `tabSales Return` sret on sreti.parent= sret.name WHERE sreti.si_item_reference=%s AND sret.name !=%s and sret.docstatus<2""",(docitem.si_item_reference, self.name))[0][0]

                si_item = frappe.get_doc("Sales Invoice Item", docitem.si_item_reference)

                print(total_returned_qty_not_in_this_sr)
                print(docitem.qty)

                if total_returned_qty_not_in_this_sr:
                    if(si_item.qty < (total_returned_qty_not_in_this_sr + docitem.qty)):
                        frappe.throw("The quantity available for return in the original sales is less than the quantity specified in the line item {}".format(docitem.idx))
                else:
                    if(si_item.qty < docitem.qty):
                        frappe.throw("The quantity available for return in the original sales is less than the quantity specified in the line item {}".format(docitem.idx))

    def on_submit(self):

        turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

        if(frappe.session.user == "Administrator" and turn_off_background_job):
            self.do_postings_on_submit()
        else:
            # frappe.enqueue(self.do_postings_on_submit, queue="long")
            self.do_postings_on_submit()

    def do_postings_on_submit(self):
        # Cost of goods sold need not include for Sales Return because it is not an expense but its only a reduction of sales revenue.
        self.do_stock_posting()
        self.insert_gl_records()
        self.insert_payment_postings()
        update_accounts_for_doc_type('Sales Return', self.name)
        create_bank_reconciliation("Sales Return", self.name)

    def insert_gl_records(self):
        default_company = frappe.db.get_single_value(
            "Global Settings", "default_company")
        default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                            'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)
        idx = 1
        # Receivable - Debit
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Sales Return"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.default_receivable_account
        gl_doc.credit_amount = self.rounded_total
        gl_doc.party_type = "Customer"
        gl_doc.party = self.customer
        gl_doc.against_account = default_accounts.default_income_account
        gl_doc.insert()
        idx +=1

        # Income account - Credit

        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Sales Return"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.default_income_account
        gl_doc.debit_amount = self.net_total - self.tax_total
        gl_doc.against_account = default_accounts.default_receivable_account
        gl_doc.insert()
        idx +=1

        # Tax - Credit
        if self.tax_total>0:
            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Sales Return"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = default_accounts.tax_account
            gl_doc.debit_amount = self.tax_total
            gl_doc.against_account = default_accounts.default_receivable_account
            gl_doc.insert()
            idx +=1

        cost_of_goods_sold = self.get_cost_of_goods_sold()

        # Inventory Account
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Sales Return"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.default_inventory_account
        gl_doc.debit_amount = cost_of_goods_sold
        gl_doc.against_account = default_accounts.cost_of_goods_sold_account
        gl_doc.insert()
        idx +=1

        # COGS
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Sales Return"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.cost_of_goods_sold_account
        gl_doc.credit_amount = cost_of_goods_sold
        gl_doc.against_account = default_accounts.default_inventory_account
        gl_doc.insert()
        idx +=1

        # Round Off
        if self.round_off != 0.00:
            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Sales Return"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = default_accounts.round_off_account
            if self.rounded_total > self.net_total:
                gl_doc.debit_amount = self.round_off
            else:
                gl_doc.credit_amount = self.round_off
            gl_doc.insert()
            idx +=1



    def insert_payment_postings(self):
        if self.credit_sale == 0:
            gl_count = frappe.db.count(
                'GL Posting', {'voucher_type': 'Sales Return', 'voucher_no': self.name})
            default_company = frappe.db.get_single_value(
                "Global Settings", "default_company")
            default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                             'stock_received_but_not_billed', 'round_off_account', 'tax_account'], as_dict=1)
            payment_mode = frappe.get_value(
                "Payment Mode", self.payment_mode, ['account'], as_dict=1)

            idx = gl_count + 1
            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Sales Return"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = default_accounts.default_receivable_account
            gl_doc.debit_amount = self.rounded_total
            gl_doc.party_type = "Customer"
            gl_doc.party = self.customer
            gl_doc.against_account = payment_mode.account
            gl_doc.insert()

            idx = idx + 1

            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Sales Return"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = payment_mode.account
            gl_doc.credit_amount = self.rounded_total
            gl_doc.against_account = default_accounts.default_receivable_account
            gl_doc.insert()

    def on_update(self):
        self.update_sales_invoice_quantities_on_update()

    def on_cancel(self):
        cancel_bank_reconciliation("Sales Return", self.name)
        turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

        # if(frappe.session.user == "Administrator" and turn_off_background_job):
        #     self.cancel_sales_return()
        # else:
            # frappe.enqueue(self.cancel_sales_return, queue="long")
        self.cancel_sales_return()

    def on_trash(self):
        # On cancel the quantities are already deleted.
        if(self.docstatus < 2):
          self.update_sales_invoice_quantities_before_delete_or_cancel()

    def update_sales_invoice_quantities_before_delete_or_cancel(self):

        si_reference_any = False

        for item in self.items:
            if not item.si_item_reference:
                continue
            else:
                total_returned_qty_not_in_this_sr = frappe.db.sql(""" SELECT SUM(qty) as total_returned_qty from `tabSales Return Item` sreti inner join `tabSales Return` sret on sreti.parent= sret.name WHERE sreti.si_item_reference=%s AND sret.name !=%s and sret.docstatus<2""",(item.si_item_reference, self.name))[0][0]

                si_item = frappe.get_doc("Sales Invoice Item", item.si_item_reference)

                if total_returned_qty_not_in_this_sr:
                    si_item.qty_returned = total_returned_qty_not_in_this_sr
                else:
                    si_item.qty_returned = 0

                si_item.save()
                si_reference_any = True

                if(si_item.delivery_note_item_reference_no):
                    self.update_delivery_note_quantities_for_invoice(si_item.name,si_item.delivery_note_item_reference_no,si_item.qty_returned)

        if si_reference_any:
            frappe.msgprint("Returned qty of items in the corresponding sales invoice reverted successfully", indicator= "green", alert= True)

    def update_delivery_note_quantities_for_invoice(self,si_item_reference,do_item_reference,qty_returned):

        do_item = frappe.get_doc("Delivery Note Item", do_item_reference)

        # The Delivery Note serves as a preceding document to the sales invoice, allowing for the existence of multiple sales invoices corresponding to a single delivery note. Therefore, it is necessary to reevaluate the quantity returned for the item in the delivery note in comparison to the quantity returned for any other line item in a sales invoice, taking into account the reference to the identical delivery note line item.

        total_returned_qty_not_in_this_si = frappe.db.sql(""" SELECT SUM(qty_returned) as total_returned_qty from `tabSales Invoice Item` where delivery_note_item_reference_no= %s and name!=%s and docstatus<2""",(do_item_reference,si_item_reference))[0][0]
        if(not total_returned_qty_not_in_this_si):
            total_returned_qty_not_in_this_si = 0
        do_item.qty_returned = qty_returned + total_returned_qty_not_in_this_si

        do_item.save()

    def update_sales_invoice_quantities_on_update(self):

        si_reference_any = False

        for item in self.items:
            if not item.si_item_reference:
                continue
            else:
                total_returned_qty_not_in_this_sr = frappe.db.sql(""" SELECT SUM(qty) as total_returned_qty from `tabSales Return Item` sreti inner join `tabSales Return` sret on sreti.parent= sret.name WHERE sreti.si_item_reference=%s AND sret.name !=%s and sret.docstatus<2""",(item.si_item_reference, self.name))[0][0]

                si_item = frappe.get_doc("Sales Invoice Item", item.si_item_reference)

                if total_returned_qty_not_in_this_sr:
                    si_item.qty_returned = total_returned_qty_not_in_this_sr + item.qty
                else:
                    si_item.qty_returned = item.qty
                si_item.save()
                si_reference_any = True

                if(si_item.delivery_note_item_reference_no):
                    self.update_delivery_note_quantities_for_invoice(si_item.name,si_item.delivery_note_item_reference_no,si_item.qty_returned)

        if si_reference_any:
            frappe.msgprint("Returned qty of items in the corresponding sales invoice updated successfully", indicator= "green", alert= True)

    def cancel_sales_return(self):

        print("from cancel sales return")

        self.update_sales_invoice_quantities_before_delete_or_cancel()

        print("before do_cancel_stock_posting")

        self.do_cancel_stock_posting()

        delete_gl_postings_for_cancel_doc_type('Sales Return',self.name)

        # frappe.db.delete("GL Posting",
        #         {"Voucher_type": "Sales Return",
        #             "voucher_no":self.name
        #         })

    def do_stock_posting(self):
        cost_of_goods_sold =0
        # Note that negative stock checking is handled in the validate method
        stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
        stock_recalc_voucher.voucher = 'Sales Return'
        stock_recalc_voucher.voucher_no = self.name
        stock_recalc_voucher.voucher_date = self.posting_date
        stock_recalc_voucher.voucher_time = self.posting_time
        stock_recalc_voucher.status = 'Not Started'
        stock_recalc_voucher.source_action = "Insert"
        more_records = 0

        posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))

        # Create a dictionary for handling duplicate items. In stock ledger posting it is expected to have only one stock ledger per item per voucher.
        item_stock_ledger = {}

        for docitem in self.items:
            maintain_stock = frappe.db.get_value('Item', docitem.item , 'maintain_stock')
            print('MAINTAIN STOCK :', maintain_stock)
            if(maintain_stock == 1):

        # Check for more records after this date time exists. This is mainly for deciding whether stock balance needs to update
        # in this flow itself. If more records, exists stock balance will be udpated later
                more_records_count_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
                    'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})
                more_records = more_records + more_records_count_for_item
                new_balance_qty = docitem.qty_in_base_unit

                previous_stock_ledger_name = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
                    , 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)

                item_in_master = frappe.get_doc("Item", docitem)

                # Default valuation rate
                valuation_rate = item_in_master.standard_buying_price
                new_balance_value = new_balance_qty * valuation_rate
                change_in_stock_value = new_balance_value

                dbCount = frappe.db.count('Stock Ledger',{'item': ['=', docitem.item],'warehouse':['=', docitem.warehouse],
                                                    'posting_date': ['<', posting_date_time]})
                if(dbCount>0):
                    # Find out the balance value and valuation rate. Here recalculates the total balance value and valuation rate
                    # from the balance qty in the existing rows x actual incoming rate
                    last_stock_ledger = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse],
                                                            'posting_date':['<', posting_date_time]},
                                                ['balance_qty', 'balance_value', 'valuation_rate'],order_by='posting_date desc', as_dict=True)

                    # Note that in the first step new_balance_qty and new_balance_value is negative
                    new_balance_qty = last_stock_ledger.balance_qty + abs(new_balance_qty)
                    new_balance_value = last_stock_ledger.balance_value + abs(new_balance_value)

                    if new_balance_qty!=0:
                        # Sometimes the balance_value and balance_qty can be negative, so it is ideal to take the abs value
                        valuation_rate = abs(new_balance_value)/abs(new_balance_qty)

                    change_in_stock_value = new_balance_value - last_stock_ledger.balance_value

                if docitem.item not in item_stock_ledger:

                    new_stock_ledger = frappe.new_doc("Stock Ledger")
                    new_stock_ledger.item = docitem.item
                    new_stock_ledger.item_name = docitem.item_name
                    new_stock_ledger.warehouse = docitem.warehouse
                    new_stock_ledger.posting_date = posting_date_time
                    new_stock_ledger.qty_in = docitem.qty_in_base_unit
                    new_stock_ledger.incoming_rate = docitem.rate_in_base_unit
                    new_stock_ledger.unit = docitem.base_unit
                    new_stock_ledger.valuation_rate = valuation_rate
                    new_stock_ledger.balance_qty = new_balance_qty
                    new_stock_ledger.balance_value = new_balance_value
                    new_stock_ledger.change_in_stock_value = change_in_stock_value
                    new_stock_ledger.voucher = "Sales Return"
                    new_stock_ledger.voucher_no = self.name
                    new_stock_ledger.source = "Sales Return Item"
                    new_stock_ledger.source_document_id = docitem.name
                    new_stock_ledger.insert()

                    sl = frappe.get_doc("Stock Ledger", new_stock_ledger.name)

                    item_stock_ledger[docitem.item] = sl.name

                else:
                    stock_ledger_name = item_stock_ledger.get(docitem.item)
                    stock_ledger = frappe.get_doc('Stock Ledger', stock_ledger_name)

                    stock_ledger.qty_in = stock_ledger.qty_in + docitem.qty_in_base_unit
                    stock_ledger.balance_qty = stock_ledger.balance_qty + docitem.qty_in_base_unit
                    stock_ledger.balance_value = stock_ledger.balance_qty * stock_ledger.valuation_rate
                    stock_ledger.change_in_stock_value = stock_ledger.change_in_stock_value + (stock_ledger.balance_qty * stock_ledger.valuation_rate)
                    change_in_stock_value = stock_ledger.change_in_stock_value
                    new_balance_qty = stock_ledger.balance_qty
                    stock_ledger.save()

                sl = frappe.get_doc("Stock Ledger", new_stock_ledger.name)
                # If no more records for the item, update balances. otherwise it updates in the flow
                if more_records_count_for_item==0:
                    if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
                        frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse})
                    new_stock_balance = frappe.new_doc('Stock Balance')
                    new_stock_balance.item = docitem.item
                    new_stock_balance.unit = docitem.unit
                    new_stock_balance.warehouse = docitem.warehouse
                    new_stock_balance.stock_qty = new_balance_qty
                    new_stock_balance.stock_value = new_balance_value
                    new_stock_balance.valuation_rate = valuation_rate
                    new_stock_balance.insert()
                    # item_name = frappe.get_value("Item", docitem.item,['item_name'])
                    update_stock_balance_in_item(docitem.item)

                else:
                    if previous_stock_ledger_name:
                        stock_recalc_voucher.append('records',{'item': docitem.item,
                                                                'warehouse': docitem.warehouse,
                                                                'base_stock_ledger': new_stock_ledger.name
                                                                    })
                    else:
                        stock_recalc_voucher.append('records',{'item': docitem.item,
                                                                    'warehouse': docitem.warehouse,
                                                                    'base_stock_ledger': "No Previous Ledger"
                                                                    })
        if(more_records>0):
            stock_recalc_voucher.insert()
            recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)



    def do_cancel_stock_posting(self):

        # Insert record to 'Stock Recalculate Voucher' doc
        stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
        stock_recalc_voucher.voucher = 'Sales Return'
        stock_recalc_voucher.voucher_no = self.name
        stock_recalc_voucher.voucher_date = self.posting_date
        stock_recalc_voucher.voucher_time = self.posting_time
        stock_recalc_voucher.status = 'Not Started'
        stock_recalc_voucher.source_action = "Cancel"
        posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))
        more_records = 0

        # Iterate on each item from the cancelling Purchase Return
        for docitem in self.items:
            print("more_records_for_item 1")
            print(docitem.item)

            more_records_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
                'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})
            more_records = more_records + more_records_for_item

            print("more_records_for_item 2")

            print("docitem.item")
            print(docitem.item)
            print("previous stock ledger for item checking")
            previous_stock_ledger_name = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
                        , 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)

            print("previous stock ledger for item checked")

            print("more")
            print(more_records_for_item)

            # If any items in the collection has more records
            if(more_records_for_item>0):

                print("before append stock recalc record")

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
                print("before get stockc balance")
                stock_balance = frappe.get_value('Stock Balance', {'item':docitem.item, 'warehouse':docitem.warehouse}, ['name'] )
                print("after get stock balance")
                balance_qty =0
                balance_value =0
                valuation_rate  = 0

                if(previous_stock_ledger_name):
                    previous_stock_ledger = frappe.get_doc('Stock Ledger',previous_stock_ledger_name)
                    balance_qty = previous_stock_ledger.balance_qty
                    balance_value = previous_stock_ledger.balance_value
                    valuation_rate = previous_stock_ledger.valuation_rate

                stock_balance_for_item = frappe.get_doc('Stock Balance',stock_balance)
                # Add qty because of balance increasing due to cancellation of delivery note
                stock_balance_for_item.stock_qty = balance_qty
                stock_balance_for_item.stock_value = balance_value
                stock_balance_for_item.valuation_rate = valuation_rate
                stock_balance_for_item.save()
                # print("item_name")

                # item_name = frappe.get_value("Item", docitem.item,['item_name'])

                # print(item_name)

                update_stock_balance_in_item(docitem.item)


        print("before delete stock ledger")
        # Delete the stock ledger before recalculate, to avoid it to be recalculated again
        frappe.db.delete("Stock Ledger",
            {"voucher": "Sales Return",
                "voucher_no":self.name
            })

        if(more_records>0):
            stock_recalc_voucher.insert()
            print("going to recalculate")
            recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)

    def get_cost_of_goods_sold(self):

            cost_of_goods_sold_in_stock_ledgers_query = """select sum(qty_in*valuation_rate) as cost_of_goods_sold from `tabStock Ledger` where voucher='Sales Return' and voucher_no=%s"""

            cog_data = frappe.db.sql(cost_of_goods_sold_in_stock_ledgers_query,(self.name), as_dict = True)

            cost_of_goods_sold = 0

            if(cog_data):
                cost_of_goods_sold = cog_data[0].cost_of_goods_sold

            return cost_of_goods_sold

@frappe.whitelist()
def get_default_payment_mode():
    default_payment_mode = frappe.db.get_value('Company', filters={'name'},fieldname='default_payment_mode_for_sales')
    print(default_payment_mode)
    return default_payment_mode
