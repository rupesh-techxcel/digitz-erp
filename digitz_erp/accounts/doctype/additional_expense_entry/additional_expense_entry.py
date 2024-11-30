# Copyright (c) 2024, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
from digitz_erp.api.gl_posting_api import update_accounts_for_doc_type, delete_gl_postings_for_cancel_doc_type
from digitz_erp.api.document_posting_status_api import init_document_posting_status, update_posting_status
from digitz_erp.api.stock_update import recalculate_stock_ledgers, update_stock_balance_in_item
from digitz_erp.api.settings_api import add_seconds_to_time

class AdditionalExpenseEntry(Document):

	def Voucher_In_The_Same_Time(self):
		possible_invalid= frappe.db.count('Expense Entry', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time]})
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

	def on_submit(self):

		init_document_posting_status(self.doctype,self.name)

		self.postings_start_time = datetime.now()
		turn_off_background_job = frappe.db.get_single_value("Global Settings",'turn_off_background_job')

		# if(frappe.session.user == "Administrator" and turn_off_background_job):
		#     self.do_postings_on_submit()
		# else:
		#     frappe.enqueue(self.do_postings_on_submit, queue="long")

		self.do_postings_on_submit()

	def on_cancel(self):

		update_posting_status(self.doctype,self.name,'posting_status','Cancel Pending')
		self.cancel_expense()

	def cancel_expense(self):

		delete_gl_postings_for_cancel_doc_type('Additional Expense Entry',self.name)

		self.update_stock_ledger_values_on_cancel()

		# frappe.db.delete("GL Posting",
		# 		{"Voucher_type": "Expense Entry",
		# 		 "voucher_no":self.name
		# 		})

		update_posting_status(self.doctype,self.name, "posting_status", "Completed")


	def do_postings_on_submit(self):

		self.insert_gl_records()

		update_posting_status(self.doctype,self.name,'gl_posted_time')

		self.insert_payment_postings()
		update_posting_status(self.doctype,self.name,'payment_posted_time')

		update_accounts_for_doc_type('Additional Expense Entry',self.name)

		update_posting_status(self.doctype,self.name,'posting_status','Completed')

		self.update_stock_postings()

	def insert_gl_records(self):

		idx = 1

		# Debit Expenses
		for expense_entry in self.expense_entry_details:

			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Additional Expense Entry'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = expense_entry.expense_date
			gl_doc.account = expense_entry.expense_account
			gl_doc.debit_amount = expense_entry.amount
			gl_doc.remarks = self.remarks;
			gl_doc.insert()

			idx += 1

		# Debit Tax Amounts
		taxes = self.get_tax_totals()

		for key, tax_amount  in taxes.items():

			tax_for_expense, expense_date = key.split('_')

			#print("tax_for_expense")
			#print(tax_for_expense)

			tax = frappe.get_doc("Tax", tax_for_expense)

			if(tax.tax_rate >0):
				gl_doc = frappe.new_doc('GL Posting')
				gl_doc.idx = idx
				gl_doc.voucher_type = 'Additional Expense Entry'
				gl_doc.voucher_no = self.name
				gl_doc.posting_date = expense_date
				gl_doc.account = tax.account
				gl_doc.debit_amount = tax_amount
				gl_doc.remarks = self.remarks;
				gl_doc.insert()
				idx += 1

		# Credit Payable Accounts, supplier
		payable_items = self.get_payable_totals()

		for key, amount  in payable_items.items():

			payable_account, supplier, expense_date = key.split('_')

			gl_doc = frappe.new_doc('GL Posting')
			gl_doc.idx = idx
			gl_doc.voucher_type = 'Additional Expense Entry'
			gl_doc.voucher_no = self.name
			gl_doc.posting_date = expense_date
			gl_doc.account = payable_account
			gl_doc.party_type = "Supplier"
			gl_doc.party = supplier
			gl_doc.credit_amount = amount
			gl_doc.remarks = self.remarks;
			gl_doc.insert()
			idx += 1

	def insert_payment_postings(self):

		if not self.credit_expense:

			gl_count = frappe.db.count('GL Posting',{'voucher_type':'Additional Expense Entry', 'voucher_no': self.name})

			idx= gl_count + 1

			payable_items = self.get_payable_totals()

			for key, amount  in payable_items.items():

				payable_account, supplier,expense_date = key.split('_')

				gl_doc = frappe.new_doc('GL Posting')
				gl_doc.idx = idx
				gl_doc.voucher_type = 'Additional Expense Entry'
				gl_doc.voucher_no = self.name
				gl_doc.posting_date = expense_date
				gl_doc.account = payable_account
				gl_doc.party_type = "Supplier"
				gl_doc.party = supplier
				gl_doc.debit_amount = amount
				gl_doc.remarks = self.remarks;
				gl_doc.insert()
				idx += 1

			payment_items = self.get_payment_totals()

			for key,amount in payment_items.items():
				payment_account,expense_date = key.split('_')

				gl_doc = frappe.new_doc('GL Posting')
				gl_doc.idx = idx
				gl_doc.voucher_type = 'Additional Expense Entry'
				gl_doc.voucher_no = self.name
				gl_doc.posting_date = expense_date
				gl_doc.account = payment_account
				gl_doc.against_account = payable_account
				gl_doc.credit_amount = amount
				gl_doc.remarks = self.remarks;
				gl_doc.insert()
				idx += 1

	def update_stock_postings(self):
		if self.expense_against == "Purchase":
			self.insert_stock_gl_posting()
			self.update_stock_ledger_values()

	def update_stock_ledger_values(self):

		stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher.voucher = 'Purchase Invoice'
		stock_recalc_voucher.voucher_no = self.name
		stock_recalc_voucher.voucher_date = self.posting_date
		stock_recalc_voucher.voucher_time = self.posting_time
		stock_recalc_voucher.status = 'Not Started'
		stock_recalc_voucher.source_action = "Update"

		mroe_records = 0

		for pi_item in self.purchase_items:

			if (pi_item.allocation_amount > 0):

				ref_doc_no = pi_item.reference_document_no
				allocation_amount = pi_item.allocation_amount

				query = """select name from `tabStock Ledger` sl where voucher='Purchase Invoice' and source_document_id= %s"""

				stock_ledger_values = frappe.db.sql(query, (ref_doc_no), as_dict = True)

				if stock_ledger_values and stock_ledger_values[0]:

					sl = frappe.get_doc("Stock Ledger",stock_ledger_values[0].name)

					sl.valuation_rate = sl.valuation_rate + (allocation_amount/ sl.qty_in)

					sl.balance_value = sl.balance_value + allocation_amount
					sl.additional_allocation = allocation_amount
					sl.save()

					more_records_count_for_item = frappe.db.count('Stock Ledger',{'item':sl.item,
				'warehouse':sl.warehouse, 'posting_date':['>', sl.posting_date]})

					mroe_records += more_records_count_for_item

					if (more_records_count_for_item>0):

						stock_recalc_voucher.append('records',{'item': sl.item,
    													'warehouse': sl.warehouse,
                                                        'base_stock_ledger': sl.name
                                                            })
					else:

						if frappe.db.exists('Stock Balance', {'item':sl.item,'warehouse': sl.warehouse}):
							frappe.db.delete('Stock Balance',{'item': sl.item, 'warehouse': sl.warehouse})

						new_stock_balance = frappe.new_doc('Stock Balance')
						new_stock_balance.item = sl.item
						new_stock_balance.item_name = sl.item_name
						new_stock_balance.unit = sl.unit
						new_stock_balance.warehouse = sl.warehouse
						new_stock_balance.stock_qty = sl.balance_qty
						new_stock_balance.stock_value = sl.balance_value
						new_stock_balance.valuation_rate = sl.valuation_rate

						new_stock_balance.insert()

						update_stock_balance_in_item(sl.item)

		if mroe_records>0:
			stock_recalc_voucher.insert()
			recalculate_stock_ledgers(stock_recalc_voucher,None,None)

	def update_stock_ledger_values_on_cancel(self):

		stock_recalc_voucher = frappe.new_doc('Stock Recalculate Voucher')
		stock_recalc_voucher.voucher = 'Purchase Invoice'
		stock_recalc_voucher.voucher_no = self.name
		stock_recalc_voucher.voucher_date = self.posting_date
		stock_recalc_voucher.voucher_time = self.posting_time
		stock_recalc_voucher.status = 'Not Started'
		stock_recalc_voucher.source_action = "Cancel"

		mroe_records = 0

		for pi_item in self.purchase_items:

			if (pi_item.allocation_amount > 0):

				ref_doc_no = pi_item.reference_document_no
				allocation_amount = pi_item.allocation_amount

				query = """select name from `tabStock Ledger` sl where voucher='Purchase Invoice' and source_document_id= %s"""

				stock_ledger_values = frappe.db.sql(query, (ref_doc_no), as_dict = True)

				if stock_ledger_values and stock_ledger_values[0]:

					sl = frappe.get_doc("Stock Ledger",stock_ledger_values[0].name)

					# Reduce the allocation amount
					sl.valuation_rate = sl.valuation_rate - (allocation_amount/ sl.qty_in)
					sl.balance_value = sl.balance_value - allocation_amount
					sl.additional_allocation = 0
					sl.save()

					more_records_count_for_item = frappe.db.count('Stock Ledger',{'item':sl.item,
				'warehouse':sl.warehouse, 'posting_date':['>', sl.posting_date]})

					mroe_records += more_records_count_for_item

					if (more_records_count_for_item>0):

						stock_recalc_voucher.append('records',{'item': sl.item,
														'warehouse': sl.warehouse,
														'base_stock_ledger': sl.name
															})
					else:

						if frappe.db.exists('Stock Balance', {'item':sl.item,'warehouse': sl.warehouse}):
							frappe.db.delete('Stock Balance',{'item': sl.item, 'warehouse': sl.warehouse})

						new_stock_balance = frappe.new_doc('Stock Balance')
						new_stock_balance.item = sl.item
						new_stock_balance.item_name = sl.item_name
						new_stock_balance.unit = sl.unit
						new_stock_balance.warehouse = sl.warehouse
						new_stock_balance.stock_qty = sl.balance_qty
						new_stock_balance.stock_value = sl.balance_value
						new_stock_balance.valuation_rate = sl.valuation_rate

						new_stock_balance.insert()

						update_stock_balance_in_item(sl.item)

		if mroe_records>0:
			stock_recalc_voucher.insert()
			recalculate_stock_ledgers(stock_recalc_voucher,None,None)

	def insert_stock_gl_posting(self):

		gl_count = frappe.db.count('GL Posting',{'voucher_type':'Additional Expense Entry', 'voucher_no': self.name})

		idx= gl_count + 1

		default_company = frappe.db.get_single_value(
			"Global Settings", "default_company")

		default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account','default_income_account', 'stock_adjustment_account', 'round_off_account', 'tax_account'], as_dict=1)

		stock_adjustment_value = self.total_expense_amount

		# Inventory account Eg: Stock In Hand
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Additional Expense Entry"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.default_inventory_account
		gl_doc.debit_amount = stock_adjustment_value
		gl_doc.against_account = default_accounts.stock_adjustment_account
		gl_doc.insert()
		idx += 1

		# Cost Of Goods Sold
		idx = 2
		gl_doc = frappe.new_doc('GL Posting')
		gl_doc.voucher_type = "Additional Expense Entry"
		gl_doc.voucher_no = self.name
		gl_doc.idx = idx
		gl_doc.posting_date = self.posting_date
		gl_doc.posting_time = self.posting_time
		gl_doc.account = default_accounts.stock_adjustment_account
		gl_doc.credit_amount = stock_adjustment_value
		gl_doc.against_account = default_accounts.default_inventory_account
		gl_doc.insert()
		idx += 1


	def get_payable_totals(self):

		payable_account_dictionary = {}

		for expense_entry in self.expense_entry_details:

			payable_account = expense_entry.get("payable_account")
			supplier = expense_entry.get("supplier")
			expense_date = expense_entry.get("expense_date")
			total = expense_entry.get("total")
			key = f"{payable_account}_{supplier}_{expense_date}"

			if key in payable_account_dictionary:
				payable_account_dictionary[key] += total
			else:
				payable_account_dictionary[key] = total

		return payable_account_dictionary

	# Need to consider the payment account for each expense date
	def get_payment_totals(self):

		payment_account_dictionary = {}

		for expense_entry in self.expense_entry_details:

			payment_account = self.payment_account

			expense_date = expense_entry.get("expense_date")

			key = f"{payment_account}_{expense_date}"

			if key in payment_account_dictionary:
				payment_account_dictionary[key] += expense_entry.total
			else:
				payment_account_dictionary[key] = expense_entry.total

		return payment_account_dictionary

	def get_tax_totals(self):
		tax_dictionary = {}

		for expense_entry in self.expense_entry_details:
			tax_amount = expense_entry.get("tax_amount")

			if(tax_amount>0):
				tax = expense_entry.get("tax")
				tax_amount = expense_entry.get("tax_amount")
				expense_date = expense_entry.get("expense_date")

				#print("tax from get_tax_totals")
				#print(tax)

				# Use the expense_date in the key along with tax, separated by an underscore
				key = f"{tax}_{expense_date}"
				#print("key from get_tax_totals")
				#print(key)

				if key in tax_dictionary:
					tax_dictionary[key] += tax_amount
				else:
					tax_dictionary[key] = tax_amount

		#print("tax_dictionary")
		#print(tax_dictionary)
		return tax_dictionary



	def on_update(self):
		self.update_payment_schedules()

	def update_payment_schedules(self):

		existing_entries = frappe.get_all("Payment Schedule", filters={"payment_against": "Additional Expense", "document_no": self.name})


		# Delete existing payment schedules if found
		for entry in existing_entries:
			try:
				frappe.delete_doc("Payment Schedule", entry.name)
			except Exception as e:
				frappe.log_error("Error deleting payment schedule: " + str(e))


		#print("self.payment_schedule")
		#print(self.payment_schedule)

		for payment_schedule in self.payment_schedule:

			new_payment_schedule = frappe.new_doc("Payment Schedule")
			new_payment_schedule.payment_against = "Additional Expense"
			new_payment_schedule.supplier = payment_schedule.supplier
			new_payment_schedule.document_no = self.name
			new_payment_schedule.document_date = self.posting_date
			new_payment_schedule.scheduled_date = payment_schedule.date
			new_payment_schedule.amount = payment_schedule.amount

			try:
				new_payment_schedule.insert()
				frappe.msgprint("payment schedule added successfully",indicator="green", alert = True)
			except Exception as e:
				frappe.log_error("Error creating payment schedule: " + str(e))
				frappe.msgprint("An error occured while inserting payment schedule",indicator="red", alert = True)

		frappe.db.commit()

	def GetAccountForTheHighestAmount(self):

		highestAmount = 0
		account = ""

		for detail in self.expense_entry_details:

			if detail.amount > highestAmount:
				highestAmount = detail.amount
				account = detail.account

		return account


	def update_gl_postings_for_purchases(self):

		for purchase in self.additional_expense_purchases:

			purchase_doc = frappe.get_doc('Purchase Invoice',purchase.purchase_invoice)
