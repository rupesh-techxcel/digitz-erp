# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from datetime import datetime
from frappe.model.document import Document
from frappe.utils.data import now
from datetime import datetime, timedelta
from digitz_erp.api.stock_update import (
    recalculate_stock_ledgers,
    update_stock_balance_in_item,
)
from digitz_erp.api.document_posting_status_api import (
    init_document_posting_status,
    update_posting_status,
)
from frappe import throw, _
from digitz_erp.api.settings_api import add_seconds_to_time

class StockTransfer(Document):
    def validate(self):
        self.validate_items()

    def validate_items(self):
        items = set()  # Initialize an empty set to keep track of unique combinations

        for item in self.items:
            # Create a unique identifier by concatenating item, source_warehouse, and target_warehouse
            unique_id = f"{item.item}-{item.source_warehouse}-{item.target_warehouse}-{item.unit}"

            if unique_id in items:
                frappe.throw(
                    _("Item {0} from {1} to {2} is already added in the list").format(
                        item.item, item.source_warehouse, item.target_warehouse
                    )
                )

            items.add(unique_id)  # Add the unique identifier to the set for tracking

    def Voucher_In_The_Same_Time(self):
        possible_invalid = frappe.db.count(
            "Stock Transfer",
            {
                "posting_date": ["=", self.posting_date],
                "posting_time": ["=", self.posting_time],
            },
        )
        return possible_invalid
    
    def Set_Posting_Time_To_Next_Second(self):
		# Add 12 seconds to self.posting_time and update it
		self.posting_time = add_seconds_to_time(str(self.posting_time), seconds=12)


    def before_validate(self):

        if self.Voucher_In_The_Same_Time():

            self.Set_Posting_Time_To_Next_Second()

            if self.Voucher_In_The_Same_Time():
                self.Set_Posting_Time_To_Next_Second()

                if self.Voucher_In_The_Same_Time():
                    self.Set_Posting_Time_To_Next_Second()

                    if self.Voucher_In_The_Same_Time():
                        frappe.throw("Voucher with same time already exists.")

        for docitem in self.items:
            if not docitem.source_warehouse:
                docitem.source_warehouse = self.source_warehouse
            if not docitem.target_warehouse:
                docitem.target_warehouse = self.target_warehouse

    def on_submit(self):

        init_document_posting_status(self.doctype, self.name)
        self.do_postings_on_submit()

    def do_postings_on_submit(self):
        self.add_stock_transfer()
        update_posting_status(self.doctype, self.name, "posting_status", "Completed")

    def add_stock_transfer(self):
        stock_recalc_voucher_for_source = frappe.new_doc("Stock Recalculate Voucher")
        stock_recalc_voucher_for_source.voucher = "Stock Transfer"
        stock_recalc_voucher_for_source.voucher_no = self.name
        stock_recalc_voucher_for_source.voucher_date = self.posting_date
        stock_recalc_voucher_for_source.voucher_time = self.posting_time
        stock_recalc_voucher_for_source.status = "Not Started"
        stock_recalc_voucher_for_source.source_action = "Stock Transfer"

        stock_recalc_voucher_for_target = frappe.new_doc("Stock Recalculate Voucher")
        stock_recalc_voucher_for_target.voucher = "Stock Transfer"
        stock_recalc_voucher_for_target.voucher_no = self.name
        stock_recalc_voucher_for_target.voucher_date = self.posting_date
        stock_recalc_voucher_for_target.voucher_time = self.posting_time
        stock_recalc_voucher_for_target.status = "Not Started"
        stock_recalc_voucher_for_target.source_action = "Stock Transfer"

        more_records_for_source = 0
        more_records_for_target = 0

        default_company = frappe.db.get_single_value(
            "Global Settings", "default_company"
        )

        allow_negative_stock = frappe.get_value(
            "Company", default_company, ["allow_negative_stock"]
        )

        if not allow_negative_stock:
            allow_negative_stock = False

        posting_date_time = get_datetime(
            str(self.posting_date) + " " + str(self.posting_time)
        )
        for docitem in self.items:
            maintain_stock = frappe.db.get_value("Item", docitem.item, "maintain_stock")

            if maintain_stock == 1:

                more_records_count_for_item_for_source = frappe.db.count(
                    "Stock Ledger",
                    {
                        "item": docitem.item,
                        "warehouse": docitem.source_warehouse,
                        "posting_date": [">", posting_date_time],
                    },
                )

                more_records_for_source = (
                    more_records_for_source + more_records_count_for_item_for_source
                )

                required_qty = docitem.qty_in_base_unit

                previous_stock_valuation_rate = frappe.db.get_value(
                    "Stock Ledger",
                    {
                        "item": ["=", docitem.item],
                        "posting_date": ["<", posting_date_time],
                    },
                    ["valuation_rate"],
                    order_by="posting_date desc",
                    as_dict=True,
                )

                previous_stock_balance_in_source = frappe.db.get_value(
                    "Stock Ledger",
                    {
                        "item": ["=", docitem.item],
                        "warehouse": ["=", docitem.source_warehouse],
                        "posting_date": ["<", posting_date_time],
                    },
                    ["name", "balance_qty", "balance_value", "valuation_rate"],
                    order_by="posting_date desc",
                    as_dict=True,
                )

                if (
                    not previous_stock_balance_in_source
                    and allow_negative_stock == False
                ):
                    frappe.throw("No stock exists for " + docitem.item)

                if (
                    previous_stock_balance_in_source
                    and previous_stock_balance_in_source.balance_qty < required_qty
                    and allow_negative_stock == False
                ):
                    frappe.throw(
                        "Sufficient qty does not exist for the item "
                        + docitem.item
                        + " Required Qty= "
                        + str(required_qty)
                        + " "
                        + docitem.base_unit
                        + "and available Qty= "
                        + str(previous_stock_balance_in_source.balance_qty)
                        + " "
                        + docitem.base_unit
                    )
                    return

                change_in_stock_value = 0
                new_balance_qty = 0
                valuation_rate = 0
                new_balance_value = 0

                if not previous_stock_balance_in_source:
                    new_balance_qty = new_balance_qty * -1
                    valuation_rate = docitem.rate
                    new_balance_value = new_balance_qty * valuation_rate
                    change_in_stock_value = new_balance_value
                else:
                    new_balance_qty = (
                        previous_stock_balance_in_source.balance_qty
                        - docitem.qty_in_base_unit
                    )
                    valuation_rate = previous_stock_balance_in_source.valuation_rate
                    new_balance_value = new_balance_qty * valuation_rate
                    change_in_stock_value = (
                        new_balance_value
                        - previous_stock_balance_in_source.balance_value
                    )

                new_stock_ledger_source = frappe.new_doc("Stock Ledger")
                new_stock_ledger_source.item = docitem.item
                new_stock_ledger_source.item_name = docitem.item_name
                new_stock_ledger_source.warehouse = docitem.source_warehouse
                new_stock_ledger_source.posting_date = posting_date_time

                new_stock_ledger_source.qty_out = docitem.qty_in_base_unit
                new_stock_ledger_source.outgoing_rate = docitem.rate_in_base_unit
                new_stock_ledger_source.unit = docitem.base_unit
                new_stock_ledger_source.valuation_rate = valuation_rate
                new_stock_ledger_source.balance_qty = new_balance_qty
                new_stock_ledger_source.balance_value = new_balance_value
                new_stock_ledger_source.voucher = "Stock Transfer"
                new_stock_ledger_source.voucher_no = self.name
                new_stock_ledger_source.source = "Stock Transfer Item"
                new_stock_ledger_source.source_document_id = docitem.name
                new_stock_ledger_source.change_in_stock_value = change_in_stock_value
                new_stock_ledger_source.more_records = (
                    more_records_count_for_item_for_source > 0
                )
                new_stock_ledger_source.more_records_for_item = (
                    more_records_count_for_item_for_source
                )
                new_stock_ledger_source.insert()

                if more_records_count_for_item_for_source > 0:
                    stock_recalc_voucher_for_source.append(
                        "records",
                        {
                            "item": docitem.item,
                            "warehouse": docitem.source_warehouse,
                            "base_stock_ledger": new_stock_ledger_source.name,
                        },
                    )
                else:
                    if frappe.db.exists(
                        "Stock Balance",
                        {"item": docitem.item, "warehouse": docitem.source_warehouse},
                    ):
                        frappe.db.delete(
                            "Stock Balance",
                            {
                                "item": docitem.item,
                                "warehouse": docitem.source_warehouse,
                            },
                        )

                    new_stock_balance = frappe.new_doc("Stock Balance")
                    new_stock_balance.item = docitem.item
                    new_stock_balance.unit = docitem.base_unit
                    new_stock_balance.warehouse = docitem.source_warehouse
                    new_stock_balance.stock_qty = new_balance_qty
                    new_stock_balance.stock_value = new_balance_value
                    new_stock_balance.valuation_rate = valuation_rate

                    new_stock_balance.insert()

                    update_stock_balance_in_item(docitem.item)

                more_records_count_for_item_for_target = frappe.db.count(
                    "Stock Ledger",
                    {
                        "item": docitem.item,
                        "warehouse": docitem.target_warehouse,
                        "posting_date": [">", posting_date_time],
                    },
                )

                more_records_for_target = (
                    more_records_for_target + more_records_count_for_item_for_target
                )

                previous_stock_balance_in_target = frappe.db.get_value(
                    "Stock Ledger",
                    {
                        "item": ["=", docitem.item],
                        "warehouse": ["=", docitem.target_warehouse],
                        "posting_date": ["<", posting_date_time],
                    },
                    ["name", "balance_qty", "balance_value", "valuation_rate"],
                    order_by="posting_date desc",
                    as_dict=True,
                )

                preivous_balance_qty = 0
                previous_balance_value = 0

                if previous_stock_balance_in_target:
                    preivous_balance_qty = previous_stock_balance_in_target.balance_qty
                    previous_balance_value = (
                        previous_stock_balance_in_target.balance_value
                    )
                    valuation_rate = previous_stock_balance_in_target.valuation_rate

                new_balance_qty = preivous_balance_qty + docitem.qty_in_base_unit

                new_balance_value = new_balance_qty * valuation_rate

                change_in_stock_value = new_balance_value - previous_balance_value

                new_stock_ledger_target = frappe.new_doc("Stock Ledger")
                new_stock_ledger_target.item = docitem.item
                new_stock_ledger_target.item_name = docitem.item_name
                new_stock_ledger_target.warehouse = docitem.target_warehouse
                new_stock_ledger_target.posting_date = posting_date_time

                new_stock_ledger_target.qty_in = docitem.qty_in_base_unit
                new_stock_ledger_target.incoming_rate = docitem.rate_in_base_unit
                new_stock_ledger_target.unit = docitem.base_unit
                new_stock_ledger_target.valuation_rate = valuation_rate
                new_stock_ledger_target.balance_qty = new_balance_qty
                new_stock_ledger_target.balance_value = new_balance_value
                new_stock_ledger_target.change_in_stock_value = change_in_stock_value
                new_stock_ledger_target.voucher = "Stock Transfer"
                new_stock_ledger_target.voucher_no = self.name
                new_stock_ledger_target.source = "Stock Transfer Item"
                new_stock_ledger_target.source_document_id = docitem.name
                new_stock_ledger_target.more_records = (
                    more_records_count_for_item_for_target > 0
                )
                new_stock_ledger_target.more_records_for_item = (
                    more_records_count_for_item_for_target
                )
                new_stock_ledger_target.insert()

                if more_records_count_for_item_for_target > 0:
                    stock_recalc_voucher_for_target.append(
                        "records",
                        {
                            "item": docitem.item,
                            "warehouse": docitem.target_warehouse,
                            "base_stock_ledger": new_stock_ledger_target.name,
                        },
                    )
                else:
                    if frappe.db.exists(
                        "Stock Balance",
                        {"item": docitem.item, "warehouse": docitem.target_warehouse},
                    ):
                        frappe.db.delete(
                            "Stock Balance",
                            {
                                "item": docitem.item,
                                "warehouse": docitem.target_warehouse,
                            },
                        )

                    new_stock_balance = frappe.new_doc("Stock Balance")
                    new_stock_balance.item = docitem.item
                    new_stock_balance.item_name = docitem.item_name
                    new_stock_balance.unit = docitem.base_unit
                    new_stock_balance.warehouse = docitem.target_warehouse
                    new_stock_balance.stock_qty = new_balance_qty
                    new_stock_balance.stock_value = new_balance_value
                    new_stock_balance.valuation_rate = valuation_rate

                    new_stock_balance.insert()

                    update_stock_balance_in_item(docitem.item)

        update_posting_status(self.doctype, self.name, "stock_posted_time")

        if more_records_for_source > 0:
            update_posting_status(
                self.doctype, self.name, "stock_recalc_required", True
            )
            stock_recalc_voucher_for_source.insert()
            recalculate_stock_ledgers(
                stock_recalc_voucher_for_source, self.posting_date, self.posting_time
            )
            update_posting_status(self.doctype, self.name, "stock_reclc_time")

        if more_records_for_target > 0:
            update_posting_status(
                self.doctype, self.name, "stock_recalc_required", True
            )
            stock_recalc_voucher_for_target.insert()
            recalculate_stock_ledgers(
                stock_recalc_voucher_for_target, self.posting_date, self.posting_time
            )
            update_posting_status(self.doctype, self.name, "stock_reclc_time")

    def on_cancel(self):

        update_posting_status(
            self.doctype, self.name, "posting_status", "Cancel Pending"
        )

        turn_off_background_job = frappe.db.get_single_value(
            "Global Settings", "turn_off_background_job"
        )

        self.cancel_stock_transfer()

    def cancel_stock_transfer(self):

        self.do_cancel_stock_transfer()
        update_posting_status(self.doctype, self.name, "posting_status", "Completed")

    def do_cancel_stock_transfer(self):

        stock_recalc_voucher_source_wh = frappe.new_doc("Stock Recalculate Voucher")
        stock_recalc_voucher_source_wh.voucher = "Stock Transfer"
        stock_recalc_voucher_source_wh.voucher_no = self.name
        stock_recalc_voucher_source_wh.voucher_date = self.posting_date
        stock_recalc_voucher_source_wh.voucher_time = self.posting_time
        stock_recalc_voucher_source_wh.status = "Not Started"
        stock_recalc_voucher_source_wh.source_action = "Cancel"

        stock_recalc_voucher_target_wh = frappe.new_doc("Stock Recalculate Voucher")
        stock_recalc_voucher_target_wh.voucher = "Stock Transfer"
        stock_recalc_voucher_target_wh.voucher_no = self.name
        stock_recalc_voucher_target_wh.voucher_date = self.posting_date
        stock_recalc_voucher_target_wh.voucher_time = self.posting_time
        stock_recalc_voucher_target_wh.status = "Not Started"
        stock_recalc_voucher_target_wh.source_action = "Cancel"

        posting_date_time = get_datetime(
            str(self.posting_date) + " " + str(self.posting_time)
        )

        more_records_source_wh = 0
        more_records_target_wh = 0

        for docitem in self.items:
            more_records_for_item_source_wh = frappe.db.count(
                "Stock Ledger",
                {
                    "item": docitem.item,
                    "warehouse": docitem.source_warehouse,
                    "posting_date": [">", posting_date_time],
                },
            )

            more_records_source_wh = (
                more_records_source_wh + more_records_for_item_source_wh
            )

            previous_stock_ledger_name_source = frappe.db.get_value(
                "Stock Ledger",
                {
                    "item": ["=", docitem.item],
                    "warehouse": ["=", docitem.source_warehouse],
                    "posting_date": ["<", posting_date_time],
                },
                ["name"],
                order_by="posting_date desc",
                as_dict=True,
            )

            if more_records_for_item_source_wh > 0:

                if previous_stock_ledger_name_source:
                    stock_recalc_voucher_source_wh.append(
                        "records",
                        {
                            "item": docitem.item,
                            "warehouse": docitem.source_warehouse,
                            "base_stock_ledger": previous_stock_ledger_name_source,
                        },
                    )
                else:
                    stock_recalc_voucher_source_wh.append(
                        "records",
                        {
                            "item": docitem.item,
                            "warehouse": docitem.source_warehouse,
                            "base_stock_ledger": "No Previous Ledger",
                        },
                    )
            else:

                balance_qty = 0
                balance_value = 0
                valuation_rate = 0

                if previous_stock_ledger_name_source:
                    previous_stock_ledger = frappe.get_doc(
                        "Stock Ledger", previous_stock_ledger_name_source
                    )
                    balance_qty = previous_stock_ledger.balance_qty
                    balance_value = previous_stock_ledger.balance_value
                    valuation_rate = previous_stock_ledger.valuation_rate

                if frappe.db.exists(
                    "Stock Balance",
                    {"item": docitem.item, "warehouse": docitem.source_warehouse},
                ):
                    frappe.db.delete(
                        "Stock Balance",
                        {"item": docitem.item, "warehouse": docitem.source_warehouse},
                    )

                unit = frappe.get_value("Item", docitem.item, ["base_unit"])
                stock_balance_for_item = frappe.new_doc("Stock Balance")
                stock_balance_for_item.item = docitem.item
                stock_balance_for_item.unit = unit
                stock_balance_for_item.warehouse = docitem.source_warehouse
                stock_balance_for_item.stock_qty = balance_qty
                stock_balance_for_item.stock_value = balance_value
                stock_balance_for_item.valuation_rate = valuation_rate
                stock_balance_for_item.insert()

                update_stock_balance_in_item(docitem.item)

            # Target warehouse posting
            more_records_for_item_target_wh = frappe.db.count(
                "Stock Ledger",
                {
                    "item": docitem.item,
                    "warehouse": docitem.target_warehouse,
                    "posting_date": [">", posting_date_time],
                },
            )

            more_records_target_wh = (
                more_records_target_wh + more_records_for_item_target_wh
            )

            previous_stock_ledger_name_target = frappe.db.get_value(
                "Stock Ledger",
                {
                    "item": ["=", docitem.item],
                    "warehouse": ["=", docitem.target_warehouse],
                    "posting_date": ["<", posting_date_time],
                },
                ["name"],
                order_by="posting_date desc",
                as_dict=True,
            )

            if more_records_for_item_target_wh > 0:

                if previous_stock_ledger_name_target:
                    stock_recalc_voucher_target_wh.append(
                        "records",
                        {
                            "item": docitem.item,
                            "warehouse": docitem.target_warehouse,
                            "base_stock_ledger": previous_stock_ledger_name_target,
                        },
                    )
                else:
                    stock_recalc_voucher_target_wh.append(
                        "records",
                        {
                            "item": docitem.item,
                            "warehouse": docitem.target_warehouse,
                            "base_stock_ledger": "No Previous Ledger",
                        },
                    )
            else:

                balance_qty = 0
                balance_value = 0
                valuation_rate = 0

                if previous_stock_ledger_name_target:
                    previous_stock_ledger = frappe.get_doc(
                        "Stock Ledger", previous_stock_ledger_name_target
                    )
                    balance_qty = previous_stock_ledger.balance_qty
                    balance_value = previous_stock_ledger.balance_value
                    valuation_rate = previous_stock_ledger.valuation_rate

                if frappe.db.exists(
                    "Stock Balance",
                    {"item": docitem.item, "warehouse": docitem.target_warehouse},
                ):
                    frappe.db.delete(
                        "Stock Balance",
                        {"item": docitem.item, "warehouse": docitem.target_warehouse},
                    )

                unit = frappe.get_value("Item", docitem.item, ["base_unit"])
                stock_balance_for_item = frappe.new_doc("Stock Balance")
                stock_balance_for_item.item = docitem.item
                stock_balance_for_item.unit = unit
                stock_balance_for_item.warehouse = docitem.target_warehouse
                stock_balance_for_item.stock_qty = balance_qty
                stock_balance_for_item.stock_value = balance_value
                stock_balance_for_item.valuation_rate = valuation_rate
                stock_balance_for_item.insert()

                update_stock_balance_in_item(docitem.item)

        update_posting_status(self.doctype, self.name, "stock_posted_on_cancel_time")

        if more_records_source_wh > 0:
            update_posting_status(
                self.doctype, self.name, "stock_recalc_required_on_cancel", True
            )
            stock_recalc_voucher_source_wh.insert()
            recalculate_stock_ledgers(
                stock_recalc_voucher_source_wh, self.posting_date, self.posting_time
            )
            update_posting_status(
                self.doctype, self.name, "stock_recalc_on_cancel_time"
            )

        if more_records_target_wh > 0:
            update_posting_status(
                self.doctype, self.name, "stock_recalc_required_on_cancel", True
            )
            stock_recalc_voucher_target_wh.insert()
            recalculate_stock_ledgers(
                stock_recalc_voucher_target_wh, self.posting_date, self.posting_time
            )
            update_posting_status(
                self.doctype, self.name, "stock_recalc_on_cancel_time"
            )

        frappe.db.delete(
            "Stock Ledger", {"voucher": "Stock Transfer", "voucher_no": self.name}
        )
