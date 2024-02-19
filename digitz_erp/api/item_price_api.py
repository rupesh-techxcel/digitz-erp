import frappe
from frappe.utils import get_datetime
from digitz_erp.api.settings_api import get_default_currency
from datetime import datetime

@frappe.whitelist()
def update_item_price(item, price_list, currency, rate, date):
   
    # Check if there's a matching Item Price record for the given item, price_list, currency, and date
    item_price = frappe.get_all("Item Price", filters={
        "item": item,
        "price_list": price_list,
        "currency": currency,
    }, fields=["rate","name","from_date", "to_date"])    
    
    date = str(date)
    
    date = datetime.strptime(date, '%Y-%m-%d').date()  # Convert date to datetime object
   
    item_price_doc_no_dates_name = ""

    if item_price:
        for ip in item_price:           
            
            if ip.from_date and ip.to_date:
                if ip.from_date <= date and ip.to_date >=date:                    
                    item_price_with_dates =frappe.get_doc("Item Price", ip.name)
                    item_price_with_dates.rate = rate
                    item_price_with_dates.save()
                    return
             
            if(ip.from_date == None and ip.to_date == None):
                 item_price_doc_no_dates_name = ip.name   
        
        if(item_price_doc_no_dates_name !="" ):
            item_price_no_dates =frappe.get_doc("Item Price", item_price_doc_no_dates_name)
            item_price_no_dates.rate = rate
            item_price_no_dates.save()
            return
        else: 
            # This case happens only if there is an item price already exists which has
            # different date range and not with even default price with out dates
            # and its not likely to occur
            item_doc = frappe.get_doc("Item", item)
            
            
            doc = frappe.new_doc("Item Price")
            doc.item = item	
            doc.item_name = item_doc.item_name
            doc.unit = item_doc.base_unit			
            doc.price_list = price_list
            doc.currency = currency
            doc.rate = rate
            doc.insert()
    else:
        item_doc = frappe.get_doc("Item", item)
        doc = frappe.new_doc("Item Price")
        doc.item = item	
        doc.item_name = item_doc.item_name
        doc.unit = item_doc.base_unit			
        doc.price_list = price_list
        doc.currency = currency
        doc.rate = rate
        doc.insert()
        
@frappe.whitelist()
def get_item_price(item, price_list, currency, date):
   
    # Check if there's a matching Item Price record for the given item, price_list, currency, and date
    item_price = frappe.get_all("Item Price", filters={
        "item": item,
        "price_list": price_list,
        "currency": currency,
    }, fields=["rate","name","from_date", "to_date"]) 
   
    date = datetime.strptime(date, '%Y-%m-%d').date()  # Convert date to datetime object
   
    item_price_doc_no_dates_name = ""
    
    print("from get_price" )
    print(item_price)

    if item_price:
        for ip in item_price:           
            
            if ip.from_date and ip.to_date:
                if ip.from_date <= date and ip.to_date >= date:                
                    return ip.rate
             
            if(ip.from_date == None and ip.to_date == None):
                 item_price_doc_no_dates_name = ip.name   
        
        if(item_price_doc_no_dates_name !="" ):
            item_price_with_rate =  frappe.get_doc("Item Price", item_price_doc_no_dates_name)
            print("item price")
            print(item_price_with_rate)
            
            if item_price_with_rate:
                return item_price_with_rate.rate    
        
        return 0
        
@frappe.whitelist()
def get_customer_last_price_for_item(item,customer):

    rate = frappe.db.sql("""select tsi.rate_in_base_unit from `tabSales Invoice Item` tsi inner join `tabSales Invoice` ts on ts.name = tsi.parent where tsi.item='{item}' and ts.customer='{customer}' and ts.docstatus <2 order by ts.posting_date desc LIMIT 1""".format(item=item, customer=customer))
    
    if(rate):
        return rate
    else:
        return 0

@frappe.whitelist()
def get_supplier_last_price_for_item(item,supplier):

    rate = frappe.db.sql("""select tpi.rate_in_base_unit from `tabPurchase Invoice Item` tpi inner join `tabPurchase Invoice` tp on tp.name = tpi.parent where tpi.item='{item}' and tp.supplier='{supplier}' and tp.docstatus <2 order by tp.posting_date desc LIMIT 1""".format(item=item, supplier=supplier))
    
    if(rate):
        return rate
    else:
        return 0


    
	