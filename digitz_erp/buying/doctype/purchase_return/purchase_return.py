# Copyright (c) 2022, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now
from frappe.model.document import Document
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_stock_balance_in_item
from frappe.model.mapper import *
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type
from digitz_erp.api.bank_reconciliation_api import create_bank_reconciliation, cancel_bank_reconciliation

class PurchaseReturn(Document):

	def validate(self):
		self.validate_purchase()
		self.validate_stock()

	def validate_purchase(self):

		for docitem in self.items:
			if(docitem.pi_item_reference):

				pi = frappe.get_doc("Purchase Invoice Item", docitem.pi_item_reference)

				total_returned_qty_not_in_this_pr = frappe.db.sql(""" SELECT SUM(qty) as total_returned_qty from `tabPurchase Return Item` preti inner join `tabPurchase Return` pret on preti.parent= pret.name WHERE preti.pi_item_reference=%s AND pret.name !=%s and pret.docstatus<2""",(docitem.pi_item_reference, self.name))[0][0]

				pi_item = frappe.get_doc("Purchase Invoice Item", docitem.pi_item_reference)

				print("total_returned_qty_not_in_this_pr")
				print(total_returned_qty_not_in_this_pr)
				print(docitem.qty)

				if total_returned_qty_not_in_this_pr:
					if(pi_item.qty < (total_returned_qty_not_in_this_pr + docitem.qty)):
						frappe.throw("The quantity available for return in the original purchase is less than the quantity specified in the line item {}".format(docitem.idx))
				else:
					if(pi_item.qty < docitem.qty):
						frappe.throw("The quantity available for return in the original purchase is less than the quantity specified in the line item {}".format(docitem.idx))

	def validate_stock(self):

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

	def on_submit(self):

		turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

		# if(frappe.session.user == "Administrator" and turn_off_background_job):
		# 	self.do_postings_on_submit()
		# else:
			# frappe.enqueue(self.do_postings_on_submit, queue="long")
		self.do_postings_on_submit()

	def on_update(self):
		self.update_purchase_invoice_quantities_on_update()

	def on_cancel(self):
		cancel_bank_reconciliation("Purchase Return", self.name)
		self.update_purchase_invoice_quantities_before_delete_or_cancel()

		turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

		if(frappe.session.user == "Administrator" and turn_off_background_job):
			self.cancel_purchase_return()
		else:
			self.cancel_purchase_return()
			# frappe.enqueue(self.cancel_purchase_return, queue ="long")


	def on_trash(self):
		# On cancel, the quantities are already deleted.
		if(self.docstatus < 2):
			self.update_purchase_invoice_quantities_before_delete_or_cancel()

	def do_postings_on_submit(self):
		self.insert_gl_records()
		self.insert_payment_postings()
		self.do_stock_posting()
		update_accounts_for_doc_type('Purchase Return', self.name)
		create_bank_reconciliation("Purchase Return", self.name)

	def do_stock_posting(self):
		# Note that negative stock checking is handled in the validate method
		stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher.voucher = 'Purchase Return'
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
				new_balance_qty = docitem.qty_in_base_unit * -1

				previous_stock_ledger_name = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
	                , 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)

				# Default valuation rate
				valuation_rate = docitem.rate_in_base_unit
				# Default balance value calculating withe the current row only. Note that it holds negative value
				new_balance_value = new_balance_qty * valuation_rate

				# Assigned current stock value to use if previous values not exist
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
					new_balance_qty = last_stock_ledger.balance_qty - abs(new_balance_qty)
					new_balance_value = last_stock_ledger.balance_value - abs(new_balance_value)

					if new_balance_qty!=0:
						# Sometimes the balance_value and balance_qty can be negative, so it is ideal to take the abs value
						valuation_rate = abs(new_balance_value)/abs(new_balance_qty)

					change_in_stock_value = new_balance_value - last_stock_ledger.balance_value

				if docitem.item not in item_stock_ledger:
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
					new_stock_ledger.voucher = "Purchase Return"
					new_stock_ledger.voucher_no = self.name
					new_stock_ledger.source = "Purchase Return Item"
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

				sl = frappe.get_doc("Stock Ledger", new_stock_ledger.name)
				# If no more records for the item, update balances. otherwise it updates in the flow
				if more_records_count_for_item==0:
					if frappe.db.exists('Stock Balance', {'item':docitem.item,'warehouse': docitem.warehouse}):
						frappe.db.delete('Stock Balance',{'item': docitem.item, 'warehouse': docitem.warehouse})
					new_stock_balance = frappe.new_doc('Stock Balance')
					new_stock_balance.item = docitem.item
					new_stock_balance.item_name = docitem.item_name
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
		stock_recalc_voucher.voucher = 'Purchase Return'
		stock_recalc_voucher.voucher_no = self.name
		stock_recalc_voucher.voucher_date = self.posting_date
		stock_recalc_voucher.voucher_time = self.posting_time
		stock_recalc_voucher.status = 'Not Started'
		stock_recalc_voucher.source_action = "Cancel"
		posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))
		more_records = 0

		# Iterate on each item from the cancelling Purchase Return
		for docitem in self.items:
			more_records_for_item = frappe.db.count('Stock Ledger',{'item':docitem.item,
            	'warehouse':docitem.warehouse, 'posting_date':['>', posting_date_time]})
			more_records = more_records + more_records_for_item
			previous_stock_ledger_name = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
            		    , 'posting_date':['<', posting_date_time]},['name'], order_by='posting_date desc', as_dict=True)
			# If any items in the collection has more records
			if(more_records_for_item>0):

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
				stock_balance = frappe.get_value('Stock Balance', {'item':docitem.item, 'warehouse':docitem.warehouse}, ['name'] )
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
				# item_name = frappe.get_value("Item", docitem.item,['item_name'])
				update_stock_balance_in_item(docitem.item)

		# Delete the stock ledger before recalculate, to avoid it to be recalculated again
		frappe.db.delete("Stock Ledger",
		{"voucher": "Purchase Return",
			"voucher_no":self.name
		})

		if(more_records>0):
			stock_recalc_voucher.insert()
			recalculate_stock_ledgers(stock_recalc_voucher, self.posting_date, self.posting_time)

	def cancel_purchase_return(self):

		self.do_cancel_stock_posting()

		delete_gl_postings_for_cancel_doc_type('Purchase Return',self.name)


	def insert_gl_records(self):

		default_company = frappe.db.get_single_value("Global Settings","default_company")
		default_accounts = frappe.get_value("Company", default_company,['default_payable_account','default_inventory_account',
		'stock_received_but_not_billed','round_off_account','tax_account'], as_dict=1)

		idx =1
		# Debit Payable A/c
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Purchase Return"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.default_payable_account
		gl_doc.debit_amount = self.rounded_total
		gl_doc.party_type = "Supplier"

		gl_doc.party = self.supplier
		gl_doc.against_account = default_accounts.default_inventory_account
		gl_doc.insert()
		idx +=1

		# # Stock Received But Not Billed
		# idx =2
		# gl_doc = frappe.new_doc('GL Posting')
		# gl_doc.voucher_type = "Purchase Return"
		# gl_doc.voucher_no = self.name
		# gl_doc.idx = idx
		# gl_doc.posting_date = self.posting_date
		# gl_doc.posting_time = self.posting_time
		# gl_doc.account = default_accounts.stock_received_but_not_billed
		# gl_doc.debit_amount =  self.net_total - self.tax_total
		# gl_doc.against_account = self.supplier
		# gl_doc.insert()

		# Credit Tax
		if self.tax_total>0:
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Purchase Return"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.tax_account
			gl_doc.credit_amount = self.tax_total
			gl_doc.against_account = default_accounts.default_payable_account
			gl_doc.insert()
			idx +=1

		# Rounded Total
		if self.round_off!=0.00:
			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Purchase Return"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.round_off_account

			# If rounded_total more than net_total debit is more in the payable account
			if self.rounded_total > self.net_total:
				gl_doc.credit_amount = self.round_off
				gl_doc.against_account = default_accounts.default_payable_account
			else:
				gl_doc.debit_amount = self.round_off
				gl_doc.against_account = default_accounts.default_inventory_account

			gl_doc.insert()
			idx +=1

		# Credit Inventory A/c

		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Purchase Return"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.default_inventory_account
		gl_doc.credit_amount = self.net_total - self.tax_total
		gl_doc.against_account = default_accounts.default_payable_account
		gl_doc.insert()
		idx +=1

	def insert_payment_postings(self):

		if self.credit_purchase==0:
			gl_count = frappe.db.count('GL Posting',{'voucher_type':'Purchase Return', 'voucher_no': self.name})
			default_company = frappe.db.get_single_value("Global Settings","default_company")
			default_accounts = frappe.get_value("Company", default_company,['default_payable_account','default_inventory_account',
			'stock_received_but_not_billed','round_off_account','tax_account'], as_dict=1)
			payment_mode = frappe.get_value("Payment Mode", self.payment_mode, ['account'],as_dict=1)

			idx = gl_count + 1

			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Purchase Return"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = default_accounts.default_payable_account
			gl_doc.credit_amount = self.rounded_total
			gl_doc.party_type = "Supplier"
			gl_doc.party = self.supplier
			gl_doc.against_account = payment_mode.account
			gl_doc.insert()

			idx= idx + 1

			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.voucher_type = "Purchase Return"
			gl_doc.voucher_no = self.name
			gl_doc.idx = idx
			gl_doc.posting_date = self.posting_date
			gl_doc.posting_time = self.posting_time
			gl_doc.account = payment_mode.account
			gl_doc.debit_amount = self.rounded_total
			gl_doc.against_account = default_accounts.default_payable_account
			gl_doc.insert()

	def update_purchase_invoice_quantities_on_update(self):

		pi_reference_any = False

		for item in self.items:
			if not item.pi_item_reference:
				continue
			else:
				total_returned_qty_not_in_this_pr = frappe.db.sql(""" SELECT SUM(qty) as total_returned_qty from `tabPurchase Return Item` preti inner join `tabPurchase Return` pret on preti.parent= pret.name WHERE preti.pi_item_reference=%s AND pret.name !=%s and pret.docstatus<2""",(item.pi_item_reference, self.name))[0][0]

				pi_item = frappe.get_doc("Purchase Invoice Item", item.pi_item_reference)

				if total_returned_qty_not_in_this_pr:
					pi_item.qty_returned = total_returned_qty_not_in_this_pr + item.qty
				else:
					pi_item.qty_returned = item.qty
				pi_item.save()
				pi_reference_any = True

		if pi_reference_any:
			frappe.msgprint("Returned qty of items in the corresponding purchase invoice updated successfully", indicator= "green", alert= True)

	def update_purchase_invoice_quantities_before_delete_or_cancel(self):

		pi_reference_any = False

		for item in self.items:
			if not item.pi_item_reference:
				continue
			else:
				total_returned_qty_not_in_this_pr = frappe.db.sql(""" SELECT SUM(qty) as total_returned_qty from `tabPurchase Return Item` preti inner join `tabPurchase Return` pret on preti.parent= pret.name WHERE preti.pi_item_reference=%s AND pret.name !=%s and pret.docstatus<2""",(item.pi_item_reference, self.name))[0][0]

				pi_item = frappe.get_doc("Purchase Invoice Item", item.pi_item_reference)

				if total_returned_qty_not_in_this_pr:
					pi_item.qty_returned = total_returned_qty_not_in_this_pr
				else:
					pi_item.qty_returned = 0

				pi_item.save()
				pi_reference_any = True

		if pi_reference_any:
			frappe.msgprint("Returned qty of items in the corresponding purchase invoice reverted successfully", indicator= "green", alert= True)

@frappe.whitelist()
def get_default_payment_mode():
    default_payment_mode = frappe.db.get_value('Company', filters={'name'},fieldname='default_payment_mode_for_purchase')
    print(default_payment_mode)
    return default_payment_mode
