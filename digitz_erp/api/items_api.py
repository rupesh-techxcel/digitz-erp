import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_item_uom(item,unit):

 return frappe.get_all(
		"Item Unit",
		filters={"parent": item,
				 "unit": unit},
		fields=["unit","conversion_factor"]		
	)

@frappe.whitelist()
def get_item_uoms(item):

 return frappe.get_all(
		"Item Unit",
		filters={"parent": item},
		fields=["unit","conversion_factor"]		
	)

@frappe.whitelist()
def get_item_price_for_price_list(item, price_list):
	 return frappe.get_all(
		"Price List Item",
		filters={"item": item,
		 "parent": price_list},
		fields=["price"]	  
)
  
def get_item_valuation_rate_for_price_list(item, posting_date, posting_time):	
	
	posting_date_time = get_datetime(str(posting_date) + " " + str(posting_time))			
	
	previous_ledger_valuation_rate = frappe.db.get_value('Stock Ledger', {'item': ['=', item],'posting_date':['<', posting_date_time]},['valuation_rate'], order_by='posting_date desc', as_dict=True)
 
	if(not  previous_ledger_valuation_rate):
		return 0
	else:
 		return previous_ledger_valuation_rate
   
 
  	
