import frappe
from frappe.utils import get_datetime
from digitz_erp.api.settings_api import get_default_currency

@frappe.whitelist()
def update_item_price(item, price_list, currency, rate, date):
    
    item_doc = frappe.get_doc('Item', item)
    
     # Check if there's a matching Item Price record for the given item, price_list, currency, and date
    item_price = frappe.get_all("Item Price", filters={
        "item_code": item,
        "price_list": price_list,
        "currency": currency,
        "from_date": ('<=', date),
        "to_date": ('>=', date)
    }, fields=["name"], limit=1)
    
    # Check price list exists without a date
    if not item_price:
        item_price = frappe.get_all("Item Price", filters={
            "item_code": item,
            "price_list": price_list,
            "currency": currency
        }, fields=["name"], limit=1)
        
    if item_price:
        
        item_price_doc = frappe.get_doc("Item Price", item_price)
        item_price_doc.rate = rate
        item_price_doc.save()            
    else:    
        doc = frappe.new_doc("Item Price")
        doc.item = item	
        doc.item_name = item_doc.item_name
        doc.unit = item_doc.base_unit			
        doc.price_list = price_list
        doc.currency = currency
        doc.rate = rate  
        print("doc")          
        print(doc)          
        doc.insert()	
    
                
@frappe.whitelist()
def get_item_price(item, price_list, currency, date):
    
    # Check if there's a matching Item Price record for the given item, price_list, currency, and date
    item_price = frappe.get_all("Item Price", filters={
        "item_code": item,
        "price_list": price_list,
        "currency": currency,
        "from_date": ('<=', date),
        "to_date": ('>=', date)
    }, fields=["rate"], limit=1)

    if item_price:
        # Return the rate from the matching record
        return item_price[0].rate
    else:
        # Add your additional condition within the else block
        item_price = frappe.get_all("Item Price", filters={
            "item_code": item,
            "price_list": price_list,
            "currency": currency
        }, fields=["rate"], limit=1)
        
        if item_price:
            return item_price[0].rate
        else:
            return 0

@frappe.whitelist()
def get_customer_last_price_for_item(item,customer):

    rate = frappe.db.sql("""select tsi.rate from `tabSales Invoice Item` tsi inner join `tabSales Invoice` ts on ts.name = tsi.parent where tsi.item='{item}' and ts.customer='{customer}' and ts.docstatus <2 order by ts.posting_date desc LIMIT 1""".format(item=item, customer=customer))
    
    if(rate):
        return rate
    else:
        return 0

@frappe.whitelist()
def get_supplier_last_price_for_item(item,supplier):

    rate = frappe.db.sql("""select tpi.rate from `tabPurchase Invoice Item` tpi inner join `tabPurchase Invoice` tp on tp.name = tpi.parent where tpi.item='{item}' and tp.supplier='{supplier}' and tp.docstatus <2 order by tp.posting_date desc LIMIT 1""".format(item=item, supplier=supplier))
    
    if(rate):
        return rate
    else:
        return 0


    
	