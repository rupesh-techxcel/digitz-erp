import frappe

@frappe.whitelist()
def check_invoices_for_purchase_order(purchase_order):
    
    po_in_pi = frappe.db.exists("Purchase Invoice",{"purchase_order":purchase_order})
    
    if(po_in_pi):        
        return True    
    else:
        print("return False")
        return False

# Before calling the below method it is supposed that the purchase order qty_purchased fiel 
# is already updated from purchase 
@frappe.whitelist()
def check_and_update_purchase_order_status(purchase_order_name):

    purchase_order = frappe.get_doc("Purchase Order", purchase_order_name)
    
    print("purchase order")
    print(purchase_order)
    
    purchase_order_items = frappe.get_list("Purchase Order Item", {'parent': purchase_order.name},['name'])
    
    purchased_any = False
    at_least_one_partial_purchase = False
    purchased_full = False #Not using for conditions
    
    print("purchase_order_items")
    print(purchase_order_items)
    
    for po_item_name in purchase_order_items:        
        
        po_item = frappe.get_doc("Purchase Order Item", po_item_name)
        print("po_tem")
        print(po_item)
        print(po_item.qty)
        print(po_item.qty_purchased)
        
        # Only negative cases checks here
        if po_item.qty_purchased:
            if po_item.qty_purchased > 0:
                purchased_any = True
                
            if po_item.qty_purchased< po_item.qty:
                at_least_one_partial_purchase = True
        else:
            print("Partial else case")
            at_least_one_partial_purchase = True
        
                
    if purchased_any == False:        
        frappe.db.set_value("Purchase Order", purchase_order.name, {'order_status': "Pending"}) 
        print("1 set value")    
    elif at_least_one_partial_purchase == True:         
        frappe.db.set_value("Purchase Order", purchase_order.name, {'order_status': "Partial"})
        print("2 set  value") 
    else:       
       frappe.db.set_value("Purchase Order", purchase_order.name, {'order_status': "Completed"})
       print("3 set value. here")
       
    
        