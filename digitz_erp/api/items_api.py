import frappe
from frappe.utils import get_datetime

# @frappe.whitelist()
# def test_job():
#     #print("hello from test job")


@frappe.whitelist()
def get_item_uom(item,unit):

 return frappe.get_all(
		"Item Unit",
		filters={"parent": item,
				 "unit": unit},
		fields=["unit","conversion_factor"]		
	)

@frappe.whitelist()
def get_item_units_query(self, query, txt, searchfield, start, page_len, filters):
        return """SELECT unit,conversion_factor FROM `tabItem Unit` unit
                  WHERE unit.parent = '{0}'""".format(self.name)

@frappe.whitelist()
def get_item_uoms(item=None):
	if(item):
		return frappe.get_all(
		"Item Unit",
		filters={"parent": item},
		fields=["unit","conversion_factor"]		
	)
	else:
		return ""

@frappe.whitelist()
def get_item_price_for_price_list(item, price_list):
	 return frappe.get_all(
		"Item List Item",
		filters={"item": item,
		 "parent": price_list},
		fields=["price"]	  
)

@frappe.whitelist()
def get_item_valuation_rate(item, posting_date, posting_time):	
	
	posting_date_time = get_datetime(str(posting_date) + " " + str(posting_time))			
	
	previous_ledger_valuation_rate = frappe.db.get_value('Stock Ledger', {'item': ['=', item],'posting_date':['<', posting_date_time]},
                                                      ['valuation_rate'], order_by='posting_date desc', as_dict=True)
 
	if(previous_ledger_valuation_rate):
		return previous_ledger_valuation_rate.valuation_rate
	else:
		return 0

@frappe.whitelist()
def get_stock_for_item(item, warehouse, posting_date, posting_time):
    
		#print("from get_stock_for_item")

		posting_date_time = get_datetime(str(posting_date) + " " + str(posting_time))  
		
		previous_stock_balance = frappe.db.get_value('Stock Ledger', {'item': ['=', item], 'warehouse':['=', warehouse]
			, 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
			order_by='posting_date desc', as_dict=True)  
  
		return previous_stock_balance.balance_qty


@frappe.whitelist()
def get_stock_for_item_project(item, project, posting_date, posting_time):
    
		#print("from get_stock_for_item")

		posting_date_time = get_datetime(str(posting_date) + " " + str(posting_time))  
		
		previous_stock_balance = frappe.db.get_value('Project Stock Ledger', {'item': ['=', item], 'project':['=', project]
			, 'posting_date':['<', posting_date_time]},['name', 'balance_qty', 'balance_value','valuation_rate'],
			order_by='posting_date desc', as_dict=True)  
  
		return previous_stock_balance.balance_qty



