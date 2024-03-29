import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_sales_invoice_exists(sales_order):
   return frappe.db.exists('Sales Invoice', {'sales_order': sales_order})

@frappe.whitelist()
def get_delivery_note_exists(sales_order):
   return frappe.db.exists('Delivery Note', {'sales_order': sales_order})

@frappe.whitelist()
def get_pending_sales_orders_for_delivery_note(customer):
    so_query = """
        SELECT 
            `name` AS 'Sales Order', 
            `posting_date` AS 'Date', 
            `rounded_total` AS 'Amount' 
        FROM 
            `tabSales Order` 
        WHERE 
            `order_status` != 'Completed' 
            AND `customer` = %s 
            AND `docstatus` = 1 
            AND `name` NOT IN (
                SELECT 
                    `sales_order` 
                FROM 
                    `tabSales Invoice` 
                WHERE 
                    `docstatus` < 2
            )
    """

    sales_orders = frappe.db.sql(so_query, (customer,), as_dict=True)
    return sales_orders

@frappe.whitelist()
def check_pending_items_exists(sales_order):
    unsold_items_count_query = """select count(1) from `tabSales Order Item` where qty_in_base_unit > qty_sold_in_base_unit and parent = %s"""
    unsold_items_count = frappe.db.sql(unsold_items_count_query, (sales_order,))
    if unsold_items_count and unsold_items_count[0][0] > 0:
        return True
    else:
        return False
    

@frappe.whitelist()
def check_and_update_sales_order_status(document_name, doctype):

    print(document_name)

    sales_orders_query = ""

    if doctype == "Sales Invoice":
      sales_orders_query = """
      select si.sales_order from `tabSales Invoice` si
      inner join `tabSales Order` so on si.sales_order = so.name
      where si.name = %s and so.name is not null
      """
    elif doctype == "Delivery Note":
      sales_orders_query = """
      select dso.sales_order from `tabDelivery Note Sales Orders` dso
      inner join `tabSales Order` so on dso.sales_order = so.name
      where dso.parent = %s and so.name is not null
      """
    elif doctype == "Sales Return":
        # Using distinct to select unique sales orders affected by the sales return
        sales_orders_query = """
            select distinct so.name as sales_order from `tabSales Return Item` sri
            inner join `tabSales Return` sr on sr.name = sri.parent
            inner join `tabSales Invoice Item` sii on sii.name = sri.si_item_reference
            inner join `tabSales Invoice` si on si.name = sii.parent
            inner join `tabSales Order Item` soi on soi.name = sii.sales_order_item_reference_no
            inner join `tabSales Order` so on so.name = soi.parent
            where so.docstatus < 2 and si.docstatus < 2 and sr.name = %s
        """

    if sales_orders_query:
        sales_orders = frappe.db.sql(sales_orders_query, (document_name), as_dict=True)

        print(sales_orders)

        for sales_order in sales_orders:
            
            sales_order_name = sales_order.sales_order
            print("sales_order_name")
            print(sales_order_name)

            sales_order_items = frappe.db.sql("""
                SELECT name FROM `tabSales Order Item`
                WHERE parent = %s
            """, (sales_order_name,), as_dict=True)

            sold_any = False
            at_least_one_partial_sale = False
            excess_allocation = False
            
            print("sales order items")
            
            print(sales_order_items)

            for so_item_dict in sales_order_items:
                
                so_item_name = so_item_dict['name']
                so_item = frappe.get_doc("Sales Order Item", so_item_name)

                if so_item.qty_sold_in_base_unit and so_item.qty_sold_in_base_unit > 0:
                    sold_any = True
                    if so_item.qty_sold_in_base_unit < so_item.qty_in_base_unit:
                        at_least_one_partial_sale = True

                    # Check for excess allocation
                    if so_item.qty_sold_in_base_unit > so_item.qty_in_base_unit:
                        excess_allocation = True

            # Update the sales order status based on conditions
            if not sold_any:
                print("not sold_any")
                
                frappe.db.set_value("Sales Order", sales_order_name, "order_status", "Pending")

            elif at_least_one_partial_sale:
                
                print("at_least_one_partial_sale")
                
                frappe.db.set_value("Sales Order", sales_order_name, "order_status", "Partial")

            elif excess_allocation:
                
                print("excess allocation")
                
                frappe.msgprint(f"Warning: Sales Order {sales_order_name} contains one or more items with excess allocation.", alert=True)

            else:
                frappe.db.set_value("Sales Order", sales_order_name, "order_status", "Completed")

            frappe.msgprint("Order Status updated in the corresponding Sales Order.", alert=True)

@frappe.whitelist()
def update_sales_order_quantities_on_update(doc_si_or_do, forDeleteOrCancel=False):

   
   so_reference_any = False
   for item in doc_si_or_do.items:

      
      if not item.sales_order_item_reference_no:
            continue
      else:

         total_quantity_sold = 0

         if doc_si_or_do.doctype == "Sales Invoice":

            #Calculate quantities for the sales order item which is not included in this sales invoice line item
            total_quantity_sold_in_other_docs = frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_used_qty from `tabSales Invoice Item` sinvi inner join `tabSales Invoice` sinv on sinvi.parent= sinv.name WHERE sinvi.sales_order_item_reference_no=%s AND sinv.name !=%s and sinv.docstatus<2""",(item.sales_order_item_reference_no, doc_si_or_do.name))[0][0]

            # Calculate quantities from the delivery notes for the corresponing sales order line item
            total_quantity_sold_in_do = frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_used_qty from `tabDelivery Note Item` dinvi inner join `tabDelivery Note` dinv on dinvi.parent= dinv.name WHERE dinvi.sales_order_item_reference_no=%s and dinv.docstatus<2""",(item.sales_order_item_reference_no))[0][0]

            total_quantity_sold = (total_quantity_sold_in_other_docs if total_quantity_sold_in_other_docs else 0) + (total_quantity_sold_in_do if total_quantity_sold_in_do else 0)


         if doc_si_or_do.doctype == "Delivery Note":

               # Calculate quantities from the sales invoices for the corresponing sales order line item
            total_quantity_sold_in_si= frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_used_qty from `tabSales Invoice Item` sinvi inner join `tabSales Invoice` sinv on sinvi.parent= sinv.name WHERE sinvi.sales_order_item_reference_no=%s and sinv.docstatus<2""",(item.sales_order_item_reference_no))[0][0]

            #Calculate quantities for the sales order item which is not included in this delivery note line item
            total_quantity_sold_in_other_docs = frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_used_qty from `tabDelivery Note Item` dinvi inner join `tabDelivery Note` dinv on dinvi.parent= dinv.name WHERE dinvi.sales_order_item_reference_no=%s and dinv.name!=%s and dinv.docstatus<2""",(item.sales_order_item_reference_no, doc_si_or_do.name))[0][0]

            total_quantity_sold = (total_quantity_sold_in_other_docs if total_quantity_sold_in_other_docs else 0) + (total_quantity_sold_in_si if total_quantity_sold_in_si else 0)

         # Calculate total returned qty for the corresponding sales order item
         total_returned_qty_for_the_si_item = frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_returned_qty from `tabSales Return Item` sreti inner join `tabSales Return` sret on sreti.parent= sret.name WHERE sreti.si_item_reference in (select name from `tabSales Invoice Item` sit where sit.sales_order_item_reference_no=%s) and sret.docstatus<2""",(item.sales_order_item_reference_no))[0][0]

         total_quantity_sold = total_quantity_sold - (total_returned_qty_for_the_si_item if total_returned_qty_for_the_si_item else 0)   + (item.qty_in_base_unit if not forDeleteOrCancel else 0)

         so_item = frappe.get_doc("Sales Order Item", item.sales_order_item_reference_no)

         so_item.qty_sold_in_base_unit = total_quantity_sold

         so_item.save()
         so_reference_any = True

   if(so_reference_any):
      frappe.msgprint("Sold Qty of items in the corresponding Sales Order updated successfully.", indicator= "green", alert= True)

@frappe.whitelist()
def update_sales_order_quantities_for_sales_return_on_update(self, for_delete_or_cancel=False):

		so_reference_any = False
		for item in self.items:
			if not item.si_item_reference:
				continue
			else:

				pi_item = frappe.get_doc("Sales Invoice Item", item.si_item_reference)

				so_item_reference = pi_item.sales_order_item_reference_no

				if so_item_reference:

					# Get the total returned quantity for the purchase invoie item which occured for all purchase invoices with the po item reference, excluded the current purchase return qty
					total_returned_qty_not_in_this_sr = frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_returned_qty from `tabSurchase Return Item` sreti inner join `tabSales Return` sret on sreti.parent= sret.name WHERE sreti.si_item_reference in (select name from `tabPurchase Invoice Item` pit where pit.sales_order_item_reference_no=%s) AND sret.name !=%s and sret.docstatus<2""",(so_item_reference, self.name))[0][0]

					current_qty = item.qty_in_base_unit
					if for_delete_or_cancel:
						print("zero")
						current_qty = 0

					print("current_qty")
					print(current_qty)

					total_returned_qty = (total_returned_qty_not_in_this_sr if total_returned_qty_not_in_this_sr else 0 )+ current_qty

					print("total_returned_qty")
					print(total_returned_qty)

               # Sales Invoice Line Item Total
					total_used_qty_in_si_for_the_so_item = frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_used_qty from `tabSales Invoice Item` sinvi inner join `tabSales Invoice` sinv on sinvi.parent= sinv.name WHERE sinvi.sales_order_item_reference_no=%s and sinv.docstatus<2""",(so_item_reference))[0][0]

					total_used_qty_in_si_for_the_so_item = total_used_qty_in_si_for_the_so_item if total_used_qty_in_si_for_the_so_item else 0

               # Delivery Note Line Item Total
					total_used_qty_in_do_for_the_so_item = frappe.db.sql(""" SELECT SUM(qty_in_base_unit) as total_used_qty from `tabDelivery Note Item` dinvi inner join `tabDelvery Note` dinv on dinvi.parent= dinv.name WHERE dinvi.sales_order_item_reference_no=%s and sinv.docstatus<2""",(so_item_reference))[0][0]

					total_used_qty_in_do_for_the_so_item = total_used_qty_in_do_for_the_so_item if total_used_qty_in_do_for_the_so_item else 0

					total_qty_sold = total_used_qty_in_si_for_the_so_item + total_used_qty_in_do_for_the_so_item - total_returned_qty

					po_item = frappe.get_doc("Sales Order Item", so_item_reference)

					po_item.qty_sold_in_base_unit = total_qty_sold

					po_item.save()

					so_reference_any = True

		if(so_reference_any):
			frappe.msgprint("Sold Qty of items in the corresponding Sales Order updated successfully", indicator= "green", alert= True)

@frappe.whitelist()
def get_sales_order_items_pending(sales_orders):
    if isinstance(sales_orders, str):
        sales_orders = frappe.parse_json(sales_orders)
    items = []
    for sales_order in sales_orders:
        sales_order_items = frappe.get_all('Sales Order Item',
                                           filters={'parent': sales_order},
                                           fields=['name', 'item', 'qty', 'warehouse', 'item_name', 'display_name', 'unit', 'rate', 'base_unit',
                                                   'qty_in_base_unit', 'qty_sold_in_base_unit', 'rate_in_base_unit', 'conversion_factor', 
                                                   'rate_includes_tax', 'gross_amount', 'tax_excluded', 'tax_rate', 'tax_amount', 
                                                   'discount_percentage', 'discount_amount', 'net_amount'])
        for so_item in sales_order_items:
            so_item['sales_order_item_reference_no'] = so_item['name']
            so_item['qty'] = (so_item.get('qty_in_base_unit', 0) - so_item.get('qty_sold_in_base_unit', 0) )/ so_item.get('conversion_factor')
            so_item['qty_in_base_unit'] = so_item.get('qty_in_base_unit', 0) - so_item.get('qty_sold_in_base_unit', 0)
            
            items.append(so_item)

    return items