import frappe
from frappe.utils import get_datetime
from digitz_erp.api.settings_api import get_default_currency

@frappe.whitelist()
def update_item_price(item, price_list, currency, rate):
    
    item_doc = frappe.get_doc('Item', item)

    if not frappe.db.exists("Item Price",{'item': item, 'price_list':price_list, 'currency':currency}):				
        
            if(rate>0):
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
                # With doc.insert it shows the message from the document, so not adding new message here
    else:
            doc_name = frappe.get_doc("Item Price",{'item': item, 'price_list': price_list, 'currency':currency},['name'])
            print("item price doc name")
            print(doc_name)
            
            frappe.set_value("Item Price", doc_name, "rate",rate)
            
            # item_price_doc = frappe.get_doc("Item Price", doc_name)
            # print("item_price_doc")
            # print(item_price_doc)
            
            # item_price_doc.rate = rate
            # item_price_doc.save()
                
@frappe.whitelist()
def get_item_price(item, price_list, currency):
    
    if not frappe.db.exists("Item Price",{'item': item, 'price_list':price_list, 'currency':currency}):				
        rate = 0
        return rate
    else:
        rate = frappe.db.get_value("Item Price",{'item': item, 'price_list': price_list, 'currency':currency},
                            ['rate'])
        return rate

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


    
	