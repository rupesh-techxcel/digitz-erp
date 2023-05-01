import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now

def recalculate_stock_ledgers(stock_recalc_voucher, posting_date, posting_time):
        
        posting_date_time = get_datetime(str(posting_date) + " " + str(posting_time))  		
                
        default_company = frappe.db.get_single_value("Global Settings",'default_company')
                
        company_info = frappe.get_value("Company",default_company,['allow_negative_stock'], as_dict = True)
        
        allow_negative_stock = company_info.allow_negative_stock
        
        if(not allow_negative_stock):
            allow_negative_stock = False
            
        for record in stock_recalc_voucher.records:
            
            new_balance_qty = 0
            new_balance_value = 0
            new_valuation_rate = 0
            
            if record.base_stock_ledger != "No Previous Ledger":
            
                base_stock_ledger = frappe.get_doc('Stock Ledger', record.base_stock_ledger)        	
                new_balance_qty = base_stock_ledger.balance_qty
                new_balance_value = base_stock_ledger.balance_value
                new_valuation_rate = base_stock_ledger.valuation_rate
            
            next_stock_ledgers = frappe.get_list('Stock Ledger',{'item':record.item,
			'warehouse':record.warehouse, 'posting_date':['>', posting_date_time]}, 'name',order_by='posting_date')
   
			# Scenario 1- PUrchase Invoice - current row cancelled. For this assigned previous stock ledger balance to 'Stock Recalculate Voucher'

            for sl_name in next_stock_ledgers:
                
                sl = frappe.get_doc('Stock Ledger', sl_name)                
                qty_in = 0
                qty_out = 0
                previous_stock_value = sl.change_in_stock_value
                
                # Exit the loop if there is a manual stock entry, since the manual stock entry is considered as corrected stock entry
                if(sl.voucher == "Stock Reconciliation"):
                    if(sl.balance_qty > new_balance_qty):
                        qty_in = sl.balance_qty - new_balance_qty
                    else:
                        qty_out = new_balance_qty -sl.balance_qty
                
                    sl.qty_in = qty_in
                    sl.qty_out = qty_out
                    
                    # Previous stock value difference
                    previous_balance_value = new_balance_value #Assign before change        
                    sl.change_in_stock_value =   (sl.balance_value - previous_balance_value) 
                                        
                    new_valuation_rate = sl.valuation_rate                    
                    new_balance_qty = sl.balance_qty
                    new_balance_value = sl.balance_value                    
                                        
                    
                    # Once qty adjusted exit for next item, since after manual entry subsequent entries are not considered
                    sl.save()
                    break;
				
                if(sl.voucher == "Delivery Note"):
                    previous_balance_value = new_balance_value #Assign before change                    
                    new_balance_qty = new_balance_qty - sl.qty_out
                    new_balance_value = new_balance_qty * new_valuation_rate                    
                    change_in_stock_value = new_balance_value - previous_balance_value
                    sl.change_in_stock_value = change_in_stock_value
                    if(previous_stock_value != change_in_stock_value):
                        gl_postings = frappe.get_list('GL Posting',{'voucher_type': 'Delivery Note','voucher_no': sl.voucher_no},['name'])
                        for gl_posting in gl_postings:
                            gl = frappe.get_doc('GL Posting', gl_posting.name)
                            gl.change_in_stock_value = change_in_stock_value
                            gl.save()                            
                            
                    if(new_balance_qty<0 and allow_negative_stock== False):
                        frappe.throw("Stock availability is not sufficiant to make this transaction, the delivery note " + sl.voucher_no + " cannot be fulfilled.")
                                        
                if (sl.voucher == "Purchase Invoice"):
                    previous_balance_value = new_balance_value #Assign before change 
                    new_balance_qty = new_balance_qty + sl.qty_in
                    new_balance_value = new_balance_value  + (sl.qty_in * sl.incoming_rate)
                    change_in_stock_value = new_balance_value - previous_balance_value
                    sl.change_in_stock_value = change_in_stock_value
     
                    if(new_balance_qty!=0): #Avoid divisible by zero
                        new_valuation_rate = new_balance_value/ new_balance_qty
                        
                if(sl.voucher == "Stock Transfer"):
                    
                    previous_balance_value = new_balance_value #Assign before change 
                    if(sl.qty_in > 0):
                        new_balance_qty = new_balance_qty + sl.qty_in
                        new_balance_value = new_balance_value  + (sl.qty_in * sl.incoming_rate)
                        change_in_stock_value = new_balance_value - previous_balance_value
                        sl.change_in_stock_value = change_in_stock_value
                    elif (sl.qty_out>0):                    
                        new_balance_qty = new_balance_qty - sl.qty_out
                        new_balance_value = new_balance_qty * new_valuation_rate                    
                        change_in_stock_value = new_balance_value - previous_balance_value
                        sl.change_in_stock_value = change_in_stock_value
                        if(new_balance_qty<0 and  allow_negative_stock== False):
                            frappe.throw("Stock availability is not sufficiant to make this transaction, the delivery note " + sl.voucher_no + " cannot be fulfilled.")
				
                sl.balance_qty = new_balance_qty
                sl.balance_value = new_balance_value
                sl.valuation_rate = new_valuation_rate
                sl.save()
    
            if frappe.db.exists('Stock Balance', {'item':record.item,'warehouse': record.warehouse}):    
                frappe.db.delete('Stock Balance',{'item': record.item, 'warehouse': record.warehouse} )

            item_name,unit = frappe.get_value("Item", record.item,['item_name','base_unit'])
            frappe.msgprint(unit)
            print(unit)
            
            new_stock_balance = frappe.new_doc('Stock Balance')	
            new_stock_balance.item = record.item
            new_stock_balance.unit = unit
            
            new_stock_balance.warehouse = record.warehouse
            new_stock_balance.stock_qty = new_balance_qty
            new_stock_balance.stock_value = new_balance_value
            new_stock_balance.valuation_rate = new_valuation_rate

            new_stock_balance.insert()

            item_name = frappe.get_value("Item", record.item,['item_name'])
            update_item_stock_balance(item_name)
        stock_recalc_voucher.status = 'Completed'
        stock_recalc_voucher.end_time = now()
        stock_recalc_voucher.save()
        
def update_item_stock_balance(item_name):
     
        item_balances_in_warehouses = frappe.get_list('Stock Balance',{'item': item_name},['stock_qty','stock_value'])
  
        balance_stock_qty = 0
        balance_stock_value = 0

        if(item_balances_in_warehouses):
            for item_stock in item_balances_in_warehouses:
                if item_stock.stock_qty:
                    balance_stock_qty = balance_stock_qty + item_stock.stock_qty

                if item_stock.stock_value:
                    balance_stock_value = balance_stock_value + item_stock.stock_value
	
		
        item_to_update = frappe.get_doc('Item', item_name)	
                
        if(not item_to_update.stock_balance):	
        
            item_to_update.stock_balance = 0
            item_to_update.stock_value = 0
            
        item_to_update.stock_balance = balance_stock_qty
        item_to_update.stock_value = balance_stock_value                
        item_to_update.save()	