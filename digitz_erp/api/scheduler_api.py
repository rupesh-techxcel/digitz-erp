import frappe

@frappe.whitelist()
def post_depreciation_for_depreciation_schedulers():
    
    current_date = frappe.utils.nowdate()

    # Query to get asset, asset_category, and date_of_depreciation for the current date
    pending_depreciations = frappe.db.sql(f"""
        SELECT name,asset, asset_category, date_of_depreciation.book_value
        FROM `tabAsset Depreciation Schedule`
        WHERE date_of_depreciation <= '{current_date}' 
        AND posting_status = 'Scheduled'
    """, as_dict=True)

    # Iterating through the fetched assets to get category details
    for depreciation_schedule in pending_depreciations:
        asset =  depreciation_schedule['asset']
        asset_category = depreciation_schedule['asset_category']
        posting_date =  depreciation_schedule['date_of_depreciation']
        book_value =  depreciation_schedule['book_value']

        # Fetching the asset category details
        category_details = frappe.get_doc('Asset Category', asset_category)
        depreciation_account = category_details.depreciation_account
        accumulated_depreciation_account = category_details.accumulated_depreciation_account        
        depreciation_amount = category_details.depreciation
        depreciation_doc_name=insert_depreciation_entry(asset=asset, depreciation_account=depreciation_account,posting_date=posting_date, accumulated_depreciation_account=accumulated_depreciation_account,depreciation=depreciation_amount)        
        frappe.set_value("Asset Depreciation Schedule", depreciation_schedule['name'], "posting_status", "Posted")
        frappe.set_value("Asset Depreciation Schedule", depreciation_schedule['name'], "depreciation_entry",depreciation_doc_name)        
        frappe.set_value("Asset", asset,{"Book Value": book_value})
        

def insert_depreciation_entry(asset,posting_date,depreciation_account,accumulated_depreciation_account,depreciation):
    
    depreciation_doc = frappe.new_doc("Depreciation Entry")
    depreciation_doc.posting_date = posting_date
    depreciation_doc.posting_time = '00:00:01'
    depreciation_doc.asset = asset
    
    depreciation_detail = frappe.new_doc("Depreciation Entry Detail")
    depreciation_detail.account = depreciation_account
    depreciation_detail.debit = depreciation
    depreciation_detail.narration = f"Periodical Depreciation for the asset, {asset}"
    depreciation_detail.against_account = accumulated_depreciation_account
    
    depreciation_doc.append("depreciation_entry_details",depreciation_detail)
    
    depreciation_detail = frappe.new_doc("Depreciation Entry Detail")
    depreciation_detail.account = accumulated_depreciation_account
    depreciation_detail.credit = depreciation
    depreciation_detail.narration = f"Periodical Depreciation for the asset, {asset}"
    depreciation_detail.against_account = depreciation_account
    depreciation_doc.append("depreciation_entry_details",depreciation_detail)
    
    depreciation_doc.insert()
    depreciation_doc.submit()
    return depreciation_doc.name