# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils import now
from frappe.model.document import Document

class SalesInvoice(Document):
    """if need of autoupdate of delivery note in case of any update in sales invoice then uncomment the before_save controller"""

    # def before_save(self):
        # for i in self.items:
        #     if i.delivery_note:
        #         frappe.db.set_value(
        #             'Delivery Note', i.delivery_note, 'against_sales_invoice', self.name)
        #         frappe.db.commit()
        
        # if not self.is_new() and self.auto_save_delivery_note:
        # if self.auto_save_delivery_note:
            #  self.generate_delivery_note()

    def before_submit(self):

        # Checking needed whether Delivery Note is creating automatically, if yes, then only stock availability need to check
        # otherwise it could be done with in the delivery note itself.

        # self.validate_item()           
        

        self.created_by = frappe.user
        self.submitted_date = now()

        self.insert_gl_records()
        self.insert_payment_postings()

    
    # def validate(self):

        # self.validate_item()        
    
    # def validate_item(self):
         
        # posting_date_time = get_datetime(self.posting_date + " " + self.posting_time)		        	
      
        # for docitem in self.items:
            # available_qty =0
            
            # previous_stocks = frappe.db.get_list('Stock In Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse], 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],order_by='posting_date', as_list=True)
            # print(previous_stocks)
            # for stock_for_balance in previous_stocks:
            #     available_qty = available_qty + stock_for_balance.balance_qty
        
            # if(available_qty< docitem.qty_in_base_unit):
            #         frappe.throw("No sufficient qty exists for the item " + docitem.item +", required qty -" + str(docitem.qty_in_base_unit) + " " + docitem.base_unit
            #         + ", available qty -" + str(available_qty))

    def before_cancel(self):

        frappe.db.delete("Stock Ledger",
                         {"Voucher_type": "Sales Invoice",
                          "voucher_no": self.name
                          })

        frappe.db.delete("GL Posting",
                         {"Voucher_type": "Sales Invoice",
                          "voucher_no": self.name
                          })      
        
    def on_trash(self):
        if self.auto_save_delivery_note:
            frappe.delete_doc('Delivery Note', self.delivery_note)

        # if self.auto_save_delivery_note:
        #      do = frappe.get_doc('Delivery Note', self.delivery_note)
        #      do.auto_generated_from_sales_invoice =0
        #      do.save()
        #      frappe.msgprint("Removed LInk with Delivery Note. You can recreate the Sales Invoice from Delivery Note if required.")
    
    def insert_gl_records(self):

        default_company = frappe.db.get_single_value(
            "Global Settings", "default_company")

        default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',

                                                                         'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)

        idx = 1

        # Trade Payavble - Debit
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
        gl_doc.aginst_account = default_accounts.default_income_account
        gl_doc.insert()

        # Stock Received But Not Billed
        idx = 2
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Sales Invoice"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.default_income_account
        gl_doc.credit_amount = self.net_total - self.tax_total
        gl_doc.aginst_account = default_accounts.default_receivable_account
        gl_doc.insert()

        # Tax
        idx = 3
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Sales Invoice"
        gl_doc.voucher_no = self.name
        gl_doc.idx = idx
        gl_doc.posting_date = self.posting_date
        gl_doc.posting_time = self.posting_time
        gl_doc.account = default_accounts.tax_account
        gl_doc.credit_amount = self.tax_total
        gl_doc.insert()

        # Round Off

        if self.round_off != 0.00:
            idx = 4
            gl_doc = frappe.new_doc('GL Posting')
            gl_doc.voucher_type = "Sales Invoice"
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

    def insert_payment_postings(self):

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
            gl_doc.account = default_accounts.default_receivable_account
            gl_doc.credit_amount = self.rounded_total
            gl_doc.party_type = "Customer"
            gl_doc.party = self.customer
            gl_doc.aginst_account = payment_mode.account
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
            gl_doc.aginst_account = default_accounts.default_receivable_account
            gl_doc.insert()

    @frappe.whitelist()
    def auto_generate_delivery_note(self):
        
        # if document already saved, do also already saved. so, if the user is submitting the sales invoice
        # just need to submit the do as well
                
        if self.docstatus == 1:
            si_do = frappe.get_doc('Sales Invoice Delivery Notes',{'parent':self.name})
            do_no = si_do.delivery_note
            do = frappe.get_doc('Delivery Note',do_no)
            do.submit()
        
            frappe.msgprint("Delivery Note submitted")
            return
        
        delivery_note_name = ""
        
        si_name = self.name        

        # Before delete the existing Delivery Note to insert it again, remove the link in the Sales Invoice
        # to avoid the reference error

        # si = frappe.get_doc('Sales Invoice',si_name)
        # Remove Reference first to avoid reference error when trying to delete before recreating
        # si.delivery_note ="" 
        # si.save()
                

        if self.auto_save_delivery_note:
            if frappe.db.exists('Sales Invoice Delivery Notes', {'parent': self.name}):    
                delivery_note_name =  frappe.db.get_value('Sales Invoice Delivery Notes',{'parent':self.name},['delivery_note'] )
                # Remove the reference first before deleting the actual document
                frappe.db.delete('Sales Invoice Delivery Notes',{'parent':self.name})
                delivery_note_doc = frappe.get_doc('Delivery Note', delivery_note_name)
                delivery_note_name = delivery_note_doc.name
                delivery_note_doc.delete()               
       
        delivery_note = self.__dict__
        delivery_note['doctype'] = 'Delivery Note'
        # delivery_note['against_sales_invoice'] = delivery_note['name']
        delivery_note['name'] = delivery_note_name        
        delivery_note['naming_series'] = ""
        # delivery_note['posting_date'] = self.posting_date
        # delivery_note['posting_time'] = self.posting_time

        delivery_note['auto_generated_from_sales_invoice'] = 1

        for item in delivery_note['items']:
            item.doctype = "Delivery Note Item"    
            item._meta = ""        

        doNo = frappe.get_doc(delivery_note).insert()
        frappe.db.commit()       
        
        
        do = frappe.get_doc('Delivery Note', doNo.name)
        si = frappe.get_doc('Sales Invoice',si_name)

        row = si.append('delivery_notes', {'delivery_note': do.name})

        si.save()

        delivery_notes = frappe.db.get_list('Sales Invoice Delivery Notes', {'parent': ['=', si_name]},['delivery_note'], as_list=True)
      
        # It is likely that there will be only one delivery note for the sales invoice for this method.
        index = 0
        maxIndex = 3
        doNos = ""
    
        for delivery_noteName in delivery_notes:     
            delivery_note = frappe.get_doc('Delivery Note',delivery_noteName )   
            doNos = doNos + delivery_note.name + "   "
            index= index + 1
            if index == maxIndex:
                break     

        si = frappe.get_doc('Sales Invoice',si_name)

        si.delivery_notes_to_print = doNos
        
        index = 0        

        for item in si.items:            
            item.delivery_note_item_reference_no = do.items[index].name
            index = index + 1

        si.save()

    @frappe.whitelist()
    def cancel_delivery_note_for_sales_invoice(self):
        
        delivery_note = frappe.get_value("Sales Invoice Delivery Notes",{'parent': self.name}, ['delivery_note'])
        do = frappe.get_doc('Delivery Note',delivery_note)
        do.cancel()
        frappe.msgprint("Delivery Note cancelled")
        
        
			
        