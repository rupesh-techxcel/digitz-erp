import frappe

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

@frappe.whitelist()
def get_item_price_for_price_list(item, price_list):
	 return frappe.get_all(
		"Price List Item",
		filters={"item": item,
		 "parent": price_list},
		fields=["price"]	
)

