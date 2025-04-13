import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, flt
import math

class BOQ(Document):
    
    def before_validate(self):
        
        if self.customer:
            self.prospect_or_customer_name = self.customer
        elif self.prospect:
            self.prospect_or_customer_name = self.prospect
            
    def on_update(self):        
        self.update_gross_total()        

    def update_gross_total(self):
        
        total_gross_amount  = 0
        total_tax = 0
        total_net_amount = 0
        
        for row in self.boq_items:
            total_gross_amount += row.gross_amount if row.gross_amount else 0
            total_tax += row.tax_amount if row.tax_amount else 0
            total_net_amount += row.net_amount if row.net_amount else 0
                
        self.total_boq_amount = total_gross_amount    
        self.total_tax_amount = total_tax
        self.total_net_amount = total_net_amount

    def validate(self):
        
        # Check if project_name is already used in another BOQ
        if self.project_name:
            existing_boq = frappe.db.exists(
                "BOQ", 
                {"project_name": self.project_name, "name": ["!=", self.name]}  # Exclude current BOQ
            )
            
            if existing_boq:
                frappe.throw("The project name '{0}' is already used in another BOQ. Please choose a different project.").format(self.project_name)
        
        # Check if project_short_name is already used in another BOQ
        if self.project_short_name:
            existing_boq_short = frappe.db.exists(
                "BOQ", 
                {"project_short_name": self.project_short_name, "name": ["!=", self.name]}  # Exclude current BOQ
            )
            
            if existing_boq_short:
                frappe.throw("The project short name '{0}' is already used in another BOQ. Please choose a different short name.").format(self.project_short_name)

        # Ensure no row in boq_items has a quantity of zero
        for row in self.boq_items:
            if row.quantity == 0:
                frappe.throw(("Row #{0}: Quantity cannot be zero. Please enter a valid quantity for item {1}.")
                        .format(row.idx, frappe.bold(row.item)))
  
@frappe.whitelist()
def check_boq(estimate):    
    return frappe.db.exists("BOQ", {"estimation_id": estimate})

@frappe.whitelist()
def create_boq(estimateid):
    estimation_doc = frappe.get_doc("Estimate", estimateid)
    boq_doc = frappe.new_doc("BOQ")
    boq_doc.project_name = estimation_doc.project_name
    boq_doc.project_short_name = estimation_doc.project_short_name
    boq_doc.date = nowdate()
    boq_doc.estimation_id = estimateid
    boq_doc.boq_table = []
    boq_doc.lead_from = estimation_doc.lead_from
    boq_doc.prospect = estimation_doc.prospect
    boq_doc.customer = estimation_doc.customer
    boq_doc.company = estimation_doc.company
    boq_doc.total_boq_amount = estimation_doc.estimate_total
    
    for row in estimation_doc.estimation_items:
        boq_doc.append("boq_items", {
            "item": row.item,
            "item_group": row.group_item,
            "item_group_description": row.group_description,
            "item_name": row.item_name,
            "description": row.description,
            "quantity": row.quantity,
            "area": row.area,
            "perimeter": row.perimeter,
            "rate": row.boq_rate, 
            "gross_amount": row.boq_amount,           
        })
    boq_doc.insert()
    return boq_doc.name

@frappe.whitelist()
def update_boq(boq_id, estimateid):
    
    print(boq_id)
    print(boq_id)
    print("estimateid")
    print(estimateid)
    
    estimation_doc = frappe.get_doc("Estimate", estimateid)
    boq_doc = frappe.get_doc("BOQ", boq_id)

    # Create a dictionary of existing BOQ items by item code for easy lookup
    boq_items_dict = {row.item: row for row in boq_doc.boq_items}

    # Initialize total BOQ amount
    total_boq_amount = 0.0
    total_tax_amount = 0.0
    total_net_amount = 0.0

    # Loop through estimation items and update only existing items in BOQ
    for est_item in estimation_doc.estimation_items:
        # Check if the item from the estimate exists in the BOQ
        if est_item.item in boq_items_dict:
            # If the item exists in BOQ, update its fields
            boq_row = boq_items_dict[est_item.item]

            # Update rate and gross_amount
            boq_row.rate = round(est_item.boq_rate, 2)
            
            # Check if tax is excluded
            if boq_row.tax_excluded:
                # If tax is excluded, no tax calculations, set gross_amount and net_amount directly
                boq_row.gross_amount = round(est_item.boq_amount, 2)
                boq_row.net_amount = round(est_item.boq_amount, 2)
                boq_row.tax_amount = 0.0  # No tax amount for tax-excluded items
            else:
                # If tax is not excluded, handle tax calculations based on rate_included_tax
                if boq_row.rate_includes_tax:
                    # Calculate rate_excluded_tax by removing the tax portion from rate
                    boq_row.rate_excluded_tax = round(boq_row.rate / (1 + (boq_row.tax_rate / 100)), 2)

                    # Calculate tax_amount as the difference between rate and rate_excluded_tax
                    boq_row.tax_amount = round(boq_row.rate - boq_row.rate_excluded_tax, 2)

                    # Set gross_amount excluding tax
                    boq_row.gross_amount = round(est_item.boq_amount / (1 + (boq_row.tax_rate / 100)), 2)

                    # Set net_amount as the original amount (including tax)
                    boq_row.net_amount = round(est_item.boq_amount, 2)
                else:
                    # If rate does not include tax, set rate_excluded_tax to rate directly
                    boq_row.rate_excluded_tax = round(boq_row.rate, 2)
                    boq_row.gross_amount = round(est_item.boq_amount, 2)
                    boq_row.tax_amount = round(boq_row.gross_amount * (boq_row.tax_rate / 100), 2)
                    boq_row.net_amount = round(boq_row.gross_amount + boq_row.tax_amount, 2)

            print("boq_row.item")
            print(boq_row.item)
            
            print("boq_row.net_amount")
            print(boq_row.net_amount)
            print("boq_row.tax_amount")
            print(boq_row.tax_amount)
            print("boq_row.gross_amount")
            print(boq_row.gross_amount)
            # Accumulate the total amount
            total_boq_amount += boq_row.gross_amount
            total_tax_amount += boq_row.tax_amount
            total_net_amount += boq_row.net_amount
            

    # Update the total BOQ amount in the parent BOQ document
    boq_doc.total_boq_amount = round(total_boq_amount, 2)
    boq_doc.total_net_amount = round(total_net_amount,2)
    boq_doc.total_tax_amount = round(total_tax_amount,2)
    boq_doc.save(ignore_permissions=True)

    # Commit the changes to the database
    frappe.db.commit()
    frappe.msgprint("The BOQ corresponding to the estimate has been successfully updated with the estimated values.", alert=True)

    return boq_doc.name


