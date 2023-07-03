# Copyright (c) 2023, Rupesh P and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):

	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_data(filters):
    data = ""
    # Item, from_date, to_date, warehouse
    if filters.get('item') and filters.get('from_date') and filters.get('to_date') and filters.get('warehouse'):
        data = frappe.db.sql("""
            SELECT sl.item, sl.voucher, sl.voucher_no, sl.posting_date, sl.warehouse,
                   sl.qty_in, sl.unit, sl.qty_out, sl.valuation_rate, sl.balance_qty
            FROM `tabStock Ledger` sl
            WHERE sl.item = '{0}'
              AND sl.warehouse = '{1}'
              AND sl.posting_date BETWEEN '{2}' AND '{3}'
            ORDER BY sl.item, sl.posting_date
        """.format(filters.get('item'), filters.get('warehouse'), filters.get('from_date'), filters.get('to_date')), as_dict=True)
    # Item, from_date, to_date
    elif filters.get('item') and filters.get('from_date') and filters.get('to_date') and not filters.get('warehouse'):
        data = frappe.db.sql("""
            SELECT sl.item, sl.voucher, sl.voucher_no, sl.posting_date, sl.warehouse,
                   sl.qty_in, sl.unit, sl.qty_out, sl.valuation_rate, sl.balance_qty
            FROM `tabStock Ledger` sl
            WHERE sl.item = '{0}'
              AND sl.posting_date BETWEEN '{1}' AND '{2}'
            ORDER BY sl.item, sl.posting_date
        """.format(filters.get('item'), filters.get('from_date'), filters.get('to_date')), as_dict=True)
    # Item, warehouse
    elif filters.get('item') and filters.get('warehouse') and not (filters.get('from_date') and filters.get('to_date')):
        data = frappe.db.sql("""
            SELECT sl.item, sl.voucher, sl.voucher_no, sl.posting_date, sl.warehouse,
                   sl.qty_in, sl.unit, sl.qty_out, sl.valuation_rate, sl.balance_qty
            FROM `tabStock Ledger` sl
            WHERE sl.item = '{0}'
              AND sl.warehouse = '{1}'
            ORDER BY sl.item, sl.posting_date
        """.format(filters.get('item'), filters.get('warehouse')), as_dict=True)
    # from_date, to_date
    elif filters.get('from_date') and filters.get('to_date') and not (filters.get('item') and filters.get('warehouse')):
        data = frappe.db.sql("""
            SELECT sl.item, sl.voucher, sl.voucher_no, sl.posting_date, sl.warehouse,
                   sl.qty_in, sl.unit, sl.qty_out, sl.valuation_rate, sl.balance_qty
            FROM `tabStock Ledger` sl
            WHERE sl.posting_date BETWEEN '{0}' AND '{1}'
            ORDER BY sl.item, sl.posting_date
        """.format(filters.get('from_date'), filters.get('to_date')), as_dict=True)
    # from_date
    elif filters.get('from_date') and not (filters.get('item') and not (filters.get('warehouse') and not filters('to_date'))):
        data = frappe.db.sql("""
            SELECT sl.item, sl.voucher, sl.voucher_no, sl.posting_date, sl.warehouse,
                   sl.qty_in, sl.unit, sl.qty_out, sl.valuation_rate, sl.balance_qty
            FROM `tabStock Ledger` sl
            WHERE sl.posting_date >= '{0}'
            ORDER BY sl.item, sl.posting_date
        """.format(filters.get('from_date')), as_dict=True)
    # Item
    elif filters.get('item') and not (filters.get('warehouse') or filters.get('from_date') or filters.get('to_date')):
        data = frappe.db.sql("""
            SELECT sl.item, sl.voucher, sl.voucher_no, sl.posting_date, sl.warehouse,
                   sl.qty_in, sl.unit, sl.qty_out, sl.valuation_rate, sl.balance_qty
            FROM `tabStock Ledger` sl
            WHERE sl.item = '{0}'
            ORDER BY sl.item, sl.posting_date
        """.format(filters.get('item')), as_dict=True)
    # Warehouse
    elif filters.get('warehouse') and not (filters.get('item') or filters.get('from_date') or filters.get('to_date')):
        data = frappe.db.sql("""
            SELECT sl.item, sl.voucher, sl.voucher_no, sl.posting_date, sl.warehouse,
                   sl.qty_in, sl.unit, sl.qty_out, sl.valuation_rate, sl.balance_qty
            FROM `tabStock Ledger` sl
            WHERE sl.warehouse = '{0}'
            ORDER BY sl.item, sl.posting_date
        """.format(filters.get('warehouse')), as_dict=True)
    else:
        data = frappe.db.sql("""
            SELECT sl.item, sl.voucher, sl.voucher_no, sl.posting_date, sl.warehouse,
                   sl.qty_in, sl.unit, sl.qty_out, sl.valuation_rate, sl.balance_qty
            FROM `tabStock Ledger` sl
            ORDER BY sl.item, sl.posting_date
        """, as_dict=True)

    last_item = ""
    last_warehouse = ""
    last_qty = 0
    for dl in data:
        if not (dl.item == last_item and dl.warehouse == last_warehouse):
            opening_qty = frappe.get_value('Stock Ledger', {'item': dl.item, 'warehouse': dl.warehouse, 'posting_date': ['<', dl.posting_date]}, 'balance_qty', order_by='posting_date')

            if opening_qty:
                dl.update({"opening_qty": round(opening_qty, 2)})
            else:
                dl.update({"opening_qty": 0})
        else:
            dl.update({"opening_qty": round(last_qty, 2)})

        last_item = dl.item
        last_qty = dl.balance_qty
        last_warehouse = dl.warehouse

    return data

def get_columns():
	return [
		{
			"fieldname": "item",
			"fieldtype": "Link",
			"label": "Item",
			"options": "Item",
			"width": 200,
		},
		{
			"fieldname": "opening_qty",
			"fieldtype": "Data",
			"label": "Opening Qty",
			"width": 125,
		},
  		{
			"fieldname": "voucher",
			"fieldtype": "Data",
			"label": "Voucher Type",
			"width": 110,
		},
    	{
			"fieldname": "voucher_no",
			"fieldtype": "Data",
			"label": "Voucher No",
			"width": 100,
		},
     	{
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"label": "Date",
			"width": 100,
		},
      	{
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"label": "W/H",
			"options": "Warehouse",
			"width": 140,
		},
        {
			"fieldname": "qty_in",
			"fieldtype": "Data",
			"label": "Qty In",
			"width": 70,
		},
        {
			"fieldname": "unit",
			"fieldtype": "Link",
			"label": "Unit",
			"options": "Unit",
			"width": 60,
		},
        {
			"fieldname": "qty_out",
			"fieldtype": "Data",
			"label": "Qty Out",
			"width": 80,
		},
        {
			"fieldname": "valuation_rate",
			"fieldtype": "Data",
			"label": "Valuation Rate",
			"width": 120,
		},
        {
			"fieldname": "balance_qty",
			"fieldtype": "Data",
			"label": "Balance Qty",
			"width": 100,
		},

	]
