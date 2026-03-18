#!/usr/bin/env python3
"""
Verify Odoo setup and create test data for integration tests.

This script:
1. Verifies Odoo Accounting module is installed
2. Creates test customer for integration tests
3. Creates test products for invoice line items
"""

import xmlrpc.client
import os
from dotenv import load_dotenv

load_dotenv()

# Odoo connection details
url = os.getenv("ODOO_URL", "http://localhost:8069")
db = os.getenv("ODOO_DB", "odoo")
username = os.getenv("ODOO_USERNAME", "admin")
password = os.getenv("ODOO_PASSWORD", "admin")

print(f"Connecting to Odoo at {url}...")

# Authenticate
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

if not uid:
    print("❌ Authentication failed!")
    exit(1)

print(f"✅ Authenticated as user ID: {uid}")

# Connect to models
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Task T003: Verify Accounting module is installed
print("\n=== T003: Verifying Accounting Module ===")
account_module = models.execute_kw(
    db, uid, password,
    'ir.module.module', 'search_read',
    [[['name', '=', 'account'], ['state', '=', 'installed']]],
    {'fields': ['name', 'state'], 'limit': 1}
)

if account_module:
    print(f"✅ Accounting module installed: {account_module[0]}")
else:
    print("❌ Accounting module NOT installed!")
    exit(1)

# Task T004: Create test customer
print("\n=== T004: Creating Test Customer ===")

# Check if test customer already exists
existing_customer = models.execute_kw(
    db, uid, password,
    'res.partner', 'search_read',
    [[['name', '=', 'Test Customer AI Employee']]],
    {'fields': ['id', 'name'], 'limit': 1}
)

if existing_customer:
    customer_id = existing_customer[0]['id']
    print(f"✅ Test customer already exists: ID {customer_id}")
else:
    # Create new test customer
    customer_id = models.execute_kw(
        db, uid, password,
        'res.partner', 'create',
        [{
            'name': 'Test Customer AI Employee',
            'email': 'test.customer@aiemployee.com',
            'phone': '+1-555-0100',
            'street': '123 Test Street',
            'city': 'Test City',
            'zip': '12345',
            'country_id': 233,  # United States
            'customer_rank': 1,
            'is_company': True
        }]
    )
    print(f"✅ Created test customer: ID {customer_id}")

# Task T005: Create test products
print("\n=== T005: Creating Test Products ===")

test_products = [
    {
        'name': 'Test Product - Consulting Service',
        'default_code': 'TEST-CONSULT-001',
        'type': 'service',
        'list_price': 150.00,
        'standard_price': 100.00,
        'uom_id': 1,  # Units
        'uom_po_id': 1,
        'sale_ok': True,
        'purchase_ok': False
    },
    {
        'name': 'Test Product - Software License',
        'default_code': 'TEST-LICENSE-001',
        'type': 'service',
        'list_price': 500.00,
        'standard_price': 300.00,
        'uom_id': 1,
        'uom_po_id': 1,
        'sale_ok': True,
        'purchase_ok': False
    },
    {
        'name': 'Test Product - Hardware Item',
        'default_code': 'TEST-HARDWARE-001',
        'type': 'consu',  # Consumable/storable product in Odoo 17
        'list_price': 250.00,
        'standard_price': 150.00,
        'uom_id': 1,
        'uom_po_id': 1,
        'sale_ok': True,
        'purchase_ok': True
    }
]

created_products = []
for product_data in test_products:
    # Check if product already exists
    existing_product = models.execute_kw(
        db, uid, password,
        'product.product', 'search_read',
        [[['default_code', '=', product_data['default_code']]]],
        {'fields': ['id', 'name'], 'limit': 1}
    )

    if existing_product:
        product_id = existing_product[0]['id']
        print(f"✅ Product already exists: {product_data['name']} (ID {product_id})")
        created_products.append(product_id)
    else:
        # Create new product
        product_id = models.execute_kw(
            db, uid, password,
            'product.product', 'create',
            [product_data]
        )
        print(f"✅ Created product: {product_data['name']} (ID {product_id})")
        created_products.append(product_id)

print("\n=== Summary ===")
print(f"✅ Odoo Accounting module: INSTALLED")
print(f"✅ Test customer ID: {customer_id}")
print(f"✅ Test product IDs: {created_products}")
print("\n✅ Phase 1 setup complete! Ready for Phase 2 implementation.")
