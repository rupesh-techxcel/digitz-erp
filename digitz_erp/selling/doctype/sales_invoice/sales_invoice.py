# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.utils import now
from frappe.model.document import Document


class SalesInvoice(Document):
    """if need of autoupdate of delivery note in case of any update in sales invoice then uncomment the before_save controller"""

    def before_save(self):
        # for i in self.items:
        #     if i.delivery_note:
        #         frappe.db.set_value(
        #             'Delivery Note', i.delivery_note, 'against_sales_invoice', self.name)
        #         frappe.db.commit()
        
        # if not self.is_new() and self.auto_save_delivery_note:        
         
        # if self.auto_save_delivery_note:
        #     self.auto_generate_delivery_note()
        # frappe.msgprint("before save event")
        # print("before save")

       def before_submit(self):

        # When duplicating the voucher user may not remember to change the date and time. So do not allow to save the voucher to be 
		# posted on the same time with any of the existing vouchers. This also avoid invalid selection to calculate moving average value
		
        # Store the current document name to the variable to use it after delete the variable
        

        possible_invalid= frappe.db.count('Sales Invoice', {'posting_date': ['=', self.posting_date], 'posting_time':['=', self.posting_time], 'docstatus':['=', 1]})
        
        if(possible_invalid >0):
            frappe.throw("There is another sales invoice exist with the same date and time. Please correct the date and time.")

        # Checking needed whether Delivery Note is creating automatically, if yes, then only stock availability need to check
        # otherwise it could be done with in the delivery note itself.

        self.validate_item()           

        print("Before submit in sales invoice")

        # self.created_by = frappe.user
        # self.submitted_date = now()
        
   
        self.insert_gl_records()
        self.insert_payment_postings()

    
    # def validate(self):

    #     self.validate_item()        
    
    def validate_item(self):

        print("From validate item, SI")
         
        posting_date_time = get_datetime(str(self.posting_date) + " " + str(self.posting_time))		        	
      
        for docitem in self.items:

            print(docitem.item)
            
            # previous_stocks = frappe.db.get_value('Stock Ledger', {'item':docitem.item,'warehouse': docitem.warehouse , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],order_by='posting_date desc', as_dict=True)
            
            previous_stock_balance = frappe.db.get_value('Stock Ledger', {'item': ['=', docitem.item], 'warehouse':['=', docitem.warehouse]
            , 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
            order_by='posting_date desc', as_dict=True)

            if(not previous_stock_balance): 
                frappe.throw("No stock exists for" + docitem.item )
        
            if(previous_stock_balance.balance_qty< docitem.qty_in_base_unit):
                frappe.throw("Sufficiant qty does not exists for the item " + docitem.item + " required Qty= " + str(docitem.qty_in_base_unit) + 
                " " + docitem.base_unit + " and available Qty=" + str(previous_stock_balance.balance_qty) + " " + docitem.base_unit )
        
    def on_cancel(self):
               
        if self.auto_save_delivery_note:
            # delivery_note_name = frappe.get_value("Sales Invoice Delivery Notes",{'parent': self.name}, ['delivery_note'])
            # delivery_note = frappe.get_doc('Delivery Note', delivery_note_name)
            
            self.cancel_delivery_note_for_sales_invoice()
                
        frappe.db.delete("GL Posting",
                         {"Voucher_type": "Sales Invoice",
                          "voucher_no": self.name
                          })      

    # def before_cancel(self):

        
        
    # def on_trash(self):
        # if self.auto_save_delivery_note:
            # delivery_note = frappe.get_value("Sales Invoice Delivery Notes",{'parent': self.name}, ['delivery_note'])
            # frappe.delete_doc('Delivery Note', delivery_note)  
    
   
        
    
    # def after_delete(self):

        # print("after delete SI event")

        # if self.auto_save_delivery_note:
        #     delivery_note = frappe.get_value("Sales Invoice Delivery Notes",{'parent': self.doc_name}, ['delivery_note'])
        #     print(delivery_note)
        #     frappe.delete_doc('Delivery Note', delivery_note)

    # def after_save():
    #     frappe.msgprint("after save")
    #     print("after save")
    
    def insert_gl_records(self):

        print("From insert gl records")

        default_company = frappe.db.get_single_value(
            "Global Settings", "default_company")

        default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                         'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)

        idx = 1

        # Trade Receivable - Debit
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

        # Income account - Credot
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

        # Tax - Credit
        idx = 3
        gl_doc = frappe.new_doc('GL Posting')
        gl_doc.voucher_type = "Sales Invoice"
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
        
        print("From auto generate delivery note")
        
        # if document already saved, do also already saved. so, if the user is submitting the sales invoice
        # just need to submit the do as well
        
        print("docstatus")
        print(self.docstatus)
                
        if self.docstatus == 1:
            si_do = frappe.get_doc('Sales Invoice Delivery Notes',{'parent':self.name})
            do_no = si_do.delivery_note
            do = frappe.get_doc('Delivery Note',do_no)
            do.submit()
        
            frappe.msgprint("A Delivery Note corresponding to the sales invoice is also generated.")
            return
        
        delivery_note_name = ""
        
        doNo = ""        
        
        si_name = self.name        

        # Before delete the existing Delivery Note to insert it again, remove the link in the Sales Invoice
        # to avoid the reference error

        # si = frappe.get_doc('Sales Invoice',si_name)
        # Remove Reference first to avoid reference error when trying to delete before recreating
        # si.delivery_note ="" 
        # si.save()
        
        do_exists = False

        if self.auto_save_delivery_note:
            if frappe.db.exists('Sales Invoice Delivery Notes', {'parent': self.name}):    
                do_exists = True
                delivery_note_name =  frappe.db.get_value('Sales Invoice Delivery Notes',{'parent':self.name},['delivery_note'] )
                # Remove the reference first before deleting the actual document
                # frappe.db.delete('Sales Invoice Delivery Notes',{'parent':self.name})
                delivery_note_doc = frappe.get_doc('Delivery Note', delivery_note_name)
                doNo = delivery_note_doc.name
                # delivery_note_doc.delete()
                # print("delivery note deleted")
                
                delivery_note_doc.customer = self.customer
                delivery_note_doc.customer_name = self.customer_name
                delivery_note_doc.customer_display_name = self.customer_display_name                
                delivery_note_doc.customer_address = self.customer_address
                delivery_note_doc.reference_no = self.reference_no
                delivery_note_doc.posting_date = self.posting_date
                delivery_note_doc.posting_time = self.posting_time
                delivery_note_doc.ship_to_location = self.ship_to_location
                delivery_note_doc.salesman = self.salesman
                delivery_note_doc.salesman_code = self.salesman_code
                delivery_note_doc.tax_id = self.tax_id
                delivery_note_doc.lpo_no = self.lpo_no
                delivery_note_doc.lpo_date = self.lpo_date
                delivery_note_doc.price_list = self.price_list
                delivery_note_doc.rate_includes_tax = self.rate_includes_tax
                delivery_note_doc.warehouse = self.warehouse
                delivery_note_doc.credit_sale = self.credit_sale
                delivery_note_doc.credit_days = self.credit_days
                delivery_note_doc.payment_terms = self.payment_terms
                delivery_note_doc.payment_mode = self.payment_mode
                delivery_note_doc.payment_account = self.payment_account
                delivery_note_doc.remarks = self.remarks
                delivery_note_doc.gross_total = self.gross_total
                delivery_note_doc.total_discount_in_line_items = self.total_discount_in_line_items
                delivery_note_doc.tax_total = self.tax_total
                delivery_note_doc.net_total = self.net_total
                delivery_note_doc.round_off = self.round_off
                delivery_note_doc.rounded_total = self.rounded_total
                delivery_note_doc.terms = self.terms
                delivery_note_doc.terms_and_conditions = self.terms_and_conditions
                delivery_note_doc.auto_generated_from_delivery_note = True
                delivery_note_doc.address_line_1 = self.address_line_1
                delivery_note_doc.address_line_2 = self.address_line_2
                delivery_note_doc.area_name = self.area_name
                delivery_note_doc.country = self.country
                delivery_note_doc.quotation = self.quotation
                delivery_note_doc.sales_order = self.sales_order
                
                # Remove existing child table values
                # frappe.db.sql("DELETE FROM `tabDelivery Note Item` where parent=%s", delivery_note_name)
                # Manually update the sales invoice details
               
                
                # Refresh document
                # delivery_note_doc = frappe.get_doc('Delivery Note', delivery_note_name)
                
                # target_items = []
                
                # for item in self.items:
                #     target_item = delivery_note_doc.append('items', {} )
                #     frappe.copy_doc(item, target_item)
                #     target_items.append(target_item)
                    
                delivery_note_doc.save()
                # Remove existing child table values
                frappe.db.sql("DELETE FROM `tabDelivery Note Item` where parent=%s", delivery_note_name)
                
                # target_items = []
                
                idx = 0
                
                for item in self.items:                                        
                    idx = idx + 1
                    delivery_note_item = frappe.new_doc("Delivery Note Item")
                    delivery_note_item.warehouse = item.warehouse
                    delivery_note_item.item = item.item
                    delivery_note_item.item_code = item.item_code
                    delivery_note_item.display_name = item.display_name
                    delivery_note_item.qty =item.qty
                    delivery_note_item.unit = item.unit
                    delivery_note_item.rate = item.rate
                    delivery_note_item.base_unit = item.base_unit
                    delivery_note_item.qty_in_base_unit = item.qty_in_base_unit
                    delivery_note_item.rate_in_base_unit = item.rate_in_base_unit
                    delivery_note_item.conversion_factor = item.conversion_factor
                    delivery_note_item.rate_included_tax = item.rate_included_tax
                    delivery_note_item.rate_excluded_tax = item.rate_excluded_tax
                    delivery_note_item.gross_amount = item.gross_amount
                    delivery_note_item.tax_excluded = item.tax_excluded
                    delivery_note_item.tax = item.tax
                    delivery_note_item.tax_rate = item.tax_rate
                    delivery_note_item.tax_amount = item.tax_amount
                    delivery_note_item.discount_percentage = item.discount_percentage
                    delivery_note_item.discount_amount = item.discount_amount
                    delivery_note_item.net_amount = item.net_amount
                    delivery_note_item.unit_conversion_details = item.unit_conversion_details
                    delivery_note_item.idx = idx                    
                    
                    delivery_note_doc.append('items', delivery_note_item )                    
                    #  target_items.append(target_item)
                
                delivery_note_doc.save()
                
                frappe.msgprint("Delivery Note for the Sales Invoice updated successfully.")
                
            else:
                delivery_note = self.__dict__
                delivery_note['doctype'] = 'Delivery Note'
                # delivery_note['against_sales_invoice'] = delivery_note['name']
                # delivery_note['name'] = delivery_note_name        
                delivery_note['naming_series'] = ""
                delivery_note['posting_date'] = self.posting_date
                delivery_note['posting_time'] = self.posting_time

                delivery_note['auto_generated_from_sales_invoice'] = 1

                for item in delivery_note['items']:
                    item.doctype = "Delivery Note Item"    
                    item._meta = ""        

                delivery_note_doc = frappe.get_doc(delivery_note).insert()
                frappe.db.commit()
                delivery_note_name = delivery_note_doc.name            
            
        # Rename the delivery note to the original dnoNo which is deleted
        # if(do_exists):
        #     frappe.rename_doc('Delivery Note', doNo.name, delivery_note_name)
        
        # do = frappe.get_doc('Delivery Note', delivery_note_name)
        si = frappe.get_doc('Sales Invoice',si_name)
        
        print("do_exists")
        print(do_exists)
        
        # if frappe.db.exists('Sales Invoice Delivery Notes', {'parent': self.name}):    
        if(not do_exists):
            si.append('delivery_notes', {'delivery_note': delivery_note_name})

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
            item.delivery_note_item_reference_no = delivery_note_doc.items[index].name
            index = index + 1

        # Need to remove the next line to set auto_save_delivery_note
        si.auto_save_delivery_note = True
        si.save()
        print("From end of auto gen delivery note")
    
    def cancel_delivery_note_for_sales_invoice(self):
        print("cancel delivbery note for sales invoice")
        delivery_note = frappe.get_value("Sales Invoice Delivery Notes",{'parent': self.name}, ['delivery_note'])
        do = frappe.get_doc('Delivery Note',delivery_note)        
        do.cancel()
        frappe.msgprint("Sales invoice and delivery note cancelled successfully")

        # frappe.msgprint("Delivery Note cancelled")
        