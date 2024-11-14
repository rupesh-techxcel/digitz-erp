import frappe

@frappe.whitelist()
def after_install():
    insert_accounts()
    create_default_warehouse()
    create_cash_payment_mode()
    create_demo_company()   
    create_budget_reference_types()
    create_default_item_group()
    create_default_supplier_group()
    create_default_customer_group()    
    create_tax()
    create_default_base_unit()
    create_default_price_lists()
    populate_area_data()

def insert_accounts():
    # List of dictionaries representing account data in hierarchical order
    accounts = [
        {"account_name": "Accounts", "is_group": 1, "parent_account": "", "account_type": "", "root_type": "", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Asset", "is_group": 1, "parent_account": "Accounts", "account_type": "", "root_type": "Asset", "balance": 0, "balance_dr_cr": "Cr"},
        {"account_name": "Current Assets", "is_group": 1, "parent_account": "Asset", "account_type": "", "root_type": "Asset", "balance": 0, "balance_dr_cr": "Dr"},
        {"account_name": "Bank Accounts", "is_group": 1, "parent_account": "Current Assets", "account_type": "", "root_type": "Asset", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "RAK BANK", "is_group": 0, "parent_account": "Bank Accounts", "account_type": "Bank", "root_type": "Asset", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Cash Accounts", "is_group": 1, "parent_account": "Current Assets", "account_type": "", "root_type": "Asset", "balance": 0, "balance_dr_cr": "Cr"},
        {"account_name": "Main Cash", "is_group": 0, "parent_account": "Cash Accounts", "account_type": "Cash", "root_type": "Asset", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Stock In Hand", "is_group": 0, "parent_account": "Current Assets", "account_type": "Stock", "root_type": "Asset", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Trade Receivable", "is_group": 0, "parent_account": "Current Assets", "account_type": "", "root_type": "Asset", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Fixed Assets", "is_group": 1, "parent_account": "Asset", "account_type": "", "root_type": "Asset", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Investments", "is_group": 1, "parent_account": "Asset", "account_type": "", "root_type": "Asset", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Expense", "is_group": 1, "parent_account": "Accounts", "account_type": "", "root_type": "Expense", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Direct Expense", "is_group": 1, "parent_account": "Expense", "account_type": "", "root_type": "Expense", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Cost Of Goods Sold Account", "is_group": 0, "parent_account": "Direct Expense", "account_type": "Cost Of Goods Sold", "root_type": "Expense", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Indirect Expense", "is_group": 1, "parent_account": "Expense", "account_type": "", "root_type": "Expense", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Operating Expenses", "is_group": 1, "parent_account": "Indirect Expense", "account_type": "", "root_type": "Expense", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Stock Received But Not Billed", "is_group": 0, "parent_account": "Operating Expenses", "account_type": "Stock Received But Not Billed", "root_type": "Expense", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Stock Adjustment A/c", "is_group": 0, "parent_account": "Operating Expenses", "account_type": "", "root_type": "Expense", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Miscellaneous Expenses", "is_group": 1, "parent_account": "Indirect Expense", "account_type": "", "root_type": "Expense", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Round Off", "is_group": 0, "parent_account": "Miscellaneous Expenses", "account_type": "Round Off", "root_type": "Expense", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Income", "is_group": 1, "parent_account": "Accounts", "account_type": "", "root_type": "Income", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Direct Income", "is_group": 1, "parent_account": "Income", "account_type": "", "root_type": "Income", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Sales Account", "is_group": 0, "parent_account": "Direct Income", "account_type": "", "root_type": "Income", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Indirect Income", "is_group": 1, "parent_account": "Income", "account_type": "", "root_type": "Income", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Liability", "is_group": 1, "parent_account": "Accounts", "account_type": "", "root_type": "Liability", "balance": 0, "balance_dr_cr": "Dr"},
        {"account_name": "Capital Account", "is_group": 1, "parent_account": "Liability", "account_type": "", "root_type": "Liability", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Current Liability", "is_group": 1, "parent_account": "Liability", "account_type": "", "root_type": "Liability", "balance": 0, "balance_dr_cr": "Dr"},
        {"account_name": "Duties & Taxes", "is_group": 1, "parent_account": "Current Liability", "account_type": "", "root_type": "Liability", "balance": 0, "balance_dr_cr": "Dr"},
        {"account_name": "UAE VAT @ 5 %", "is_group": 0, "parent_account": "Duties & Taxes", "account_type": "Duties and Taxes", "root_type": "Liability", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Trade Payable", "is_group": 0, "parent_account": "Current Liability", "account_type": "", "root_type": "Liability", "balance": 0, "balance_dr_cr": ""},
        {"account_name": "Customer Advances", "is_group": 0, "parent_account": "Current Liability", "account_type": "Unearned Revenue", "root_type": "Liability", "balance": 0, "balance_dr_cr": ""},
    ]

    for account_data in accounts:               
        # Check if the account already exists to avoid duplicates
        if not frappe.db.exists("Account", account_data["account_name"]):
            # Create and insert the new account record
            account = frappe.get_doc({
                "doctype": "Account",
                "account_name": account_data["account_name"],
                "is_group": account_data["is_group"],
                "parent_account": account_data["parent_account"] if account_data["parent_account"]!='' else None ,
                "account_type": account_data["account_type"],
                "root_type": account_data["root_type"],
                "balance": account_data["balance"],
                "balance_dr_cr": account_data["balance_dr_cr"],
            })
            account.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"Inserted: {account_data['account_name']}")
        else:
            print(f"Account already exists: {account_data['account_name']}")

def create_demo_company():
    # Check if company already exists to avoid duplicates
    if not frappe.db.exists("Company", "DEMO COMPANY"):
        # Create new Company document
        company = frappe.get_doc({
            "doctype": "Company",
            "company_name": "DEMO COMPANY",
            "default_currency": "AED",
            "default_payable_account": "Trade Payable",
            "default_receivable_account": "Trade Receivable",
            "stock_received_but_not_billed": "Stock Received But Not Billed",
            "default_inventory_account": "Stock In Hand",
            "round_off_account": "Round Off",
            "default_income_account": "Sales Account",
            "cost_of_goods_sold_account": "Cost Of Goods Sold Account",
            "stock_adjustment_account": "Stock Adjustment A/c",
            "creation": "2022-12-31 09:00:37.024371",
            "owner": "Administrator",
            "country": "United Arab Emirates",                       
            "perdiod_closing_mode": 'Yearly',
            "use_customer_last_price": 1,
            "use_supplier_last_price": 1,
            "update_price_list_price_with_sales_invoice": 1,
            "update_price_list_price_with_purchase_invoice": 1,
            "allow_negative_stock": 1,
            "default_warehouse": "Default Warehouse",
            "rules_for_prices": "Default Selling Price List : Standard Selling Default Buying Price List : Standard Buying Use Default price LIst when customer or supplier price not available: Yes",
            "maintain_stock": 1,
            "update_stock_in_sales_invoice": 1,
            "tax_excluded": 0,
            "tax_type": "VAT",
            "tax": "UAE VAT - 5%",
            "tax_account": "UAE VAT @ 5 %",
            "do_not_apply_round_off_in_si": 0,
            "default_product_expense_account": "Cost Of Goods Sold Account",
            "default_payment_mode_for_purchase": "Cash",
            "default_payment_mode_for_sales": "Cash",
            "default_credit_purchase": 0,
            "default_credit_sale": 0,
            "default_asset_location": "",
            "rate_includes_tax": 0,
            "use_percentage_for_overheads_in_estimate": 1,
            "use_generic_items_for_material_and_labour": 1,
            "default_advance_received_account": "Customer Advances",
            "default_advance_paid_account": "",
            "supplier_terms": "",
            "customer_terms": "",
            "material_receipt_integrated_with_purchase": 1,
            "use_custom_item_group_description_in_estimation": 1,
            "overheads_based_on_percentage": 1
        })
        
        # Insert document into database
        company.insert()
        frappe.db.commit()
        print("DEMO COMPANY created successfully!")
        
        set_default_company_in_global_settings("DEMO COMPANY")
    else:
        print("DEMO COMPANY already exists.")
        
def set_default_company_in_global_settings(company_name):
    # Check if the specified company exists
    if not frappe.db.exists("Company", company_name):
        print(f"Error: Company '{company_name}' does not exist. Please provide a valid company name.")
        return

    # Fetch the Global Defaults single doctype
    global_defaults = frappe.get_single("Global Settings")

    # Set the default company if it's not set or needs updating
    if global_defaults.default_company != company_name:
        global_defaults.default_company = company_name
        global_defaults.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"Success: Default company set to '{company_name}' in Global Defaults.")
    else:
        print(f"Info: The default company is already set to '{company_name}' in Global Defaults.")

def create_default_warehouse():
    """Create a warehouse named 'Default Warehouse' if it doesn't exist."""
    warehouse_name = "Default Warehouse"
    
    # Check if the warehouse already exists
    if not frappe.db.exists("Warehouse", warehouse_name):
        # Create the Default Warehouse
        warehouse = frappe.get_doc({
            "doctype": "Warehouse",
            "warehouse_name": warehouse_name,
            "is_group": 0  # Set to 0 to indicate it's a non-group warehouse
        })
        
        # Insert the warehouse into the database
        warehouse.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Warehouse '{warehouse_name}' created successfully.")
    else:
        print(f"Warehouse '{warehouse_name}' already exists.")

def create_default_item_group():
    """Create a Item Group named 'Default Item Group' if it doesn't exist."""
    item_group_name = "Default Item Group"

    # Check if the warehouse already exists
    if not frappe.db.exists("Item Group", item_group_name):
        # Create the Default Warehouse
        item_group = frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": item_group_name            
        })
        
        # Insert the itemgroup into the database
        item_group.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Item Group '{item_group_name}' created successfully.")
    else:
        print(f"Item Group '{item_group_name}' already exists.")

def create_default_supplier_group():
    """Create a Supplier Group named 'Default Item Group' if it doesn't exist."""
    supplier_group_name = "Default Supplier Group"

    # Check if the warehouse already exists
    if not frappe.db.exists("Supplier Group", supplier_group_name):
        # Create the Default Warehouse
        supplier_group = frappe.get_doc({
            "doctype": "Supplier Group",
            "supplier_group_name": supplier_group_name            
        })
        
        # Insert the itemgroup into the database
        supplier_group.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Supplier Group '{supplier_group_name}' created successfully.")
    else:
        print(f"Supplier Group '{supplier_group_name}' already exists.")

def create_default_customer_group():
    """Create a Customer Group named 'Default Item Group' if it doesn't exist."""
    customer_group_name = "Default Customer Group"

    # Check if the warehouse already exists
    if not frappe.db.exists("Customer Group", customer_group_name):
        # Create the Default Warehouse
        customer_group = frappe.get_doc({
            "doctype": "Customer Group",
            "customer_group_name": customer_group_name            
        })
        
        # Insert the itemgroup into the database
        customer_group.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Customer Group '{customer_group_name}' created successfully.")
    else:
        print(f"Customer Group '{customer_group_name}' already exists.")
       
def create_cash_payment_mode():
     
    payment_mode = "Cash"
    
    # Check if the payment mode is already set to 'Cash' and the account is not 'Main Cash'
    if not frappe.db.exists("Payment Mode", payment_mode):
        # Create a new Payment Mode if it doesn't exist
        payment = frappe.get_doc({
            "doctype": "Payment Mode",
            "payment_mode": payment_mode,
            "mode": "Cash",
            "account": "Main Cash"
        })
        
        # Insert the payment mode into the database
        payment.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Payment mode '{payment_mode}' created successfully.")

def create_tax():
        
    tax_name = "UAE VAT - 5%"

    # Check if the payment mode is already set to 'Cash' and the account is not 'Main Cash'
    if not frappe.db.exists("Tax", tax_name):
        # Create a new Payment Mode if it doesn't exist
        tax = frappe.get_doc({
            "doctype": "Tax",
            "tax_name":tax_name,            
            "tax_type": "VAT",
            "tax_rate": 5,
            "applied_on":"Product Or Service",
            "account" : "UAE VAT @ 5 %"            
        })
        
        # Insert the payment mode into the database
        tax.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Tax '{tax_name}' created successfully.")    

def create_default_base_unit():
    
    unit_name = "PCS"

    # Check if the payment mode is already set to 'Cash' and the account is not 'Main Cash'
    if not frappe.db.exists("Unit", unit_name):
        # Create a new Payment Mode if it doesn't exist
        unit_doc = frappe.get_doc({
            "doctype": "Unit",
            "unit":unit_name
        })
        
        # Insert the payment mode into the database
        unit_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Default Unit '{unit_name}' created successfully.")   


def create_budget_reference_types():
    
    reference_type = "Account Group"
    
    if not frappe.db.exists("Budget Reference Type", reference_type):
        # Create a new Payment Mode if it doesn't exist
        budget_reference_type = frappe.get_doc({
            "doctype": "Budget Reference Type",
            "reference_type": reference_type,
            "budget_against": "Expense"        
        })
    
        # Insert the payment mode into the database
        budget_reference_type.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Budget reference Type '{reference_type}' created successfully.")
    
    reference_type = "Account"
    
    if not frappe.db.exists("Budget Reference Type", reference_type):
        # Create a new Payment Mode if it doesn't exist
        budget_reference_type = frappe.get_doc({
            "doctype": "Budget Reference Type",
            "reference_type": reference_type,
            "budget_against": "Expense"        
        })
    
        # Insert the payment mode into the database
        budget_reference_type.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Budget reference Type, '{reference_type}' created successfully.")
    
    reference_type = "Item Group"
    
    if not frappe.db.exists("Budget Reference Type", reference_type):
        # Create a new Payment Mode if it doesn't exist
        budget_reference_type = frappe.get_doc({
            "doctype": "Budget Reference Type",
            "reference_type": reference_type,
            "budget_against": "Purchase"        
        })
    
        # Insert the payment mode into the database
        budget_reference_type.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Budget reference Type, '{reference_type}' created successfully.")
    
    reference_type = "Item"
    
    if not frappe.db.exists("Budget Reference Type", reference_type):
        # Create a new Payment Mode if it doesn't exist
        budget_reference_type = frappe.get_doc({
            "doctype": "Budget Reference Type",
            "reference_type": reference_type,
            "budget_against": "Purchase"        
        })
    
        # Insert the payment mode into the database
        budget_reference_type.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Budget reference Type, '{reference_type}' created successfully.")
        
def create_default_price_lists():
    
    price_list_name = "Standard Buying"
    
    if not frappe.db.exists("Price List", price_list_name):
        # Create a new Price List if it doesn't exist
        price_list = frappe.get_doc({
            "doctype": "Price List",
            "price_list_name": price_list_name,
            "is_buying": 1       
        })
    
        # Insert the price list into the database
        price_list.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Default Price List, '{price_list_name}' created successfully.")
        
    price_list_name = "Standard Selling"
    
    if not frappe.db.exists("Price List", price_list_name):
        # Create a new Price List if it doesn't exist
        price_list = frappe.get_doc({
            "doctype": "Price List",
            "price_list_name": price_list_name,
            "is_selling": 1       
        })
    
        # Insert the price list into the database
        price_list.insert(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"Default Price List, '{price_list_name}' created successfully.")
        
def populate_area_data():
    
    areas = [
    {"Area": "AL QULAIYA", "Emirate": "Sharjah"},
    {"Area": "AL Qulaiya", "Emirate": "Abu Dhabi"},
    {"Area": "CLOCKTOWER", "Emirate": "Sharjah"},
    {"Area": "AL NAHDAI", "Emirate": "Dubai"},
    {"Area": "JABEL ALI", "Emirate": "Abu Dhabi"},
    {"Area": "Al Quoz", "Emirate": "Dubai"},
    {"Area": "Oud Metha", "Emirate": "Dubai"},
    {"Area": "Oud Mehtha", "Emirate": "Dubai"},
    {"Area": "MANKHOOL", "Emirate": "Dubai"},
    {"Area": "MASAFI", "Emirate": "Fujairah"},
    {"Area": "Sajja", "Emirate": "Sharjah"},
    {"Area": "Industrial Area 10", "Emirate": "Sharjah"},
    {"Area": "Khorfakkan, Sharjah", "Emirate": "Sharjah"},
    {"Area": "Al Ain, Town Center", "Emirate": "Abu Dhabi"},
    {"Area": "Al Jimi, Al Ain", "Emirate": "Abu Dhabi"},
    {"Area": "Al Nabbah", "Emirate": "Sharjah"},
    {"Area": "Jebel Ali", "Emirate": "Dubai"},
    {"Area": "Al Qusais 3", "Emirate": "Dubai"},
    {"Area": "Al Khan", "Emirate": "Sharjah"},
    {"Area": "New Muwailah", "Emirate": "Sharjah"},
    {"Area": "Free Zone", "Emirate": "Sharjah"},
    {"Area": "Abuhail", "Emirate": "Dubai"},
    {"Area": "Al Digdagah", "Emirate": "Ras Al Khaimah"},
    {"Area": "Nasserya", "Emirate": "Sharjah"},
    {"Area": "Maysaloon", "Emirate": "Sharjah"},
    {"Area": "Rashidiya", "Emirate": "Dubai"},
    {"Area": "Industrial Area-6", "Emirate": "Sharjah"},
    {"Area": "Al Manakh", "Emirate": "Sharjah"},
    {"Area": "Umm Ramool", "Emirate": "Dubai"},
    {"Area": "Al Ghafia", "Emirate": "Sharjah"},
    {"Area": "Majaz-3", "Emirate": "Sharjah"},
    {"Area": "Al Nakheel", "Emirate": "Ras Al Khaimah"},
    {"Area": "Al Seer", "Emirate": "Ras Al Khaimah"},
    {"Area": "Dafan Al Khor", "Emirate": "Ras Al Khaimah"},
    {"Area": "Al Shahaba Area", "Emirate": "Sharjah"},
    {"Area": "Al Majaz", "Emirate": "Sharjah"},
    {"Area": "Um Al Tarafa", "Emirate": "Sharjah"},
    {"Area": "Al Mahatah", "Emirate": "Sharjah"},
    {"Area": "Al Qasimia", "Emirate": "Sharjah"},
    {"Area": "Kalba", "Emirate": "Sharjah"},
    {"Area": "Mega Mall", "Emirate": "Sharjah"},
    {"Area": "Garhoud", "Emirate": "Dubai"},
    {"Area": "Fujairah city", "Emirate": "Fujairah"},
    {"Area": "Industrial Area-2", "Emirate": "Sharjah"},
    {"Area": "Hamriya-2, Deira", "Emirate": "Dubai"},
    {"Area": "Al Riqqa, Deira", "Emirate": "Dubai"},
    {"Area": "Muteena, Deira", "Emirate": "Dubai"},
    {"Area": "Muraqqabat, Deira", "Emirate": "Dubai"},
    {"Area": "Jaddaf Waterfront", "Emirate": "Dubai"},
    {"Area": "Al Dhait", "Emirate": "Ras Al Khaimah"},
    {"Area": "Al Jazeera", "Emirate": "Ras Al Khaimah"},
    {"Area": "Yarmook", "Emirate": "Sharjah"},
    {"Area": "Al Ghubaiba", "Emirate": "Sharjah"},
    {"Area": "Buhaira", "Emirate": "Sharjah"},
    {"Area": "Al Nahda 1", "Emirate": "Dubai"},
    {"Area": "Al Nahda 2", "Emirate": "Dubai"},
    {"Area": "Cricket Stadium", "Emirate": "Sharjah"},
    {"Area": "Al Bu Daniq", "Emirate": "Sharjah"},
    {"Area": "Al Ras", "Emirate": "Umm Al Quwain"},
    {"Area": "Al Quds", "Emirate": "Dubai"},
    {"Area": "Istiqlal Street - Al Bu Daniq", "Emirate": "Sharjah"},
    {"Area": "Satwa", "Emirate": "Dubai"},
    {"Area": "International City", "Emirate": "Dubai"},
    {"Area": "Jumairah", "Emirate": "Dubai"},
    {"Area": "Al Barsha", "Emirate": "Dubai"},
    {"Area": "Bur Dubai", "Emirate": "Dubai"},
    {"Area": "Deira", "Emirate": "Dubai"},
    {"Area": "Naif", "Emirate": "Dubai"},
    {"Area": "Al Nahda", "Emirate": "Sharjah"},
    {"Area": "Muwaileh", "Emirate": "Sharjah"},
    {"Area": "Dhaid", "Emirate": "Sharjah"},
    {"Area": "Maliha", "Emirate": "Sharjah"},
    {"Area": "King Faizal Street", "Emirate": "Sharjah"},
    {"Area": "Al Wahda Street", "Emirate": "Sharjah"},
    {"Area": "Al Taawun", "Emirate": "Sharjah"},
    {"Area": "Majaz-2", "Emirate": "Sharjah"},
    {"Area": "Karama", "Emirate": "Ajman"},
    {"Area": "Abu Shagara", "Emirate": "Sharjah"},
    {"Area": "Rolla", "Emirate": "Sharjah"},
    {"Area": "Karama", "Emirate": "Dubai"},
    {"Area": "Majaz-1", "Emirate": "Sharjah"}
    ]
    for area in areas:
        # Check if the area already exists to avoid duplicates
        if not frappe.db.exists("Area", {"area": area["Area"], "emirate": area["Emirate"]}):
            # Create a new Area document
            area_doc = frappe.get_doc({
                "doctype": "Area"                
                "area": area["Area"],
                "emirate": area["Emirate"]
            })
            # Insert the document into the database
            area_doc.insert()
            print(f"Inserted Area: {area['Area']} in {area['Emirate']}")
        else:
            print(f"Area already exists: {area['Area']} in {area['Emirate']}")
