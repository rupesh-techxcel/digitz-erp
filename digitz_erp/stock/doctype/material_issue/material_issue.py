# Copyright (c) 2024, Rupesh P and contributors
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


class MaterialIssue(Document):
    def validate(self):
        self.validate_items()

    def validate_items(self):
        items = set()  # Initialize an empty set to keep track of unique combinations

        for item in self.items:
            # Create a unique identifier by concatenating item, warehouse, and project
            unique_id = (
                f"{item.item}-{item.warehouse}-{item.project}-{item.unit}"
            )

            if unique_id in items:
                frappe.throw(
                    _("Item {0} from {1} to {2} is already added in the list").format(
                        item.item, item.warehouse, item.project
                    )
                )

            items.add(unique_id)  # Add the unique identifier to the set for tracking



    def Voucher_In_The_Same_Time(self):
        possible_invalid = frappe.db.count(
            "Material Issue",
            {
                "posting_date": ["=", self.posting_date],
                "posting_time": ["=", self.posting_time],
            },
        )
        return possible_invalid

    def Set_Posting_Time_To_Next_Second(self):
        datetime_object = datetime.strptime(str(self.posting_time), "%H:%M:%S")

        # Add one second to the datetime object
        new_datetime = datetime_object + timedelta(seconds=1)

        # Extract the new time as a string
        self.posting_time = new_datetime.strftime("%H:%M:%S")



    def on_submit(self):
        for row in self.items:
            item_code = row.item
            warehouse = row.warehouse
            qty = row.qty  # Quantity to be deducted
            rate = row.rate
            unit = row.base_unit

            # Fetch the current stock balance
            stock_balance = frappe.db.get_value("Stock Balance", {
                'item': item_code,
                'warehouse': warehouse
            }, ['stock_qty', 'stock_value'])

            if stock_balance:
                current_qty, current_value = stock_balance
                
                # Calculate new stock quantity and value
                new_qty = current_qty - qty
                new_value = current_value - (qty * rate)

                # Update stock balance
                frappe.db.sql("""
                    UPDATE `tabStock Balance`
                    SET stock_qty = %(new_qty)s,
                        stock_value = %(new_value)s
                    WHERE item = %(item)s AND warehouse = %(warehouse)s
                """, {
                    'new_qty': new_qty,
                    'new_value': new_value,
                    'item': item_code,
                    'warehouse': warehouse
                })

                # Create a new Project Stock Ledger entry
                doc = frappe.new_doc("Project Stock Ledger")
                doc.item = item_code
                doc.item_name = row.item_name
                posting_date = datetime.strptime(self.posting_date, '%Y-%m-%d').date()
                posting_time = datetime.strptime(self.posting_time, '%H:%M:%S').time()
                combined_datetime = datetime.combine(posting_date, posting_time)
                doc.posting_date = combined_datetime
                doc.warehouse = warehouse
                doc.project = self.project
                doc.incoming_rate = rate
                doc.valuation_rate = rate
                doc.consumed_qty = row.qty
                doc.balance_qty = new_qty  # Record as a negative quantity to reflect issuance
                doc.balance_value = doc.incoming_rate * doc.balance_qty
                doc.change_in_stock_value = doc.consumed_qty * doc.incoming_rate
                doc.unit = unit
                doc.voucher = "Material Issue"
                doc.voucher_no = self.name
                doc.source = "Material Issue Item"
                doc.source_document_id = row.name
                doc.save()

                # Create a new Stock Ledger entry
                stock_ledger = frappe.new_doc("Stock Ledger")
                stock_ledger.item = item_code
                stock_ledger.item_name = row.item_name

                posting_date = datetime.strptime(self.posting_date, '%Y-%m-%d').date()
                posting_time = datetime.strptime(self.posting_time, '%H:%M:%S').time()
                combined_datetime = datetime.combine(posting_date, posting_time)
                
                stock_ledger.posting_date = combined_datetime
                stock_ledger.warehouse = warehouse
                stock_ledger.project = self.project
                stock_ledger.incoming_rate = rate
                stock_ledger.valuation_rate = rate
                stock_ledger.qty_out = row.qty
                stock_ledger.balance_qty = new_qty  # Record as a negative quantity to reflect issuance
                stock_ledger.balance_value = stock_ledger.incoming_rate * stock_ledger.balance_qty
                stock_ledger.change_in_stock_value = stock_ledger.qty_out * stock_ledger.incoming_rate
                stock_ledger.unit = unit
                stock_ledger.voucher = "Material Issue"
                stock_ledger.voucher_no = self.name
                stock_ledger.source = "Material Issue Item"
                stock_ledger.source_document_id = row.name
                stock_ledger.save()