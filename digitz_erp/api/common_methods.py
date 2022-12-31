import frappe

@frappe.whitelist()
def get_item_uoms(item,unit):

 return frappe.get_all(
		"Item Unit",
		filters={"parent": item,
				 "unit": unit},
		fields=["unit","conversion_factor"]		
	)


