# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils import now
from frappe.model.document import Document
from digitz_erp.utils import *
from frappe.model.mapper import *
class SalesReturn(Document):
    def before_submit(self):
        cost_of_goods_sold = 0

        self.insert_gl_records(cost_of_goods_sold)
        self.insert_payment_postings()

    def insert_gl_records(self, cost_of_goods_sold):
        default_company = frappe.db.get_single_value(
            "Global Settings", "default_company")
        default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                         'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)
        idx = 1
        # Trade Receivable - Debit
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
        gl_doc.aginst_account = default_accounts.default_income_account
        gl_doc.insert()

        # Income account - Credot
        idx = 2
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Sales Return"
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
        gl_doc.voucher_type = "Sales Return"
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
            gl_doc.voucher_type = "Sales Return"
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
        if self.tab_sales:
            default_company = frappe.db.get_single_value("Global Settings", "default_company")
            default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                         'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)

            idx = idx + 1

            # Inventory account Eg: Stock In Hand
            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Sales Return"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = default_accounts.default_inventory_account
            gl_doc.debit_amount = cost_of_goods_sold
            gl_doc.party_type = "Customer"
            gl_doc.party = self.customer
            gl_doc.aginst_account = default_accounts.cost_of_goods_sold_account
            gl_doc.insert()

            # Cost Of Goods Sold
            idx = idx + 1
            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Sales Return"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = default_accounts.cost_of_goods_sold_account
            gl_doc.credit_amount = cost_of_goods_sold
            gl_doc.aginst_account = default_accounts.default_inventory_account
            gl_doc.insert()

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
            gl_doc.credit_amount = self.rounded_total
            gl_doc.party_type = "Customer"
            gl_doc.party = self.customer
            gl_doc.aginst_account = payment_mode.account
            gl_doc.insert()

            idx = idx + 1

            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Sales Return"
            gl_doc.voucher_no = self.name
            gl_doc.idx = idx
            gl_doc.posting_date = self.posting_date
            gl_doc.posting_time = self.posting_time
            gl_doc.account = payment_mode.account
            gl_doc.debit_amount = self.rounded_total
            gl_doc.aginst_account = default_accounts.default_receivable_account
            gl_doc.insert()


    def deduct_stock_for_tab_sales(self):
        stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
        stock_recalc_voucher.voucher = 'Sales Return'
        stock_recalc_voucher.voucher_no = self.name
        stock_recalc_voucher.voucher_date = self.posting_date
        stock_recalc_voucher.voucher_time = self.posting_time
        stock_recalc_voucher.status = 'Not Started'
        stock_recalc_voucher.source_action = "Insert"
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
            required_qty = docitem.qty_in_base_unit

            # Check available qty
            previous_stock_balance = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
            , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
            order_by='posting_date desc', as_dict=True)
            if(allow_negative_stock == False and not previous_stock_balance):
                frappe.throw("No stock exists for" + docitem.item )
                return
            if(allow_negative_stock == False and previous_stock_balance and previous_stock_balance.balance_qty < required_qty ):
                frappe.throw("Sufficiant qty does not exists for the item " + docitem.item + " Required Qty= " + str(required_qty) + " " +
                    docitem.base_unit + "and available Qty= " + str(previous_stock_balance.balance_qty) + " " + docitem.base_unit)
                return
            previous_stock_balance_value = 0

            if previous_stock_balance:
                new_balance_qty = previous_stock_balance.balance_qty - docitem.qty_in_base_unit
                valuation_rate = previous_stock_balance.valuation_rate
                previous_stock_balance_value = previous_stock_balance.balance_value
            else:
                new_balance_qty = 0 - docitem.qty_in_base_unit
                valuation_rate = frappe.get_value("Item", docitem.item, ['standard_buying_price'])

            new_balance_value = previous_stock_balance_value - (docitem.qty_in_base_unit * valuation_rate)
            cost_of_goods_sold = cost_of_goods_sold + (docitem.qty_in_base_unit * valuation_rate)

            if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
                frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse})

            change_in_stock_value = new_balance_value - previous_stock_balance_value
            new_stock_ledger = frappe.new_doc("Stock Ledger")
            new_stock_ledger.item = docitem.item
            new_stock_ledger.warehouse = docitem.warehouse
            new_stock_ledger.posting_date = posting_date_time

            new_stock_ledger.qty_out = docitem.qty_in_base_unit
            new_stock_ledger.outgoing_rate = docitem.rate_in_base_unit
            new_stock_ledger.unit = docitem.base_unit
            new_stock_ledger.valuation_rate = valuation_rate
            new_stock_ledger.balance_qty = new_balance_qty
            new_stock_ledger.balance_value = new_balance_value
            new_stock_ledger.change_in_stock_value = change_in_stock_value
            new_stock_ledger.voucher = "Sales Return"
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
                new_stock_balance.unit = unit
                new_stock_balance.warehouse = docitem.warehouse
                new_stock_balance.stock_qty = new_balance_qty
                new_stock_balance.stock_value = new_balance_value
                new_stock_balance.valuation_rate = valuation_rate

                new_stock_balance.insert()

                item_name = frappe.get_value("Item", docitem.item,['item_name'])
                update_item_stock_balance(item_name)
            else:
                stock_recalc_voucher.append('records',{'item': docitem.item,
                                                            'warehouse': docitem.warehouse,
                                                            'base_stock_ledger': new_stock_ledger.name
                                                            })
        if(more_records>0):
            stock_recalc_voucher.insert()
            recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)

        return cost_of_goods_sold
