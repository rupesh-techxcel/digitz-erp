# Copyright (c) 2024,   and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from digitz_erp.api.boq_api import copy_boq_items_to_original_boq_items
from datetime import datetime
from digitz_erp.api.project_api import update_project_advance_amount

class BOQAmendment(Document):
    
    def validate(self):     
        # Ensure at least one item is entered in the BOQ amendment
        if not self.boq_items or len(self.boq_items) == 0:
            frappe.throw(_("Please enter at least one item in the BOQ Amendment."))
               
        # Convert posting_date (string) to datetime.date
        posting_date_obj = datetime.strptime(self.posting_date, "%Y-%m-%d").date()

        # Convert posting_time (string) to datetime.time
        posting_time_obj = datetime.strptime(self.posting_time, "%H:%M:%S").time()

        # Combine date and time
        boq_amendment_datetime = datetime.combine(posting_date_obj, posting_time_obj)

        # Get related project using sales order linked to BOQ
        sales_order = frappe.db.get_value('Sales Order', {'boq': self.boq}, 'name')
                
           
        if(not sales_order):
            frappe.throw("Cannot identified the corresponding Sales Order for the BOQ")            
        else:
            project = frappe.db.get_value('Project',{'sales_order':sales_order},'name')
            
            if not project:
                frappe.throw("Cannot identified the corresponding project for the BOQ")                
            else:
                # Fetch progress entries for project to check for amendments
                progress_entries = []
                if project:
                    progress_entries = frappe.get_all(
                        'Progress Entry', filters={'project': project}, fields=['name', 'posting_date', 'posting_time']
                    )
                    
                    for entry in progress_entries:
                        
                        posting_date = str(entry.posting_date) if not isinstance(entry.posting_date, str) else entry.posting_date
                        entry_date_obj = datetime.strptime(posting_date, "%Y-%m-%d").date()

                        # Ensure posting_time is a string
                        posting_time = str(entry.posting_time) if not isinstance(entry.posting_time, str) else entry.posting_time
                        entry_time_obj = datetime.strptime(posting_time, "%H:%M:%S").time()
                        
                        progress_entry_datetime = datetime.combine(entry_date_obj, entry_time_obj)
                        
                        if progress_entry_datetime > boq_amendment_datetime:
                            frappe.throw(f"Progress entry '{entry.name}' exists after the BOQ Amendment date and time {self.posting_date} {self.posting_time}. Amendment not allowed.")

                # Deduction validation: check if items in BOQ Amendment are used in any progress entries
                if self.option == 'Deduction' and project:
                    used_in_progress_entries = set()
                    for entry in progress_entries:
                        progress_entry_doc = frappe.get_doc('Progress Entry', entry.name)
                        for item in progress_entry_doc.progress_entry_items:
                            used_in_progress_entries.add(item.item)

                    # Find items in boq_items that are in progress entries
                    used_items = [item.item for item in self.boq_items if item.item in used_in_progress_entries]
                    if used_items:
                        frappe.throw(
                            f"The following items cannot be deducted as they are used in progress entries: {', '.join(used_items)}"
                        )

                # Logic for 'Addition' option
                if self.option == 'Addition':
                    boq_doc = frappe.get_doc('BOQ', self.boq)
                    existing_items = {item.item for item in boq_doc.boq_items}

                    # Track items used in progress entries
                    used_in_progress_entries = set()
                    if project:
                        for entry in progress_entries:
                            progress_entry_doc = frappe.get_doc('Progress Entry', entry.name)
                            for item in progress_entry_doc.progress_entry_items:
                                used_in_progress_entries.add(item.item)

                    for item in self.boq_items:
                        # Check if item is already in the progress entries
                        if item.item in used_in_progress_entries:
                            frappe.throw(f"Item '{item.item}' cannot be added because it is used in progress entries.")
                        
                        # Check for duplicate items in BOQ
                        if item.item in existing_items:
                            frappe.throw(f"Item '{item.item}' already exists in the BOQ items.")
                            
        self.validate_deduction()
        
    def validate_deduction(self):
        
        if self.option == 'Deduction':
            
            boq_doc = frappe.get_doc("BOQ", self.boq)

            # Create a set of item codes from boq_original_items for quick lookup
            original_items = {original_item.item for original_item in boq_doc.original_boq_items}

            # Validate each item in boq_items against boq_original_items
            for boq_item in self.boq_items:
                if boq_item.item not in original_items:
                    frappe.throw(f"Item {boq_item.item} is not present in BOQ Original Items, so it cannot be processed.")
                    
    def on_cancel(self):
        frappe.throw("Cannot cancel the BOQ Amendment.")
 
    def on_submit(self):    
        # Copy the BOQ items to the original items upon submission
        result = copy_boq_items_to_original_boq_items(self.boq)

        # Show success message if copy was successful
        if result and result.get('status') == 'success':
            frappe.msgprint(result.get('message'), alert=True)

        # Load the related BOQ document for modification
        boq_doc = frappe.get_doc('BOQ', self.boq)

        # Load the related Sales Order document
        sales_order_doc = frappe.get_doc("Sales Order", {'boq': self.boq})
        
        sales_orders_updated = False

        if self.option == 'Deduction':
            # Remove items in BOQ amendment from BOQ if marked for deduction
            for item in self.boq_items:
                boq_item_to_delete = next((boq_item for boq_item in boq_doc.boq_items if boq_item.item == item.item), None)
                
                if boq_item_to_delete:
                    # Append the deleted item to the items_deleted table
                    boq_doc.append("items_deleted", {
                        "item": boq_item_to_delete.item,
                        "description": boq_item_to_delete.description,
                        "quantity": boq_item_to_delete.quantity,
                        "item_name": boq_item_to_delete.item_name,
                        "item_group": boq_item_to_delete.item_group,
                        "item_group_description": boq_item_to_delete.item_group_description,
                        "unit": boq_item_to_delete.unit,
                        "rate": boq_item_to_delete.rate,
                        "rate_includes_tax": boq_item_to_delete.rate_includes_tax,
                        "tax": boq_item_to_delete.tax,
                        "tax_rate": boq_item_to_delete.tax_rate,
                        "net_amount": boq_item_to_delete.net_amount,
                        "gross_amount": boq_item_to_delete.gross_amount,
                        "tax_amount": boq_item_to_delete.tax_amount
                    })
                    
                    # Remove the item from the BOQ items table
                    boq_doc.boq_items = [boq_item for boq_item in boq_doc.boq_items if boq_item != boq_item_to_delete]
                    
                    # Remove the item from the Sales Order items table
                    if sales_order_doc:
                        sales_order_doc.items = [so_item for so_item in sales_order_doc.items if so_item.boq_item != boq_item_to_delete.name]
                        sales_orders_updated = True

        elif self.option == 'Addition':
            # Add items in BOQ amendment to BOQ if marked for addition
            for item in self.boq_items:
                # Add to the 'addition items' collection
                new_row_for_addition = boq_doc.append('items_added', {})
                new_row_for_addition.item = item.item
                new_row_for_addition.description = item.description
                new_row_for_addition.item_name = item.item_name
                new_row_for_addition.item_group = item.item_group
                new_row_for_addition.item_group_description = item.item_group_description
                new_row_for_addition.quantity = item.quantity
                new_row_for_addition.unit = item.unit
                new_row_for_addition.rate = item.rate
                new_row_for_addition.rate_includes_tax = item.rate_includes_tax
                new_row_for_addition.tax_excluded = item.tax_excluded                            
                new_row_for_addition.tax = item.tax
                new_row_for_addition.tax_rate = item.tax_rate
                new_row_for_addition.rate_excluded_tax = item.rate_excluded_tax
                new_row_for_addition.gross_amount = item.gross_amount
                new_row_for_addition.tax_amount = item.tax_amount
                new_row_for_addition.net_amount = item.net_amount                
                
                # Add to the boq items
                new_row = boq_doc.append('boq_items', {})
                new_row.item = item.item
                new_row.description = item.description
                new_row.item_name = item.item_name
                new_row.item_group = item.item_group
                new_row.item_group_description = item.item_group_description
                new_row.quantity = item.quantity
                new_row.unit = item.unit
                new_row.rate = item.rate
                new_row.rate_includes_tax = item.rate_includes_tax
                new_row.tax_excluded = item.tax_excluded                            
                new_row.tax = item.tax
                new_row.tax_rate = item.tax_rate
                new_row.rate_excluded_tax = item.rate_excluded_tax
                new_row.gross_amount = item.gross_amount
                new_row.tax_amount = item.tax_amount
                new_row.net_amount = item.net_amount
                new_row.addition = True
                
                 # Add to the Sales Order items table
                if sales_order_doc:
                    sales_order_doc.append("items", {
                        "item": item.item,
                        "item_name": item.item_name,
                        "description": item.description,
                        "item_group": item.item_group,
                        "qty": item.quantity,
                        "uom": item.unit,
                        "rate": item.rate,
                        "rate_includes_tax": item.rate_includes_tax,
                        "tax_excluded" : item.tax_excluded,                         
                        "tax": item.tax,
                        "tax_rate": item.tax_rate,
                        "rate_excluded_tax": item.rate_excluded_tax,
                        "gross_amount": item.gross_amount,
                        "tax_amount": item.tax_amount,
                        "net_amount": item.net_amount,
                        "boq_item": new_row.name,  # Link to the BOQ item
                        "warehouse":sales_order_doc.warehouse
                    })
                    sales_orders_updated = True
            
        # Calculate and update the total BOQ amount after changes
        boq_doc.total_net_amount = sum(item.net_amount for item in boq_doc.boq_items)
        boq_doc.total_tax_amount = sum(item.tax_amount for item in boq_doc.boq_items)
        boq_doc.total_boq_amount =  sum(item.gross_amount for item in boq_doc.boq_items)

        # Save the BOQ document after modifications
        boq_doc.save(ignore_permissions=True)

        # Save the Sales Order document if it exists
        if sales_order_doc:
            sales_order_doc.save(ignore_permissions=True)
            self.update_sales_order_totals(sales_order_doc)
            self.update_project_values(sales_order_doc)
            
        if sales_orders_updated:            
            frappe.msgprint("The ameneded item(s) udpated in the Sales Order.", alert = True)
            
    def update_sales_order_totals(self,doc):
        """
        Calculate totals, taxes, and other amounts for the document.
        """
        
        print("Update calculations for Sales Order.")
        # Initialize totals
        gross_total = 0
        tax_total = 0
        net_total = 0
        discount_total = 0

        print("Iterating through the items to update the sales order")
        # Iterate through items
        for item in doc.get("items"):
            
            print("Sales Order Iitem ")
            # Initialize item amounts
            item.gross_amount = 0
            item.tax_amount = 0
            item.net_amount = 0
            item.warehosue = doc.warehouse

            # Check if rate includes tax
            if doc.rate_includes_tax:
                # Tax-inclusive rate logic
                if item.tax_rate > 0:
                    tax_in_rate = item.rate * (item.tax_rate / (100 + item.tax_rate))
                    item.rate_excluded_tax = item.rate - tax_in_rate
                    item.tax_amount = (item.qty * item.rate) * (item.tax_rate / (100 + item.tax_rate))
                else:
                    item.rate_excluded_tax = item.rate
                    item.tax_amount = 0

                item.net_amount = (item.qty * item.rate) - item.get("discount_amount", 0)
                item.gross_amount = item.net_amount - item.tax_amount
            else:
                # Tax-exclusive rate logic
                item.rate_excluded_tax = item.rate

                if item.tax_rate > 0:
                    item.tax_amount = ((item.qty * item.rate) - item.get("discount_amount", 0)) * (item.tax_rate / 100)
                    item.net_amount = ((item.qty * item.rate) - item.get("discount_amount", 0)) + item.tax_amount
                else:
                    item.tax_amount = 0
                    item.net_amount = (item.qty * item.rate) - item.get("discount_amount", 0)

                item.gross_amount = item.qty * item.rate_excluded_tax

            # Update totals
            gross_total += item.gross_amount
            tax_total += item.tax_amount
            discount_total += item.get("discount_amount", 0)

        # Handle additional discount
        additional_discount = doc.get("additional_discount", 0)
        if additional_discount is None:
            additional_discount = 0

        # Calculate net total after additional discount
        net_total = gross_total + tax_total - additional_discount

        # Calculate rounding adjustment
        if net_total != round(net_total):
            round_off = round(net_total) - net_total
            rounded_total = round(net_total)
        else:
            round_off = 0
            rounded_total = net_total

        # Update document totals
        doc.gross_total = gross_total
        doc.tax_total = tax_total
        doc.net_total = net_total
        doc.total_discount_in_line_items = discount_total
        doc.round_off = round_off
        doc.rounded_total = rounded_total

        # Refresh fields (if needed)
        # doc.notify_update()
        doc.save()
        
    def update_project_values(self,sales_order):
        project_name = frappe.get_value("Project", {"sales_order": sales_order.name}, "name")    
        if project_name:
            # Get the project document
            project = frappe.get_doc("Project", project_name)
            
            # Update project values
            project.project_value = sales_order.rounded_total
            project.project_gross_value = sales_order.gross_total
            
            # Save the project document
            project.save()
            # When project value changes advance percentage also needs to be recalculated.
            update_project_advance_amount(project_name)