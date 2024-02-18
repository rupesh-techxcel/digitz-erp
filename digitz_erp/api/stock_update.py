import frappe
from frappe.utils import get_datetime
from frappe.utils.data import now
from datetime import datetime, timedelta

def do_recalculate_stock_ledgers(stock_recalc_voucher, posting_date, posting_time):
    
    
    # This method is hitting from the background worker and need to ignore the negative_stock_checking, Means it will allow negative stock in any case.
    
    allow_negative_stock = True
    
    posting_date_time = get_datetime(str(posting_date) + " " + str(posting_time)) if posting_date and posting_time else None 		
            
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
            
            # For additional_stock there is no posting_date and time passing in
            if posting_date_time is None:
                posting_date_time = base_stock_ledger.posting_date
        
        next_stock_ledgers = frappe.get_list('Stock Ledger',{'item':record.item,
        'warehouse':record.warehouse, 'posting_date':['>', posting_date_time]}, 'name',order_by='posting_date')

        # Scenario 1- Purchase Invoice - current row cancelled. For this assigned previous stock ledger balance to 'Stock Recalculate Voucher'
                
        log = ""

        for sl_name in next_stock_ledgers:            
            new_balance_qty,new_valuation_rate,new_balance_value= update_stock_ledger_values(sl_name, new_balance_qty,new_valuation_rate, new_balance_value,for_reposting=False)

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
        
        update_stock_balance_in_item(record.item)
        
    stock_recalc_voucher.status = 'Completed'
    stock_recalc_voucher.end_time = now()
    stock_recalc_voucher.save()
    

def recalculate_stock_ledgers(stock_recalc_voucher, posting_date, posting_time):
    do_recalculate_stock_ledgers(stock_recalc_voucher= stock_recalc_voucher, posting_date=posting_date, posting_time=posting_time)
    
def update_all_item_stock_balances():
    
    print("from update all item stock balances")
    item_stock_balances = frappe.db.sql("""select item,warehouse,sum(qty_in)- sum(qty_out) as balance_qty from `tabStock Ledger` group by item,warehouse""",as_dict = True)
    
    for record in item_stock_balances:
        
        print("item")
        print(record.item)
        print("warehouse")
        print(record.warehouse)
        
        if frappe.db.exists('Stock Balance', {'item':record.item,'warehouse': record.warehouse}):    
            frappe.db.delete('Stock Balance',{'item': record.item, 'warehouse': record.warehouse} )

        item_name,unit = frappe.get_value("Item", record.item,['item_name','base_unit'])
        new_stock_balance = frappe.new_doc('Stock Balance')	
        new_stock_balance.item = record.item
        new_stock_balance.item_name = item_name
        new_stock_balance.unit = unit
        
        new_stock_balance.warehouse = record.warehouse
        new_stock_balance.stock_qty = record.balance_qty
        
       # Fetch the latest valuation_rate and balance_value for the given item
        balance_values_query = """
        SELECT valuation_rate, balance_value
        FROM `tabStock Ledger`
        WHERE item=%s AND posting_date = (
            SELECT MAX(posting_date)
            FROM `tabStock Ledger`
            WHERE item=%s
        ) ORDER BY posting_time DESC, creation DESC
        LIMIT 1
        """
        # Execute the query
        balance_values = frappe.db.sql(balance_values_query, (record.item, record.item), as_dict=True)

        # Check if any result is returned and then access the values
        if balance_values:
            # Since the result is a list of dictionaries, access the first item
            balance_value_dict = balance_values[0]
            
            new_stock_balance.stock_value = balance_value_dict.get('balance_value')
            new_stock_balance.valuation_rate = balance_value_dict.get('valuation_rate')
        else:
            new_stock_balance.stock_value = 0
            new_stock_balance.valuation_rate = 0            
            
        new_stock_balance.insert()
        
    items = frappe.db.sql("""SELECT distinct item from `tabStock Ledger` """,as_dict = True)
    
    for item in items:
        update_stock_balance_in_item(item.item)
        
   
# Update item stock balance based on all warehouse balances
def update_stock_balance_in_item(item):
    
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

def re_post_stock_ledgers():
    
    post_only_for_a_date=False
    doc = frappe.get_doc("Stock Repost")
    
    if(not doc):
        return
    
    posting_date = doc.last_processed_posting_date
        
    if not posting_date:
        return
    
    if(doc.posting_status == "In Process"):
        return
    
    doc.posting_status = "In Process"
    doc.save()
    
    # If there is already a reposting happened, get the last_processed_stock_ledger and fetch its posting_date to process subsequent stock ledgers  
    last_processed_ledger = doc.last_processed_stock_ledger
    
    # If there is a last procssed stock ledger. posting_date fetch from that
    if last_processed_ledger:
        last_processed_ledger_doc = frappe.get_doc('Stock Ledger', last_processed_ledger)
        posting_date = last_processed_ledger_doc.posting_date
                    
    # post_only_for_a_date should be true when calling from the scheduler which updates only for the current date
    
    udpate_ledgers = True
    
    while udpate_ledgers==True:
        
        # [17-02-2023 - Rupesh]
        # Checking the count for the stock ledgers to fetch records with the same posting date and time since in the next query it cannot give >= with the posting_date and checking a value(eg: recalculated) which already updated in the stock ledger table to avoid the records already processed, because of the database locking. So using the approach to fetch all records with the same date and time and procecss it
        
        # Get stock ledgers with the last assigned posting_date (there can be multiple records)
        count = frappe.db.count('Stock Ledger', filters={'posting_date': posting_date})
        
        if(count>0):
            stock_ledgers_with_same_date_and_time = frappe.get_all('Stock Ledger', 
                                filters={'posting_date': posting_date},
                                fields=['name', 'posting_date'])          

            # Loop through each 'Stock Ledger' record
            for ledger in stock_ledgers_with_same_date_and_time:                
                update_stock_ledger(ledger['name'], for_reposting=True)                
                doc.last_processed_stock_ledger = ledger['name']
                doc.last_processed_posting_date = posting_date
        
        next_stock_ledger = frappe.db.sql("""
            SELECT sl.name, sl.posting_date FROM `tabStock Ledger` sl
            WHERE posting_date > %s ORDER BY posting_date ASC
            LIMIT 1
        """, (posting_date,), as_dict=True)
        
        if(next_stock_ledger and next_stock_ledger[0]): 
        
            if post_only_for_a_date == True and (  
                    next_stock_ledger[0].posting_date.date() != posting_date.date()):                
                    udpate_ledgers = False    
                    break  
                    
            update_stock_ledger(next_stock_ledger[0].name, for_reposting=True)
            udpate_ledgers = True
            posting_date = next_stock_ledger[0].posting_date
            doc.last_processed_stock_ledger = next_stock_ledger[0].name
            doc.last_processed_posting_date = posting_date
            
        else:
            udpate_ledgers = False
            
    update_all_item_stock_balances()
       
    doc.posting_status = "Not Started"
    doc.save()
    frappe.db.commit()
    
    frappe.msgprint("Stock update completed")
    
                
def update_stock_ledger_values(stock_ledger_name, balance_qty, valuation_rate, balance_value, for_reposting):
        
        
        valuation_rate = valuation_rate if valuation_rate else 0
        balance_qty = balance_qty if balance_qty else 0
        balance_value = balance_value if balance_value else 0
        
        sl = frappe.get_doc('Stock Ledger', stock_ledger_name)
        qty_in = 0
        qty_out = 0
        
        if(sl.voucher == "Stock Reconciliation") :
            
            if(sl.balance_qty > balance_qty):
                qty_in = sl.balance_qty - balance_qty
            else:
                qty_out = balance_qty -sl.balance_qty
        
            sl.qty_in = qty_in
            sl.qty_out = qty_out
            
            # Previous stock value difference
            previous_balance_value = balance_value #Assign before change        
            sl.change_in_stock_value =   (sl.balance_value - previous_balance_value) 
                                
            valuation_rate = sl.valuation_rate                    
            balance_qty = sl.balance_qty
            balance_value = sl.balance_value
       
        # Sales invoice included to favor Tab Sales
        if(sl.voucher == "Delivery Note" or sl.voucher== "Sales Invoice"):
            previous_balance_qty = balance_qty
            previous_balance_value = balance_value #Assign before change                    
            balance_qty = balance_qty - sl.qty_out
            balance_value = balance_qty * (valuation_rate  if valuation_rate else 0)
            change_in_stock_value = balance_value - previous_balance_value
            sl.change_in_stock_value = change_in_stock_value
            sl.log = f"previous stock balance {previous_balance_qty}"
        
        # Valuation rate adjusts based on purchase return
        if (sl.voucher == "Purchase Return"):            
            previous_balance_qty = balance_qty
            previous_balance_value = balance_value #Assign before change                    
            balance_qty = balance_qty - sl.qty_out
            balance_value = balance_value - (balance_qty * sl.outgoing_rate)                    
            change_in_stock_value = balance_value - previous_balance_value
            sl.change_in_stock_value = change_in_stock_value
            
            if(balance_qty!=0): #Avoid divisible by zero               
                    valuation_rate = balance_value/ balance_qty
                    
            sl.log = f"previous stock balance {previous_balance_qty}"            
                                
        if (sl.voucher == "Purchase Invoice" or sl.voucher == "Sales Return"):
            previous_balance_value = balance_value #Assign before change 
            balance_qty = balance_qty + sl.qty_in
            balance_value = balance_value  + (sl.qty_in * sl.incoming_rate)
            change_in_stock_value = balance_value - previous_balance_value
            sl.change_in_stock_value = change_in_stock_value

            if(balance_qty!=0): #Avoid divisible by zero
                if sl.voucher == "Purchases Invoice":  #Avoid sales return to assign new_valuation_rate
                    valuation_rate = balance_value/ balance_qty
                
        if(sl.voucher == "Stock Transfer"):
            
            previous_balance_value = balance_value #Assign before change 
            
            if(sl.qty_in > 0):
                                
                balance_qty = balance_qty + sl.qty_in
                
                # balance_value = balance_value  + (sl.qty_in * sl.incoming_rate)
                balance_value = balance_qty * (valuation_rate if valuation_rate else 0)
                change_in_stock_value = balance_value - previous_balance_value
                sl.change_in_stock_value = change_in_stock_value
                
            elif (sl.qty_out>0):    
               
                print("stck trnsfr - qty_out")
                balance_qty = balance_qty if balance_qty else 0                
                qty_out = sl.qty_out if sl.qty_out else 0
                valuation_rate = valuation_rate if valuation_rate else 0
                previous_balance_value = previous_balance_value  if previous_balance_value else 0                                    
                balance_qty = balance_qty - qty_out
                balance_value = balance_qty * valuation_rate                    
                change_in_stock_value = balance_value - previous_balance_value
                sl.change_in_stock_value = change_in_stock_value  
                
        if for_reposting:
            if sl.balance_qty != balance_qty:
                sl.corrected_on_repost = True                
                sl.balance_qty_before_repost = sl.balance_qty
        
        if(sl.balance_qty != balance_qty):
            sl.balance_qty = balance_qty
        
        if(sl.valuation_rate != valuation_rate):
            sl.valuation_rate = valuation_rate
        
        if (sl.balance_value != balance_value):
            sl.balance_value = balance_value    
                    
        sl.recalculated = True    
        sl.save()
        frappe.db.commit()
                             
        return balance_qty,valuation_rate,balance_value
        

def update_stock_ledger(stock_ledger_name, for_reposting):
    
       
    stock_ledger = frappe.get_doc('Stock Ledger', stock_ledger_name) 
    
    # Get Previous Stock Ledger    
    previous_stock_ledger = frappe.db.sql("""
                    SELECT name,item,qty_in,qty_out,balance_qty,balance_value,warehouse,posting_date FROM `tabStock Ledger` 
                    WHERE posting_date < %s and item=%s and warehouse = %s
                    ORDER BY posting_date desc limit 1
                """, (stock_ledger.posting_date, stock_ledger.item, stock_ledger.warehouse), as_dict=True) 
    
    balance_qty = 0
    valuation_rate = 0
    balance_value = 0
    
    if(previous_stock_ledger and previous_stock_ledger[0]):        
        balance_qty = previous_stock_ledger[0].balance_qty
        valuation_rate = previous_stock_ledger[0].valuation_rate
        balance_value = previous_stock_ledger[0].balance_value   
   
    update_stock_ledger_values(stock_ledger_name, balance_qty,valuation_rate,balance_value,for_reposting)
        
        