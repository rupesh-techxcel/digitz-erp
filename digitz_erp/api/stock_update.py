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
        print("record.base_stock_ledger")
        print(record.base_stock_ledger)
                
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
            print("new_valuation_rate") 
            print(new_valuation_rate)        
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

# def update_purchase_usage_for_delivery_note(delivery_note_no):
    
#     delivery_note_doc = frappe.get_doc('Delivery Note', delivery_note_no)    
#     do_posting_date = delivery_note_doc.posting_date
#     delivery_note_items = frappe.get_list('Delivery Note Item',{'parent': delivery_note_no },['name','item_code','qty','rate'])
    
#     frappe.db.delete("Purchase Stock Usage", {"delivery_note":delivery_note_no})
#     frappe.db.commit()
    
#     for item in delivery_note_items:
        
#         # query = """SELECT p.name as p_name, pi.name as pi_name,pi.item_code,pi_item,pi.qty- sum(su.sold_qty) as qty  from `tabPurchase Invoice Item` as pi left   outer join `tabPurchase Stock Usage` su on su.purchase_invoice_item = pi.name and su.item_code= pi.item_code inner join `tabPurchase Invoice` p on p.name= pi.parent  WHERE pi.posting_date<={do_date} and  pi.item_code={item} pi.qty > sum(su.sold_qty) group by pi.name,pi.item_code,pi.item,pi.qty. p.name order by pi.posting_date""".format(item=item.item_code, do_date=do_posting_date)
        
#         # result = frappe.db.sql(query, as_dict = True)        
        
#         query = """
#         SELECT
#             p.name AS p_name,
#             pi.name AS pi_name,
#             pi.item_code,
#             pi.item,
#             pi.qty - COALESCE(SUM(su.sold_qty), 0) AS qty
#         FROM
#             `tabPurchase Invoice Item` AS pi
#         LEFT JOIN
#             `tabPurchase Stock Usage` AS su
#         ON
#             su.purchase_invoice_item = pi.name AND su.item_code = pi.item_code
#         INNER JOIN
#             `tabPurchase Invoice` AS p
#         ON
#             p.name = pi.parent
#         WHERE
#             p.posting_date <= '{do_date}'
#             AND pi.item_code = '{item_code}'
#             AND pi.qty > COALESCE((SELECT SUM(sold_qty) FROM `tabPurchase Stock Usage` WHERE purchase_invoice_item = pi.name AND item_code = pi.item_code), 0)
#         GROUP BY
#             pi.name, pi.item_code, pi.item, pi.qty, p.name
#         ORDER BY
#             p.posting_date
#         """.format(item_code=item.item, do_date=do_posting_date)
        

#         result = frappe.db.sql(query, as_dict=True)
#         qtyRequired = item.qty
        
#         for result_item in result:
#             if(result_item.qty > 0):
#                 # When purchase qty is less than qty required then need to iterate again.
#                 if(result_item.qty < qtyRequired):
#                     # Insert a record in the tabPurchase Stock Usage table                    
#                     su_doc = frappe.new_doc("Purchase Stock Usage")
#                     su_doc.purchase_invoice = result_item.p_name
#                     su_doc.purchase_invoice_item = result_item.pi_name
#                     su_doc.item = result_item.item_code
#                     su_doc.item_name = result_item.item
#                     su_doc.delivery_note = delivery_note_no
#                     su_doc.delivery_note_item = item.name
#                     su_doc.sold_qty = result_item.qty
#                     su_doc.insert()
#                     qtyRequired = qtyRequired - result_item.qty
#                 else:
#                     su_doc = frappe.new_doc("Purchase Stock Usage")
#                     su_doc.purchase_invoice = result_item.p_name
#                     su_doc.purchase_invoice_item = result_item.pi_name                    
#                     su_doc.item_name = result_item.item
#                     su_doc.item = result_item.item_code
#                     su_doc.delivery_note = delivery_note_no
#                     su_doc.delivery_note_item = item.name
#                     su_doc.sold_qty = qtyRequired
#                     su_doc.insert()
#                     continue

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
    
    clean_stock_ledgers_duplicated()
    
    # If there is already a reposting happened, get the last_processed_stock_ledger and fetch its posting_date to process subsequent stock ledgers  
    last_processed_ledger = doc.last_processed_stock_ledger
    
    # If there is a last procssed stock ledger. posting_date fetch from that
    if last_processed_ledger:
        last_processed_ledger_doc = frappe.get_doc('Stock Ledger', last_processed_ledger)
        posting_date = last_processed_ledger_doc.posting_date
                    
    # post_only_for_a_date should be true when calling from the scheduler which updates only for the current date
    
    udpate_ledgers = True
    
    stock_ledgers_for_delivery_note = []
    stock_ledgers_for_sales_invoice = []
    stock_ledgers_for_sales_return = []
    
    while udpate_ledgers==True:
               
        # Get stock ledgers with the last assigned posting_date (there can be multiple records)
        count = frappe.db.count('Stock Ledger', filters={'posting_date': posting_date})
        
        if(count>0):
            stock_ledgers_with_same_date_and_time = frappe.get_all('Stock Ledger', 
                                filters={'posting_date': posting_date},
                                fields=['name', 'posting_date','voucher','voucher_no'])          

            # Loop through each 'Stock Ledger' record
            for ledger in stock_ledgers_with_same_date_and_time: 
                
                update_stock_ledger(ledger['name'], for_reposting=True)                
                doc.last_processed_stock_ledger = ledger['name']
                doc.last_processed_posting_date = posting_date
                
                if ledger['voucher'] == "Sales Invoice" and ledger['voucher_no'] not in stock_ledgers_for_sales_invoice:
                    stock_ledgers_for_sales_invoice.append(ledger['voucher_no'])
                    
                if ledger['voucher'] == "Delivery Note" and ledger['voucher_no'] not in stock_ledgers_for_delivery_note:
                    stock_ledgers_for_delivery_note.append(ledger['voucher_no'])
                
                if ledger['voucher'] == "Sales Return" and ledger['voucher_no'] not in stock_ledgers_for_sales_return:
                    stock_ledgers_for_sales_return.append(ledger['voucher_no'])
                
        
        next_stock_ledger = frappe.db.sql("""
            SELECT sl.name, sl.posting_date,voucher,voucher_no FROM `tabStock Ledger` sl
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
            
            if next_stock_ledger[0].voucher == "Sales Invoice" and next_stock_ledger[0].voucher_no not in stock_ledgers_for_sales_invoice:
                    stock_ledgers_for_sales_invoice.append(next_stock_ledger[0].voucher_no)
                    
            if next_stock_ledger[0].voucher == "Delivery Note" and next_stock_ledger[0].voucher_no not in stock_ledgers_for_delivery_note:
                    stock_ledgers_for_delivery_note.append(next_stock_ledger[0].voucher_no)
                    
            if next_stock_ledger[0].voucher == "Sales Return" and next_stock_ledger[0].voucher_no not in stock_ledgers_for_sales_return:
                    stock_ledgers_for_sales_return.append(next_stock_ledger[0].voucher_no)
            
        else:
            udpate_ledgers = False
            
    update_all_item_stock_balances()
    
    update_all_cost_of_goods_solds(stock_ledgers_for_delivery_note,stock_ledgers_for_sales_invoice, stock_ledgers_for_sales_return)
       
    doc.posting_status = "Not Started"
    doc.save()
    frappe.db.commit()
    
    frappe.msgprint("Stock update completed")

def update_all_cost_of_goods_solds(delivery_note_list, sales_invoice_list,sales_return_list):
    
    if delivery_note_list:
        for delivery_note in delivery_note_list:
            update_cost_of_goods_sold("Delivery Note", delivery_note)        
    
    if sales_invoice_list:
        for sales_invocie in sales_invoice_list:
            update_cost_of_goods_sold("Sales Invoice", sales_invocie)
        
    if sales_return_list:
        for sales_return in sales_return_list:
            update_cost_of_goods_sold("Sales Return", sales_return)
            
def clean_stock_ledgers_duplicated():
    
    udpate_ledgers = True
    
    doc = frappe.get_doc("Stock Repost")
    
    if(not doc):
        return
    
    posting_date = doc.last_processed_posting_date
       
    deleted_stock_ledgers =[]
        
    while udpate_ledgers==True:
                   
    # Get stock ledgers with the last assigned posting_date (there can be multiple records)
        count = frappe.db.count('Stock Ledger', filters={'posting_date': posting_date})
        
        if(count>0):
            stock_ledgers_with_same_date_and_time = frappe.get_all('Stock Ledger', 
                                filters={'posting_date': posting_date},
                                fields=['name', 'posting_date','voucher','voucher_no'])   
            
            # Loop through each 'Stock Ledger' record
            for ledger in stock_ledgers_with_same_date_and_time: 
                                
                if not deleted_stock_ledgers or ledger.name not in deleted_stock_ledgers:
                    deleted_stock_ledgers = clean_stock_ledger(ledger.name, deleted_stock_ledgers)
                
                # Process fo the same date and time
        
        next_stock_ledger = frappe.db.sql("""
        SELECT sl.name, sl.posting_date,voucher,voucher_no FROM `tabStock Ledger` sl
        WHERE posting_date > %s ORDER BY posting_date ASC 
        LIMIT 1
    """, (posting_date,), as_dict=True)
        
        if(next_stock_ledger and next_stock_ledger[0]): 
            
            posting_date = next_stock_ledger[0].posting_date
                      
            if not deleted_stock_ledgers or next_stock_ledger[0].name not in deleted_stock_ledgers:
                deleted_stock_ledgers = clean_stock_ledger(next_stock_ledger[0].name, deleted_stock_ledgers)
            
        else:
            udpate_ledgers = False
    
    print("final deleted stock ledgers") 
    print(deleted_stock_ledgers)    
        # [End]
                    
def clean_stock_ledger(ledger_name, deleted_stock_ledgers):
    
    if ledger_name in deleted_stock_ledgers:        
        return deleted_stock_ledgers
    
    sl =frappe.get_doc("Stock Ledger", ledger_name)    
    
    if(sl.qty_in>0):
        sl.log = sl.qty_in
    if(sl.qty_out >0):
        sl.log = sl.qty_out
                
    sl.save()
    
    other_stock_ledgers_for_item_in_the_voucher_query = ""
    # While In Stock Transfer, there are records with qty_in and qty_out for both the source and target warehoues, need to consider only the corresponding one for the stock ledger
    if sl.qty_in>0:
        other_stock_ledgers_for_item_in_the_voucher_query = """select name,item,qty_in,qty_out,valuation_rate from `tabStock Ledger` where name !=%s and voucher=%s and voucher_no=%s and item=%s  and qty_in>0"""
    else:
        other_stock_ledgers_for_item_in_the_voucher_query = """select name,item,qty_in,qty_out,valuation_rate from `tabStock Ledger` where name !=%s and voucher=%s and voucher_no=%s and item=%s and qty_out>0 """
        
    other_stock_ledgers_for_item_in_the_voucher_data = frappe.db.sql(other_stock_ledgers_for_item_in_the_voucher_query,(sl.name,sl.voucher,sl.voucher_no,sl.item), as_dict=True)
    qty_in_for_item_in_voucher = sl.qty_in
    qty_out_for_item_in_voucher = sl.qty_out    
    
    for data in other_stock_ledgers_for_item_in_the_voucher_data:        
        qty_in_for_item_in_voucher += data.qty_in
        qty_out_for_item_in_voucher += data.qty_out    
    
    
    if(qty_in_for_item_in_voucher != sl.qty_in or qty_out_for_item_in_voucher != sl.qty_out):
        sl.qty_in = qty_in_for_item_in_voucher
        sl.qty_out = qty_out_for_item_in_voucher
        sl.save()
        
        
    for data in other_stock_ledgers_for_item_in_the_voucher_data:
        
        if frappe.db.exists('Stock Ledger', data['name']):           
            frappe.delete_doc('Stock Ledger', data['name'], ignore_permissions=True)
            frappe.db.commit()
            deleted_stock_ledgers.append(data['name'])


        # Optionally, you can commit after each deletion to ensure data consistency.
        # frappe.db.commit()
    
                
    return deleted_stock_ledgers   
    

def get_valuation_rate_for_item_when_missing(item):

    # Get first purchase rate of the item. This method calls only when valuation_rate is missing. Logically it should happen only for the first sales without maing purchase invoice. So taking the oldest rate
    query = """Select rate_in_base_unit from `tabPurchase Invoice Item` pi inner join `tabPurchase Invoice` p on p.name = pi.parent where item=%s order by posting_date Limit 1"""
    data = frappe.db.sql(query,(item), as_dict = True)
    if data:
        return data[0].rate_in_base_unit
    else:
        return 0    
                
def update_stock_ledger_values(stock_ledger_name, balance_qty, valuation_rate, balance_value, for_reposting):
        
        valuation_rate = valuation_rate if valuation_rate else 0
        balance_qty = balance_qty if balance_qty else 0
        balance_value = balance_value if balance_value else 0
        
        sl = frappe.get_doc('Stock Ledger', stock_ledger_name)
        qty_in = 0
        qty_out = 0
        
        if valuation_rate == 0:
            valuation_rate = get_valuation_rate_for_item_when_missing(sl.item)
            
        # System does not allow same item to be repeated in multiple rows in Stock Reconciliation so need not consider the case. (sl.balance_qty is not a calculated column in Stock Reconciliation, but its directly usihg to find out qty_in and qty_out). For other cases balance_qty is a calculated column from qty_in or qty_out. 
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
                     
                                
        if (sl.voucher == "Purchase Invoice" or sl.voucher == "Sales Return"):
            
            print(f"valuation rate before change {valuation_rate}")
            print(f"incoming_rate in the stock_ledger", sl.incoming_rate)
            previous_balance_value = balance_value #Assign before change 
            balance_qty = balance_qty + sl.qty_in
            balance_value = balance_value  + (sl.qty_in * sl.incoming_rate)
            change_in_stock_value = balance_value - previous_balance_value
            sl.change_in_stock_value = change_in_stock_value

            if(balance_qty!=0): #Avoid divisible by zero
                if sl.voucher == "Purchase Invoice":  #Avoid sales return to assign new_valuation_rate
                    valuation_rate = balance_value/ balance_qty
                    print("valuation_rate reassigned")
            
            print(f"new valuation rate {valuation_rate}")
                
        if(sl.voucher == "Stock Transfer"):
            
            previous_balance_value = balance_value #Assign before change 
            
            if(sl.qty_in > 0):
                                
                balance_qty = balance_qty + sl.qty_in
                
                # balance_value = balance_value  + (sl.qty_in * sl.incoming_rate)
                balance_value = balance_qty * (valuation_rate if valuation_rate else 0)
                change_in_stock_value = balance_value - previous_balance_value
                sl.change_in_stock_value = change_in_stock_value
                
            elif (sl.qty_out>0):    
               
                
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
    
def update_cost_of_goods_sold(voucher,voucher_no):
    
    script = ""
    
    if voucher == "Delivery Note" or voucher == "Sales Invoice":
        script ="""Select sum(qty_out* valuation_rate) as cost_of_goods_sold from `tabStock Ledger` where voucher=%s and voucher_no=%s"""
    else: # for sales return
        script ="""Select sum(qty_in* valuation_rate) as cost_of_goods_sold from `tabStock Ledger` where voucher=%s and voucher_no=%s"""
        
    cog_data = frappe.db.sql(script,(voucher,voucher_no), as_dict = True)
    
    cost_of_goods_sold = 0
    
    print(cog_data)
    
    if(cog_data):
        cost_of_goods_sold = cog_data[0].cost_of_goods_sold
        
    print(f"cost of goods sold for voucher {voucher_no} = {cost_of_goods_sold}" )
        
    
    default_company = frappe.db.get_single_value("Global Settings", "default_company")

    default_accounts = frappe.get_value("Company", default_company, ['default_receivable_account', 'default_inventory_account',
                                                                    'default_income_account', 'cost_of_goods_sold_account', 'round_off_account', 'tax_account'], as_dict=1)
    
    document  = frappe.get_doc(voucher, voucher_no)
    
    posting_date = document.posting_date
    posting_time = document.posting_time
        
    gl_posts_for_cogs =frappe.db.sql("select name from `tabGL Posting` where voucher_type=%s and voucher_no=%s and (account=%s or account=%s)",(voucher,voucher_no,default_accounts.cost_of_goods_sold_account,default_accounts.default_inventory_account),as_dict = True)
    
    for gl_post in gl_posts_for_cogs:
        frappe.delete_doc('GL Posting', gl_post.name, ignore_permissions=True)
    
    gl_count = frappe.db.count(
                'GL Posting', {'voucher_type': voucher, 'voucher_no': voucher_no})
    idx = gl_count + 1
    
    # Insert recrods again with the updated cogs
    
    # Cost Of Goods Sold
    gl_doc = frappe.new_doc('GL Posting')
    gl_doc.voucher_type = voucher
    gl_doc.voucher_no = voucher_no
    gl_doc.idx = idx
    gl_doc.posting_date = posting_date
    gl_doc.posting_time = posting_time
    gl_doc.account = default_accounts.cost_of_goods_sold_account
    
    if(voucher == "Delivery Note" or voucher == "Sales Invoice"):
        gl_doc.debit_amount = cost_of_goods_sold
    else:
        # For Sales Return
        gl_doc.credit_amount = cost_of_goods_sold
        
    gl_doc.against_account = default_accounts.default_inventory_account
    gl_doc.insert()
    idx +=1

    # Inventory account Eg: Stock In Hand
    gl_doc = frappe.new_doc('GL Posting')
    gl_doc.voucher_type = voucher
    gl_doc.voucher_no = voucher_no
    gl_doc.idx = idx
    gl_doc.posting_date = posting_date
    gl_doc.posting_time = posting_time
    gl_doc.account = default_accounts.default_inventory_account
    if(voucher == "Delivery Note" or voucher == "Sales Invoice"):
        gl_doc.credit_amount = cost_of_goods_sold
    else:
        # For Sales Return
        gl_doc.debit_amount = cost_of_goods_sold
        
    gl_doc.against_account = default_accounts.cost_of_goods_sold_account
    gl_doc.insert()
    