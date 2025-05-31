import frappe
from frappe.model.document import Document
from digitz_erp.api.boq_api import update_boq_execution_start_time,update_boq_execution_end_time,update_boq_execution_times

class WorkOrder(Document):

    def on_update(self):
        
        # Update BOQ Execution Items when the Work Order is updated
        self.update_boq_execution_with_qty_used_in_wo()

        # Handle updates for BOQ Execution based on field changes
        self.handle_boq_execution_updates()

    def on_update_after_submit(self):
        # Handle updates for BOQ Execution based on field changes
        self.handle_boq_execution_updates()

    def handle_boq_execution_updates(self):
        # Get the document before save to compare field values
        previous_doc = self.get_doc_before_save()
        
        if not previous_doc:
            print("No previous doc found")
            return

        # Check if 'start_date' or 'start_time' has changed while status is "In Process"
        if self.status == "In Process" and (self.start_date != previous_doc.start_date or self.start_time != previous_doc.start_time):
            update_boq_execution_start_time(self.boq_execution)

        # Check if 'end_date' or 'end_time' has changed while status is "Completed"
        if self.status == "Completed" and (self.end_date != previous_doc.end_date or self.end_time != previous_doc.end_time):
            print("Calling update_boq_execution_end_time from handle_boq_execution_updates")
            update_boq_execution_end_time(self.boq_execution)            
   
    def on_trash(self):        
       
        # For cancelled document boq the following code is not required to run since it is already running  in the on_cancel event
        # And qty_produced is not required to recalculate, for documents with draft mode, because it can be created only for submitted documents, by means of 'Complete Work Order' button inthe user interface
        if self.docstatus !=2:
            self.update_boq_execution_with_qty_used_in_wo(is_deleting=True)   
            update_boq_execution_times(self.name)     
    
    def on_cancel(self):
        # Update BOQ Execution Items when the Work Order is deleted
        self.update_boq_execution_with_qty_used_in_wo(is_deleting=True)
        self.update_boq_execution_with_qty_produced_in_wo(is_deleting=True)  
        update_boq_execution_times(self.name)      

    def update_boq_execution_with_qty_used_in_wo(self, is_deleting=False):
                
        boq_execution_doc = frappe.get_doc('BOQ Execution', self.boq_execution)
        
        for boq_execution_item_doc in boq_execution_doc.boq_execution_items:
            boq_item = boq_execution_item_doc.item
            total_quantity_used = 0
            
            # Get parent work orders for the relevant item
            work_order_names = frappe.get_all(
                'Work Order Item',
                filters={'item': boq_item, 'parent': ['!=', self.name]},  # Exclude the current work order
                fields=['parent']
            )

            # Extract work order names and filter out canceled work orders
            completed_work_orders = [
                wo['parent'] for wo in work_order_names
                if frappe.get_value('Work Order', wo['parent'], 'docstatus') != 2  # Exclude canceled work orders
            ]

            # Fetch quantities from non-canceled completed work orders
            other_work_order_items = frappe.get_all(
                'Work Order Item',
                filters={'item': boq_item, 'parent': ['in', completed_work_orders]},
                fields=['quantity']
            )

            total_quantity_used += sum(work_order_item['quantity'] for work_order_item in other_work_order_items)
            
            if not is_deleting:
                current_work_order_item = next((item for item in self.work_order_items if item.item == boq_item), None)
                if current_work_order_item:
                    total_quantity_used += current_work_order_item.quantity
            
            # Explicitly mark field as changed
            boq_execution_item_doc.db_set('quantity_in_work_order', total_quantity_used, update_modified=False)

        # Save BOQ Execution document after updating child items
        try:
            boq_execution_doc.save()
            frappe.db.commit()
            print("BOQ Execution saved successfully.")
        except Exception as e:
            print("Error saving BOQ Execution:", e)


    def update_boq_execution_with_qty_produced_in_wo(self, is_deleting=False):
        # Ensure the BOQ Execution field is set in the Work Order
        if not self.boq_execution:
            frappe.throw("BOQ Execution is not linked to this Work Order.")

        # Fetch the BOQ Execution document corresponding to the Work Order
        boq_execution_doc = frappe.get_doc('BOQ Execution', self.boq_execution)

        print("boq_execution_doc", boq_execution_doc)

        # Iterate through each BOQ Execution Item linked to the BOQ Execution document
        for boq_execution_item_doc in boq_execution_doc.boq_execution_items:
            
            print("boq_execution_item_doc", boq_execution_item_doc)
            
            item = boq_execution_item_doc.item
            
            print("item", item)
            
            # Calculate total produced quantity for this BOQ Execution Item
            total_produced = 0
            
            # Get completed work orders
            completed_work_orders = self.get_completed_work_orders() or []

            # Extract the names of completed work orders from the list of dictionaries
            completed_work_order_names = [wo['name'] for wo in completed_work_orders]

            print("completed_work_order_names", completed_work_order_names)

            # Fetch all completed work order items for this BOQ Execution Item, excluding the current work order
            completed_work_order_items = frappe.get_all(
                'Work Order Item',
                filters={
                    'item': item,
                    'parent': ['in', completed_work_order_names]  # Use the extracted names
                },
                fields=['quantity']
            )

            print("completed_work_order_items", completed_work_order_items)
            
            # Sum quantities from completed work orders
            total_produced += sum(wo_item['quantity'] for wo_item in completed_work_order_items)

            print("total_produced after completed work orders", total_produced)
            
            if not is_deleting and self.status == "Completed":
                # Include current work order item quantity
                current_work_order_item = frappe.get_all(
                    'Work Order Item',
                    filters={'item': item, 'parent': self.name},
                    fields=['quantity']
                )
                
                total_produced += sum(wo_item['quantity'] for wo_item in current_work_order_item)
                print("total_produced after including current work order", total_produced)

            # Update the produced_quantity field directly in the database
            boq_execution_item_doc.db_set('produced_quantity', total_produced, update_modified=False)

            # Calculate the balance quantity
            quantity = boq_execution_item_doc.quantity  # Use the quantity field directly
            balance_quantity = quantity - total_produced
            
            print("balance_quantity")
            print(balance_quantity)
            
            # Update the balance_quantity field in the database
            boq_execution_item_doc.db_set('balance_quantity', balance_quantity, update_modified=False)

        # Commit all changes
        frappe.db.commit()


    def get_completed_work_orders(self):
        # Fetch completed and submitted work orders, excluding the current one
        return frappe.get_all(
            'Work Order',
            filters={
                'status': 'Completed',
                'docstatus': 1,  # Only include submitted work orders
                'name': ['!=', self.name]  # Exclude the current work order
            },
            fields=['name']
        )

