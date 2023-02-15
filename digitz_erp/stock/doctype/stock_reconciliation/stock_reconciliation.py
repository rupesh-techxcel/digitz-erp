# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now
from frappe.model.document import Document


class StockReconciliation(Document):
    def before_submit(self):
        self.add_stock_for_purchase_receipt()

    def add_stock_for_purchase_receipt(self):

        more_records = 0

        for docitem in self.items:

            new_balance_qty = docitem.qty_in_base_unit
            # Default valuation rate
            valuation_rate = docitem.rate_in_base_unit

            posting_date_time = get_datetime(
                str(self.posting_date) + " " + str(self.posting_time))

            # Default balance value calculating withe the current row only
            new_balance_value = new_balance_qty * valuation_rate

            print(posting_date_time)

            # posting_date<= consider because to take the dates with in the same minute
            # dbCount = frappe.db.count('Stock Ledger',{'item_code': ['=', docitem.item_code],'warehouse':['=', docitem.warehouse], 'posting_date':['<=', posting_date_time]})
            dbCount = frappe.db.count('Stock Ledger', {'item_code': ['=', docitem.item_code], 'warehouse': [
                                      '=', docitem.warehouse], 'posting_date': ['<', posting_date_time]})

            if (dbCount > 0):

                # Find out the balance value and valuation rate. Here recalculates the total balance value and valuation rate
                # from the balance qty in the existing rows x actual incoming rate

                last_stock_ledger = frappe.db.get_value('Stock Ledger', {'item_code': ['=', docitem.item_code], 'warehouse': ['=', docitem.warehouse], 'posting_date': [
                                                        '<', posting_date_time]}, ['balance_qty', 'balance_value', 'valuation_rate'], order_by='posting_date desc', as_dict=True)
                new_balance_qty = new_balance_qty + last_stock_ledger.balance_qty

                new_balance_value = new_balance_value + \
                    (last_stock_ledger.balance_value)

                valuation_rate = new_balance_value/new_balance_qty

            new_stock_ledger = frappe.new_doc("Stock Ledger")
            new_stock_ledger.item = docitem.item
            new_stock_ledger.warehouse = docitem.warehouse
            new_stock_ledger.posting_date = posting_date_time

            new_stock_ledger.qty_in = docitem.qty_in_base_unit if new_balance_qty > docitem.qty_in_base_unit else 0
            new_stock_ledger.qty_out = docitem.qty_in_base_unit if new_balance_qty < docitem.qty_in_base_unit else 0
            new_stock_ledger.incoming_rate = docitem.rate_in_base_unit
            new_stock_ledger.unit = docitem.base_unit
            new_stock_ledger.valuation_rate = valuation_rate
            new_stock_ledger.balance_qty = new_balance_qty
            new_stock_ledger.balance_value = new_balance_value
            new_stock_ledger.voucher = "Purchase Invoice"
            new_stock_ledger.voucher_no = ""
            new_stock_ledger.source = "Purchase Invoice Item"
            new_stock_ledger.source_document_id = ""
            new_stock_ledger.insert()

            # Find out subsequent records to recalculate and update the balances
            if frappe.db.exists('Stock Balance', {'item': docitem.item, 'warehouse': docitem.warehouse}):
                frappe.db.delete('Stock Balance', {
                                 'item': docitem.item, 'warehouse': docitem.warehouse})

            new_stock_balance = frappe.new_doc('Stock Balance')
            new_stock_balance.item = docitem.item
            new_stock_balance.unit = docitem.unit
            new_stock_balance.warehouse = docitem.warehouse
            new_stock_balance.stock_qty = new_balance_qty
            new_stock_balance.stock_value = new_balance_value
            new_stock_balance.valuation_rate = valuation_rate

            new_stock_balance.insert()

            item = frappe.get_doc('Item', docitem.item)
            item.stock_balance = item.stock_balance + docitem.qty_in_base_unit
            item.save()

            # For back dated purchase invoice
            more_records_count = frappe.db.count('Stock Ledger', {'item': docitem.item,
                                                                  'warehouse': docitem.warehouse, 'posting_date': ['>', posting_date_time]})

            more_records = more_records + more_records_count

        if (more_records > 0):
            self.recalculate_stock_ledgers("Add", new_stock_ledger.name)
