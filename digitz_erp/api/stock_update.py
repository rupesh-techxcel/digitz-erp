import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now

def do_recalculate_stock_ledgers(stock_recalc_voucher, posting_date, posting_time):
    
    
    # This method is hitting from the background worker and need to ignore the negative_stock_checking, Means it will allow negative stock in any case.
    
    allow_negative_stock = True
    
    posting_date_time = get_datetime(str(posting_date) + " " + str(posting_time))  		
            
    default_company = frappe.db.get_single_value("Global Settings",'default_company')
            
    company_info = frappe.get_value("Company",default_company,['allow_negative_stock'], as_dict = True)
    
    # allow_negative_stock = company_info.allow_negative_stock
    
    # if(not allow_negative_stock):
    #     allow_negative_stock = False
        
    for record in stock_recalc_voucher.records:
        
        new_balance_qty = 0
        new_balance_value = 0
        new_valuation_rate = 0
        
        base_stock_ledger_name = ""
                
        if record.base_stock_ledger != "No Previous Ledger":
        
            base_stock_ledger = frappe.get_doc('Stock Ledger', record.base_stock_ledger)        	
            base_stock_ledger_name = base_stock_ledger.name
            
            new_balance_qty = base_stock_ledger.balance_qty
            new_balance_value = base_stock_ledger.balance_value
            new_valuation_rate = base_stock_ledger.valuation_rate
        
        next_stock_ledgers = frappe.get_list('Stock Ledger',{'item':record.item,
        'warehouse':record.warehouse, 'posting_date':['>', posting_date_time]}, 'name',order_by='posting_date')

        # Scenario 1- PUrchase Invoice - current row cancelled. For this assigned previous stock ledger balance to 'Stock Recalculate Voucher'
                
        log = ""

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
                                    
                sl.recalculated = True
                
                # Once qty adjusted exit for next item, since after manual entry subsequent entries are not considered
                sl.save()
                break;
            
            # Sales invoice included to favor Tab Sales
            if(sl.voucher == "Delivery Note" or sl.voucher== "Purchase Return" or sl.voucher== "Sales Invoice"):
                previous_balance_qty = new_balance_qty
                previous_balance_value = new_balance_value #Assign before change                    
                new_balance_qty = new_balance_qty - sl.qty_out
                new_balance_value = new_balance_qty * new_valuation_rate                    
                change_in_stock_value = new_balance_value - previous_balance_value
                sl.change_in_stock_value = change_in_stock_value
                sl.log = f"previous stock balance {previous_balance_qty}"
                
                # If there is a value change for stock, make adjustment in GL Posting
                # if(previous_stock_value != change_in_stock_value):
                #     gl_postings = frappe.get_list('GL Posting',{'voucher_type': sl.voucher,'voucher_no': sl.voucher_no},['name'])
                #     for gl_posting in gl_postings:
                #         gl = frappe.get_doc('GL Posting', gl_posting.name)
                #         gl.change_in_stock_value = change_in_stock_value
                #         gl.save()                            
                        
                # if(new_balance_qty<0 and allow_negative_stock== False):
                #     frappe.throw("Stock availability is not sufficiant to make this transaction, the delivery note " + sl.voucher_no + " cannot be fulfilled.")
                
                # update_purchase_usage_for_delivery_note(sl.voucher_no)
                                    
            if (sl.voucher == "Purchase Invoice" or sl.voucher == "Sales Return"):
                previous_balance_value = new_balance_value #Assign before change 
                new_balance_qty = new_balance_qty + sl.qty_in
                new_balance_value = new_balance_value  + (sl.qty_in * sl.incoming_rate)
                change_in_stock_value = new_balance_value - previous_balance_value
                sl.change_in_stock_value = change_in_stock_value
    
                if(new_balance_qty!=0): #Avoid divisible by zero
                    if sl.voucher == "Purchases Invoice":  #Avoid sales return to assign new_valuation_rate
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
                    # if(new_balance_qty<0 and  allow_negative_stock== False):
                    #     frappe.throw("Stock availability is not sufficiant to make this transaction, the delivery note " + sl.voucher_no + " cannot be fulfilled.")
            
            sl.balance_qty = new_balance_qty
            sl.balance_value = new_balance_value
            sl.valuation_rate = new_valuation_rate
            sl.save()

        if frappe.db.exists('Stock Balance', {'item':record.item,'warehouse': record.warehouse}):    
            frappe.db.delete('Stock Balance',{'item': record.item, 'warehouse': record.warehouse} )

        item_name,unit = frappe.get_value("Item", record.item,['item_name','base_unit'])
        new_stock_balance = frappe.new_doc('Stock Balance')	
        new_stock_balance.item = record.item
        new_stock_balance.item_name = item_name
        new_stock_balance.unit = unit
        
        new_stock_balance.warehouse = record.warehouse
        new_stock_balance.stock_qty = new_balance_qty
        new_stock_balance.stock_value = new_balance_value
        new_stock_balance.valuation_rate = new_valuation_rate

        new_stock_balance.insert()

        # item_name = frappe.get_value("Item", record.item,['item_name'])
        print("record.item")
        print(record.item)
        
        update_item_stock_balance(record.item)
    stock_recalc_voucher.status = 'Completed'
    stock_recalc_voucher.end_time = now()
    stock_recalc_voucher.save()
    

def recalculate_stock_ledgers(stock_recalc_voucher, posting_date, posting_time):
    do_recalculate_stock_ledgers(stock_recalc_voucher= stock_recalc_voucher, posting_date=posting_date, posting_time=posting_time)

        
def update_item_stock_balance(item):
    
    print("before udpate item stock balance")
    
    item_balances_in_warehouses = frappe.get_list('Stock Balance',{'item': item},['stock_qty','stock_value'])

    balance_stock_qty = 0
    balance_stock_value = 0

    if(item_balances_in_warehouses):
        for item_stock in item_balances_in_warehouses:
            if item_stock.stock_qty:
                balance_stock_qty = balance_stock_qty + item_stock.stock_qty

            if item_stock.stock_value:
                balance_stock_value = balance_stock_value + item_stock.stock_value
    
    item_to_update = frappe.get_doc('Item', item)	
            
    if(not item_to_update.stock_balance):	
    
        item_to_update.stock_balance = 0
        item_to_update.stock_value = 0
        
    item_to_update.stock_balance = balance_stock_qty
    item_to_update.stock_value = balance_stock_value                
    item_to_update.save()
    
    print("after udpate item stock balance")

def update_purchase_usage_for_delivery_note(delivery_note_no):
    
    delivery_note_doc = frappe.get_doc('Delivery Note', delivery_note_no)    
    do_posting_date = delivery_note_doc.posting_date
    delivery_note_items = frappe.get_list('Delivery Note Item',{'parent': delivery_note_no },['name','item_code','qty','rate'])
    
    frappe.db.delete("Purchase Stock Usage", {"delivery_note":delivery_note_no})
    frappe.db.commit()
    
    for item in delivery_note_items:
        
        # query = """SELECT p.name as p_name, pi.name as pi_name,pi.item_code,pi_item,pi.qty- sum(su.sold_qty) as qty  from `tabPurchase Invoice Item` as pi left   outer join `tabPurchase Stock Usage` su on su.purchase_invoice_item = pi.name and su.item_code= pi.item_code inner join `tabPurchase Invoice` p on p.name= pi.parent  WHERE pi.posting_date<={do_date} and  pi.item_code={item} pi.qty > sum(su.sold_qty) group by pi.name,pi.item_code,pi.item,pi.qty. p.name order by pi.posting_date""".format(item=item.item_code, do_date=do_posting_date)
        
        # result = frappe.db.sql(query, as_dict = True)
        
        
        query = """
        SELECT
            p.name AS p_name,
            pi.name AS pi_name,
            pi.item_code,
            pi.item,
            pi.qty - COALESCE(SUM(su.sold_qty), 0) AS qty
        FROM
            `tabPurchase Invoice Item` AS pi
        LEFT JOIN
            `tabPurchase Stock Usage` AS su
        ON
            su.purchase_invoice_item = pi.name AND su.item_code = pi.item_code
        INNER JOIN
            `tabPurchase Invoice` AS p
        ON
            p.name = pi.parent
        WHERE
            p.posting_date <= '{do_date}'
            AND pi.item_code = '{item_code}'
            AND pi.qty > COALESCE((SELECT SUM(sold_qty) FROM `tabPurchase Stock Usage` WHERE purchase_invoice_item = pi.name AND item_code = pi.item_code), 0)
        GROUP BY
            pi.name, pi.item_code, pi.item, pi.qty, p.name
        ORDER BY
            p.posting_date
        """.format(item_code=item.item, do_date=do_posting_date)
        

        result = frappe.db.sql(query, as_dict=True)
        qtyRequired = item.qty
        
        for result_item in result:
            if(result_item.qty > 0):
                # When purchase qty is less than qty required then need to iterate again.
                if(result_item.qty < qtyRequired):
                    # Insert a record in the tabPurchase Stock Usage table                    
                    su_doc = frappe.new_doc("Purchase Stock Usage")
                    su_doc.purchase_invoice = result_item.p_name
                    su_doc.purchase_invoice_item = result_item.pi_name
                    su_doc.item = result_item.item_code
                    su_doc.item_name = result_item.item
                    su_doc.delivery_note = delivery_note_no
                    su_doc.delivery_note_item = item.name
                    su_doc.sold_qty = result_item.qty
                    su_doc.insert()
                    qtyRequired = qtyRequired - result_item.qty
                else:
                    su_doc = frappe.new_doc("Purchase Stock Usage")
                    su_doc.purchase_invoice = result_item.p_name
                    su_doc.purchase_invoice_item = result_item.pi_name                    
                    su_doc.item_name = result_item.item
                    su_doc.item = result_item.item_code
                    su_doc.delivery_note = delivery_note_no
                    su_doc.delivery_note_item = item.name
                    su_doc.sold_qty = qtyRequired
                    su_doc.insert()
                    continue
