# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from datetime import datetime, timedelta
from frappe.model.document import Document
from frappe.utils.data import now
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_stock_balance_in_item
from digitz_erp.api.document_posting_status_api import init_document_posting_status, reset_document_posting_status_for_recalc_after_submit, update_posting_status, reset_document_posting_status_for_recalc_after_cancel
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type
from digitz_erp.api.sales_order_api import check_and_update_sales_order_status,update_sales_order_quantities_on_update
class DeliveryNote(Document):

    def Voucher_In_The_Same_Time(self):
        possible_invalid= frappe.db.count('Delivery Note', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time], 'docstatus':['=', 1]})
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




    def validate(self):
        self.validate_item()
        # self.validate_item_valuation_rates()

    def on_cancel(self):

        update_posting_status(self.doctype,self.name,'posting_status','Cancel Pending')

        turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

        # if(frappe.session.user == "Administrator" and turn_off_background_job):
        #     self.cancel_delivery_note()
        # else:
            # frappe.enqueue(self.cancel_delivery_note, queue="long")
            # frappe.msgprint("The relevant postings for this document are happening in the background. Changes may take a few seconds to reflect.", alert= True)
        self.cancel_delivery_note()
        
        
    def on_update(self):
        
        update_sales_order_quantities_on_update(self)        
        check_and_update_sales_order_status(self.name, "Sales Invoice")

    def on_submit(self):

        init_document_posting_status(self.doctype,self.name)
        turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

        # if(frappe.session.user == "Administrator" and turn_off_background_job):
        #     self.do_postings_on_submit()
        # else:
            # frappe.enqueue(self.do_postings_on_submit, queue="long")
            # frappe.msgprint("The relevant postings for this document are happening in the background. Changes may take a few seconds to reflect.", alert= True)
        self.do_postings_on_submit()


    def do_postings_on_submit(self):

        self.do_stock_posting()
        self.insert_gl_records()

        update_accounts_for_doc_type('Delivery Note',self.name)

        update_posting_status(self.doctype, self.name,'posting_status', 'Completed')

    def validate_item(self):

        print("DN validate item")

        posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))

        default_company = frappe.db.get_single_value("Global Settings", "default_company")

        company_info = frappe.get_value("Company",default_company,['allow_negative_stock'], as_dict = True)

        allow_negative_stock = company_info.allow_negative_stock

        if not allow_negative_stock:
            allow_negative_stock = False

        if allow_negative_stock == False:
            for docitem in self.items:
                # previous_stocks = frappe.db.get_value('Stock Ledger', {'item':docitem.item,'warehouse': docitem.warehouse , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],order_by='posting_date desc', as_dict=True)

                previous_stock_balance = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
                , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
                order_by='posting_date desc', as_dict=True)

                if(not previous_stock_balance):
                    frappe.throw("No stock exists for" + docitem.item )

                if(previous_stock_balance.balance_qty< docitem.qty_in_base_unit):
                    frappe.throw("Sufficiant qty does not exists for the item " + docitem.item + " required Qty= " + str(docitem.qty_in_base_unit) +
                    " " + docitem.base_unit + " and available Qty=" + str(previous_stock_balance.balance_qty) + " " + docitem.base_unit )

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

    @frappe.whitelist()
    def generate_sale_invoice(self):
        sales_invoice_name = ""

        deliveryNoteName =  self.name
        sales_invoice = self.__dict__
        sales_invoice['doctype'] = 'Sales Invoice'
        sales_invoice['name'] = sales_invoice_name
        sales_invoice['naming_series'] = ""
        sales_invoice['posting_date'] = self.posting_date
        sales_invoice['posting_time'] = self.posting_time
        sales_invoice['delivery_note'] =deliveryNoteName
        # Change the document status to draft to avoid error while submitting child table
        sales_invoice['docstatus'] = 0
        for item in sales_invoice['items']:
            item.doctype = "Sales Invoice Item"
            item.delivery_note_item_reference_no = item.name
            item._meta = ""

        sales_invoice_doc = frappe.get_doc(
            sales_invoice).insert(ignore_permissions=True)

        frappe.db.commit()

        print(sales_invoice_doc.name)

        si =  frappe.get_doc('Sales Invoice',sales_invoice_doc.name)

        # Add reference link to the 'Sales Invoice Delivery NOtes' child doctype

        si.append('delivery_notes', {'delivery_note': deliveryNoteName})

        # si.docstatus = 1

        si.save()

        frappe.msgprint("Sales Invoice created successfully, in draft mode.", alert=True)

    @frappe.whitelist()
    def do_test_do_script(self):
        frappe.msgprint("hello")

    @frappe.whitelist()
    def do_stock_re_posting(self):

        if(self.docstatus==1):
            # frappe.enqueue(self.do_stock_posting,recalculate_after_submit=True, queue="long")
            self.do_stock_posting()
        elif(self.docstatus == 2):
            self.do_stock_posting_on_cancel()

    def cancel_delivery_note(self):
        self.do_cancel_delivery_note()
        update_posting_status(self.doctype, self.name, 'posting_status', 'Completed')

    def do_cancel_delivery_note(self):

        self.do_stock_posting_on_cancel()

        frappe.db.delete("Stock Ledger",
            {"voucher": "Delivery Note",
                "voucher_no":self.name
            })

        delete_gl_postings_for_cancel_doc_type('Delivery Note', self.name)

        # frappe.db.delete("GL Posting",
		# 		{"Voucher_type": "Delivery Note",
		# 		 "voucher_no":self.name
		# 		})

    def do_stock_posting(self):

        stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
        stock_recalc_voucher.voucher = 'Delivery Note'
        stock_recalc_voucher.voucher_no = self.name
        stock_recalc_voucher.voucher_date = self.posting_date
        stock_recalc_voucher.voucher_time = self.posting_time
        stock_recalc_voucher.status = 'Not Started'
        stock_recalc_voucher.source_action = "Insert"

        cost_of_goods_sold = 0

        more_records = 0

        # Create a dictionary for handling duplicate items. In stock ledger posting it is expected to have only one stock ledger per item per voucher.
        item_stock_ledger = {}

        for docitem in self.items:
            maintain_stock = frappe.db.get_value('Item', docitem.item , 'maintain_stock')
            print('MAINTAIN STOCK :', maintain_stock)
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

                # if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
                #     frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse})

                change_in_stock_value = new_balance_value - previous_stock_balance_value

                new_stock_ledger = None

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
                    new_stock_ledger.voucher = "Delivery Note"
                    new_stock_ledger.voucher_no = self.name
                    new_stock_ledger.source = "Delivery Note Item"
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
                    new_stock_balance.unit = unit
                    new_stock_balance.warehouse = docitem.warehouse
                    new_stock_balance.stock_qty = new_balance_qty
                    new_stock_balance.stock_value = new_balance_value
                    new_stock_balance.valuation_rate = valuation_rate

                    new_stock_balance.insert()

                    # item_name = frappe.get_value("Item", docitem.item,['item_name'])
                    # print("item_name")
                    # print(item_name)
                    update_stock_balance_in_item(docitem.item)
                else:
                    stock_recalc_voucher.append('records',{'item': docitem.item,
                                                            'item_name': docitem.item_name,
                                                                'warehouse': docitem.warehouse,
                                                                'base_stock_ledger': new_stock_ledger.name
                                                                })


        update_posting_status(self.doctype,self.name, 'stock_posted_time')

        if(more_records>0):

            update_posting_status(self.doctype,self.name, 'stock_recalc_required', True)

            stock_recalc_voucher.insert()
            recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)


            update_posting_status(self.doctype, self.name, 'stock_recalc_time')

    def get_cost_of_goods_sold(self):

        cost_of_goods_sold_in_stock_ledgers_query = """select sum(qty_out*valuation_rate) as cost_of_goods_sold from `tabStock Ledger` where voucher='Delivery Note' and voucher_no=%s"""

        cog_data = frappe.db.sql(cost_of_goods_sold_in_stock_ledgers_query,(self.name), as_dict = True)

        cost_of_goods_sold = 0

        if(cog_data):
            cost_of_goods_sold = cog_data[0].cost_of_goods_sold

        return cost_of_goods_sold

    def insert_gl_records(self):

        print("From insert gl records")

        default_company = frappe.db.get_single_value("Global Settings", "default_company")

        default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account', 'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)

        idx = 1

        cost_of_goods_sold = self.get_cost_of_goods_sold()

        # Inventory account - Credit - Against Cost Of Goods Sold
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Delivery Note"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.default_inventory_account
        gl_doc.credit_amount = cost_of_goods_sold
        gl_doc.against_account = default_accounts.cost_of_goods_sold_account
        gl_doc.is_for_cogs = True
        gl_doc.insert()

        # Cost Of Goods Sold - Debit - Against Inventory
        idx = 2
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Delivery Note"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.cost_of_goods_sold_account
        gl_doc.debit_amount = cost_of_goods_sold
        gl_doc.against_account = default_accounts.default_inventory_account
        gl_doc.is_for_cogs = True
        gl_doc.insert()

        update_posting_status(self.doctype,self.name, 'gl_posted_time')

    def do_stock_posting_on_cancel(self):

        # Insert record to 'Stock Recalculate Voucher' doc
        stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')

        stock_recalc_voucher.voucher = 'Delivery Note'
        stock_recalc_voucher.voucher_no = self.name
        stock_recalc_voucher.voucher_date = self.posting_date
        stock_recalc_voucher.voucher_time = self.posting_time
        stock_recalc_voucher.status = 'Not Started'
        stock_recalc_voucher.source_action = "Cancel"

        posting_date_time =  get_datetime(str(self.posting_date) + " " + str(self.posting_time))

        more_records = 0

        for docitem in self.items:

            # For cancel delivery note balance qty logic is safe because it only add the qty back to the stock.
            more_record_for_item = frappe.db.count('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
                , 'posting_date':['>', posting_date_time]})

            more_records = more_records + more_record_for_item

            previous_stock_ledger_name = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
                , 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)

            if(more_record_for_item == 0):

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
                update_stock_balance_in_item(docitem.item)


            else:
                if previous_stock_ledger_name:
                # Previous stock ledger assigned to base stock ledger
                    stock_recalc_voucher.append('records',{'item': docitem.item,
                                                            'warehouse': docitem.warehouse,
                                                            'base_stock_ledger': previous_stock_ledger_name
                                                            })
                else:
                    stock_recalc_voucher.append('records',{'item': docitem.item,
                                                            'warehouse': docitem.warehouse,
                                                            'base_stock_ledger': "No Previous Ledger"
                                                            })


        update_posting_status(self.doctype, self.name, 'stock_posted_on_cancel_time')


        if more_records:
            update_posting_status(self.doctype,self.name, 'stock_recalc_required_on_cancel', True)
            stock_recalc_voucher.insert()
            recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)
            update_posting_status(self.doctype,self.name, 'stock_recalc_on_cancel_time')


@frappe.whitelist()
def get_sales_order_items(sales_orders):
    if isinstance(sales_orders, str):
        sales_orders = frappe.parse_json(sales_orders)
    items = []
    for sales_order in sales_orders:
        sales_order_items = frappe.get_all('Sales Order Item',
                                           filters={'parent': sales_order},
                                           fields=['name', 'item', 'qty', 'warehouse', 'item_name', 'display_name', 'unit', 'rate', 'base_unit',
                                           'qty_in_base_unit', 'rate_in_base_unit', 'conversion_factor', 'rate_includes_tax', 'gross_amount',
                                           'tax_excluded', 'tax_rate', 'tax_amount', 'discount_percentage', 'discount_amount', 'net_amount'
                                           ])
        for so_item in sales_order_items:
            so_item['sales_order_item_reference_no'] = so_item['name']
            items.append(so_item)

    return items

@frappe.whitelist()
def get_gl_postings(delivery_note):
    gl_postings = frappe.get_all("GL Posting",
                                  filters={"voucher_no": delivery_note},
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
def get_stock_ledgers(delivery_note):
    stock_ledgers = frappe.get_all("Stock Ledger",
                                    filters={"voucher_no": delivery_note},
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
