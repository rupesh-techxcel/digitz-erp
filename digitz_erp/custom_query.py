import frappe


@frappe.whitelist()
def get_item_wise_unit(doctype, txt, searchfield, start, page_len, filters):
    where = ""
    where += "WHERE (parent = '{item}') ".format(item=filters.get("item"))
    if len(txt) > 0:
        where += 'and name LIKE "%{txt}%")'.format(
            txt=txt)

    return frappe.db.sql(
        """
        SELECT name, unit 
        FROM `tabItem Unit`
        {where}
    """.format(
            where=where
        ),
        debug=True
    )
