"""
Unit tests for Odoo Client

Tests cover:
- Authentication and session management
- Utility functions (masking, approval ID generation)
- Error handling and retry logic
- Circuit breaker integration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import xmlrpc.client

# Import will work after odoo_client.py is in place
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp_servers'))

from odoo_client import (
    OdooClient,
    mask_financial_data,
    generate_approval_id,
    create_approval_request_file
)


@pytest.fixture
def odoo_client():
    """Fixture providing OdooClient instance for testing."""
    with patch.dict(os.environ, {
        'ODOO_URL': 'http://localhost:8069',
        'ODOO_DB': 'odoo',
        'ODOO_USERNAME': 'admin',
        'ODOO_PASSWORD': 'admin'
    }):
        client = OdooClient()
        return client


@pytest.fixture
def mock_xmlrpc():
    """Fixture providing mocked XML-RPC connections."""
    with patch('xmlrpc.client.ServerProxy') as mock_proxy:
        mock_common = MagicMock()
        mock_models = MagicMock()

        def proxy_side_effect(url, **kwargs):
            if 'xmlrpc/2/common' in url:
                return mock_common
            elif 'xmlrpc/2/object' in url:
                return mock_models
            return MagicMock()

        mock_proxy.side_effect = proxy_side_effect

        yield {
            'proxy': mock_proxy,
            'common': mock_common,
            'models': mock_models
        }


# ============================================================================
# Utility Function Tests (Phase 2: T011-T014)
# ============================================================================

class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_mask_financial_data(self):
        """Test that financial amounts are masked correctly (T011)."""
        # Test simple amount masking
        data = {"amount": 1500.00, "name": "Invoice"}
        masked = mask_financial_data(data)
        assert masked["amount"] == "***"
        assert masked["name"] == "Invoice"

        # Test nested structure
        data = {
            "invoice": {
                "total": 2500.50,
                "subtotal": 2000.00,
                "tax": 500.50
            },
            "customer": "Test Customer"
        }
        masked = mask_financial_data(data)
        assert masked["invoice"]["total"] == "***"
        assert masked["invoice"]["subtotal"] == "***"
        assert masked["invoice"]["tax"] == "***"
        assert masked["customer"] == "Test Customer"

        # Test list of items with amounts
        data = {
            "line_items": [
                {"product": "Item 1", "price": 100.00, "quantity": 2},
                {"product": "Item 2", "price": 200.00, "quantity": 1}
            ]
        }
        masked = mask_financial_data(data)
        assert masked["line_items"][0]["price"] == "***"
        assert masked["line_items"][1]["price"] == "***"
        assert masked["line_items"][0]["product"] == "Item 1"

        # Test various amount field names
        data = {
            "amount": 100.00,
            "total": 200.00,
            "subtotal": 150.00,
            "price": 50.00,
            "cost": 30.00,
            "balance": 70.00,
            "payment": 100.00,
            "name": "Keep this"
        }
        masked = mask_financial_data(data)
        assert masked["amount"] == "***"
        assert masked["total"] == "***"
        assert masked["subtotal"] == "***"
        assert masked["price"] == "***"
        assert masked["cost"] == "***"
        assert masked["balance"] == "***"
        assert masked["payment"] == "***"
        assert masked["name"] == "Keep this"

    def test_generate_approval_id(self):
        """Test approval ID generation format (T013)."""
        # Test invoice approval ID
        approval_id = generate_approval_id("invoice")
        assert approval_id.startswith("approval_")
        assert "_invoice" in approval_id

        # Verify format: approval_YYYYMMDD_HHMMSS_type
        parts = approval_id.split("_")
        assert len(parts) == 4
        assert parts[0] == "approval"
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 6  # HHMMSS
        assert parts[3] == "invoice"

        # Test payment approval ID
        approval_id = generate_approval_id("payment")
        assert "_payment" in approval_id

        # Test uniqueness (two calls should generate different IDs)
        import time
        id1 = generate_approval_id("test")
        time.sleep(1)
        id2 = generate_approval_id("test")
        assert id1 != id2


# ============================================================================
# Authentication Tests (Phase 2: T015-T022)
# ============================================================================

class TestAuthentication:
    """Tests for Odoo authentication."""

    def test_authenticate_success(self, odoo_client, mock_xmlrpc):
        """Test successful authentication (T015)."""
        # Mock successful authentication
        mock_xmlrpc['common'].authenticate.return_value = 2  # User ID

        uid = odoo_client.authenticate()

        assert uid == 2
        assert odoo_client.uid == 2
        mock_xmlrpc['common'].authenticate.assert_called_once_with(
            'odoo', 'admin', 'admin', {}
        )

    def test_authenticate_failure_invalid_credentials(self, odoo_client, mock_xmlrpc):
        """Test authentication failure with invalid credentials (T016)."""
        # Mock failed authentication (returns False)
        mock_xmlrpc['common'].authenticate.return_value = False

        with pytest.raises(Exception) as exc_info:
            odoo_client.authenticate()

        assert "Authentication failed" in str(exc_info.value)

    def test_authenticate_with_retry_on_network_error(self, odoo_client, mock_xmlrpc):
        """Test authentication retry on network error (T017)."""
        # Mock network error on first call, success on second
        mock_xmlrpc['common'].authenticate.side_effect = [
            ConnectionError("Network error"),
            2  # Success on retry
        ]

        # With @with_retry decorator, this should succeed after retry
        uid = odoo_client.authenticate()
        assert uid == 2
        assert mock_xmlrpc['common'].authenticate.call_count == 2


# ============================================================================
# Session Management Tests (Phase 2: T023-T027)
# ============================================================================

class TestSessionManagement:
    """Tests for session management."""

    def test_session_renewal_on_expiration(self, odoo_client, mock_xmlrpc):
        """Test session renewal when expired (T023)."""
        # First authentication
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()
        assert odoo_client.uid == 2

        # Simulate session expiration by clearing uid
        odoo_client.uid = None

        # Call _ensure_authenticated should re-authenticate
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client._ensure_authenticated()
        assert odoo_client.uid == 2

    def test_session_reuse_across_calls(self, odoo_client, mock_xmlrpc):
        """Test session reuse across multiple calls (T024)."""
        # First authentication
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Multiple calls to _ensure_authenticated should not re-authenticate
        odoo_client._ensure_authenticated()
        odoo_client._ensure_authenticated()

        # authenticate should only be called once
        assert mock_xmlrpc['common'].authenticate.call_count == 1


# ============================================================================
# Approval Request Tests (Phase 2: T028-T030)
# ============================================================================

class TestApprovalRequest:
    """Tests for approval request generation."""

    def test_create_approval_request_file(self, tmp_path):
        """Test approval request file creation (T028)."""
        vault_path = str(tmp_path / "AI_Employee_Vault")
        os.makedirs(f"{vault_path}/Pending_Approval", exist_ok=True)

        # Test invoice approval request
        invoice_data = {
            "customer_id": 7,
            "invoice_date": "2026-03-17",
            "line_items": [
                {"product_id": 1, "quantity": 2, "price_unit": 150.00}
            ]
        }
        approval_id = "approval_20260317_143022_invoice"

        file_path = create_approval_request_file(
            "invoice",
            invoice_data,
            approval_id,
            vault_path
        )

        # Verify file was created
        assert os.path.exists(file_path)
        assert "Pending_Approval" in file_path
        assert "APPROVAL_invoice" in file_path

        # Verify file content
        with open(file_path, 'r') as f:
            content = f.read()

        # Check YAML frontmatter
        assert "---" in content
        assert f"approval_id: {approval_id}" in content
        assert "operation: invoice" in content
        assert "status: pending" in content

        # Check markdown body
        assert "# Approval Request: Create Invoice" in content
        assert '"customer_id": 7' in content  # JSON format

        # Test payment approval request
        payment_data = {
            "invoice_id": 123,
            "amount": 1500.00,
            "payment_date": "2026-03-17"
        }
        approval_id = "approval_20260317_143023_payment"

        file_path = create_approval_request_file(
            "payment",
            payment_data,
            approval_id,
            vault_path
        )

        assert os.path.exists(file_path)
        assert "APPROVAL_payment" in file_path


# ============================================================================
# Phase 3: Invoice Creation Tests (US1)
# ============================================================================

class TestInvoiceCreation:
    """Tests for invoice creation functionality (User Story 1)."""

    def test_create_draft_invoice_success(self, odoo_client, mock_xmlrpc):
        """Test successful draft invoice creation (T031)."""
        # Mock authentication
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock sequential execute_kw calls:
        # 1. Check for existing invoice (idempotency) - returns empty list
        # 2. Validate customer - returns customer data
        # 3. Validate product - returns product data
        # 4. Create invoice - returns invoice ID
        mock_xmlrpc['models'].execute_kw.side_effect = [
            [],  # No existing invoice
            [{"id": 7, "name": "Test Customer"}],  # Customer found
            [{"id": 1, "name": "Test Product"}],  # Product found
            100  # Invoice created with ID 100
        ]

        invoice_data = {
            "customer_id": 7,
            "invoice_date": "2026-03-17",
            "line_items": [
                {"product_id": 1, "quantity": 2, "price_unit": 150.00, "description": "Consulting"}
            ],
            "approval_id": "approval_20260317_143022_invoice"
        }

        invoice_id = odoo_client.create_draft_invoice(**invoice_data)

        assert invoice_id == 100

    def test_create_draft_invoice_invalid_customer(self, odoo_client, mock_xmlrpc):
        """Test invoice creation with invalid customer (T032)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock sequential calls:
        # 1. Check for existing invoice - returns empty list
        # 2. Validate customer - returns empty list (customer not found)
        mock_xmlrpc['models'].execute_kw.side_effect = [
            [],  # No existing invoice
            []   # Customer not found
        ]

        invoice_data = {
            "customer_id": 99999,  # Non-existent customer
            "invoice_date": "2026-03-17",
            "line_items": [{"product_id": 1, "quantity": 1, "price_unit": 100.00}],
            "approval_id": "approval_test"
        }

        with pytest.raises(ValueError, match="Customer.*not found"):
            odoo_client.create_draft_invoice(**invoice_data)

    def test_create_draft_invoice_invalid_product(self, odoo_client, mock_xmlrpc):
        """Test invoice creation with invalid product (T033)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock sequential calls:
        # 1. Check for existing invoice - returns empty list
        # 2. Validate customer - returns customer data
        # 3. Validate product - returns empty list (product not found)
        mock_xmlrpc['models'].execute_kw.side_effect = [
            [],  # No existing invoice
            [{"id": 7, "name": "Test Customer"}],  # Customer found
            []   # Product not found
        ]

        invoice_data = {
            "customer_id": 7,
            "invoice_date": "2026-03-17",
            "line_items": [{"product_id": 99999, "quantity": 1, "price_unit": 100.00}],
            "approval_id": "approval_test"
        }

        with pytest.raises(ValueError, match="Product.*not found"):
            odoo_client.create_draft_invoice(**invoice_data)

    def test_create_draft_invoice_with_multiple_line_items(self, odoo_client, mock_xmlrpc):
        """Test invoice creation with multiple line items (T034)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock sequential calls:
        # 1. Check for existing invoice - returns empty list
        # 2. Validate customer - returns customer data
        # 3-5. Validate 3 products - returns product data for each
        # 6. Create invoice - returns invoice ID
        mock_xmlrpc['models'].execute_kw.side_effect = [
            [],  # No existing invoice
            [{"id": 7, "name": "Test Customer"}],  # Customer found
            [{"id": 1, "name": "Product 1"}],  # Product 1 found
            [{"id": 2, "name": "Product 2"}],  # Product 2 found
            [{"id": 3, "name": "Product 3"}],  # Product 3 found
            101  # Invoice created with ID 101
        ]

        invoice_data = {
            "customer_id": 7,
            "invoice_date": "2026-03-17",
            "line_items": [
                {"product_id": 1, "quantity": 2, "price_unit": 150.00, "description": "Service 1"},
                {"product_id": 2, "quantity": 1, "price_unit": 500.00, "description": "Service 2"},
                {"product_id": 3, "quantity": 3, "price_unit": 250.00, "description": "Product"}
            ],
            "approval_id": "approval_test"
        }

        invoice_id = odoo_client.create_draft_invoice(**invoice_data)
        assert invoice_id == 101

    def test_create_draft_invoice_idempotency(self, odoo_client, mock_xmlrpc):
        """Test invoice creation idempotency via approval_id (T035)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        approval_id = "approval_20260317_143022_invoice"

        # Mock: invoice with this approval_id already exists
        mock_xmlrpc['models'].execute_kw.return_value = [{"id": 100}]

        invoice_data = {
            "customer_id": 7,
            "invoice_date": "2026-03-17",
            "line_items": [{"product_id": 1, "quantity": 1, "price_unit": 100.00}],
            "approval_id": approval_id
        }

        # Should return existing invoice ID instead of creating new one
        invoice_id = odoo_client.create_draft_invoice(**invoice_data)
        assert invoice_id == 100


# ============================================================================
# Phase 3: Invoice Finalization Tests (US1)
# ============================================================================

class TestInvoiceFinalization:
    """Tests for invoice finalization functionality (User Story 1)."""

    def test_finalize_invoice_success(self, odoo_client, mock_xmlrpc):
        """Test successful invoice finalization (T043)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock sequential calls:
        # 1. Check invoice exists and is in draft state
        # 2. Post the invoice
        mock_xmlrpc['models'].execute_kw.side_effect = [
            [{"id": 100, "state": "draft"}],  # Invoice found in draft state
            True  # action_post successful
        ]

        result = odoo_client.finalize_invoice(100)
        assert result is True

    def test_finalize_invoice_not_found(self, odoo_client, mock_xmlrpc):
        """Test finalization of non-existent invoice (T044)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: invoice not found
        mock_xmlrpc['models'].execute_kw.return_value = []

        with pytest.raises(ValueError, match="Invoice.*not found"):
            odoo_client.finalize_invoice(99999)

    def test_finalize_invoice_already_posted(self, odoo_client, mock_xmlrpc):
        """Test finalization of already posted invoice (T045)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: invoice already posted
        mock_xmlrpc['models'].execute_kw.return_value = [{"id": 100, "state": "posted"}]

        with pytest.raises(ValueError, match="already posted"):
            odoo_client.finalize_invoice(100)


# ============================================================================
# Invoice Querying Tests (T096-T101)
# ============================================================================

class TestInvoiceQuerying:
    """Test invoice search and querying functionality."""

    def test_search_invoices_no_filters(self, odoo_client, mock_xmlrpc):
        """Test searching invoices without filters (T096)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: return list of invoices
        mock_xmlrpc['models'].execute_kw.return_value = [
            {
                "id": 100,
                "name": "INV/2026/0001",
                "partner_id": [7, "Test Customer"],
                "invoice_date": "2026-03-17",
                "state": "posted",
                "amount_total": 300.00,
                "amount_residual": 300.00
            },
            {
                "id": 101,
                "name": "INV/2026/0002",
                "partner_id": [8, "Another Customer"],
                "invoice_date": "2026-03-18",
                "state": "draft",
                "amount_total": 500.00,
                "amount_residual": 500.00
            }
        ]

        result = odoo_client.search_invoices()

        assert len(result) == 2
        assert result[0]['id'] == 100
        assert result[0]['name'] == "INV/2026/0001"
        assert result[1]['id'] == 101

    def test_search_invoices_by_date_range(self, odoo_client, mock_xmlrpc):
        """Test searching invoices by date range (T097)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: return invoices within date range
        mock_xmlrpc['models'].execute_kw.return_value = [
            {
                "id": 100,
                "name": "INV/2026/0001",
                "partner_id": [7, "Test Customer"],
                "invoice_date": "2026-03-17",
                "state": "posted",
                "amount_total": 300.00,
                "amount_residual": 0.00
            }
        ]

        result = odoo_client.search_invoices(
            date_from="2026-03-01",
            date_to="2026-03-31"
        )

        assert len(result) == 1
        assert result[0]['invoice_date'] == "2026-03-17"

    def test_search_invoices_by_customer(self, odoo_client, mock_xmlrpc):
        """Test searching invoices by customer ID (T098)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: return invoices for specific customer
        mock_xmlrpc['models'].execute_kw.return_value = [
            {
                "id": 100,
                "name": "INV/2026/0001",
                "partner_id": [7, "Test Customer"],
                "invoice_date": "2026-03-17",
                "state": "posted",
                "amount_total": 300.00,
                "amount_residual": 0.00
            }
        ]

        result = odoo_client.search_invoices(customer_id=7)

        assert len(result) == 1
        assert result[0]['partner_id'][0] == 7

    def test_search_invoices_by_status(self, odoo_client, mock_xmlrpc):
        """Test searching invoices by status (T099)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: return only posted invoices
        mock_xmlrpc['models'].execute_kw.return_value = [
            {
                "id": 100,
                "name": "INV/2026/0001",
                "partner_id": [7, "Test Customer"],
                "invoice_date": "2026-03-17",
                "state": "posted",
                "amount_total": 300.00,
                "amount_residual": 0.00
            }
        ]

        result = odoo_client.search_invoices(status="posted")

        assert len(result) == 1
        assert result[0]['state'] == "posted"

    def test_search_invoices_pagination(self, odoo_client, mock_xmlrpc):
        """Test invoice search with pagination (T100)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: return paginated results
        mock_xmlrpc['models'].execute_kw.return_value = [
            {
                "id": 105,
                "name": "INV/2026/0005",
                "partner_id": [7, "Test Customer"],
                "invoice_date": "2026-03-17",
                "state": "posted",
                "amount_total": 300.00,
                "amount_residual": 0.00
            }
        ]

        result = odoo_client.search_invoices(limit=1, offset=4)

        assert len(result) == 1
        assert result[0]['id'] == 105

    def test_search_invoices_empty_results(self, odoo_client, mock_xmlrpc):
        """Test searching invoices with no matching results (T101)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: return empty list
        mock_xmlrpc['models'].execute_kw.return_value = []

        result = odoo_client.search_invoices(customer_id=99999)

        assert len(result) == 0
        assert result == []


# ============================================================================
# Financial Reporting Tests (T119-T122)
# ============================================================================

class TestFinancialReporting:
    """Test financial report generation functionality."""

    def test_get_revenue_summary(self, odoo_client, mock_xmlrpc):
        """Test revenue summary report generation (T119)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: return invoices for revenue calculation
        mock_xmlrpc['models'].execute_kw.return_value = [
            {
                "id": 100,
                "name": "INV/2026/0001",
                "state": "posted",
                "amount_total": 300.00,
                "invoice_date": "2026-03-17"
            },
            {
                "id": 101,
                "name": "INV/2026/0002",
                "state": "posted",
                "amount_total": 500.00,
                "invoice_date": "2026-03-18"
            }
        ]

        result = odoo_client.get_financial_report(
            report_type="revenue_summary",
            date_from="2026-03-01",
            date_to="2026-03-31"
        )

        assert result['report_type'] == "revenue_summary"
        assert result['total_revenue'] == 800.00
        assert result['invoice_count'] == 2

    def test_get_receivables_report(self, odoo_client, mock_xmlrpc):
        """Test receivables report generation (T120)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: return invoices with outstanding balances
        mock_xmlrpc['models'].execute_kw.return_value = [
            {
                "id": 100,
                "name": "INV/2026/0001",
                "state": "posted",
                "amount_total": 300.00,
                "amount_residual": 300.00,
                "partner_id": [7, "Test Customer"]
            },
            {
                "id": 101,
                "name": "INV/2026/0002",
                "state": "posted",
                "amount_total": 500.00,
                "amount_residual": 250.00,
                "partner_id": [8, "Another Customer"]
            }
        ]

        result = odoo_client.get_financial_report(
            report_type="receivables",
            date_from="2026-03-01",
            date_to="2026-03-31"
        )

        assert result['report_type'] == "receivables"
        assert result['total_outstanding'] == 550.00
        assert result['invoice_count'] == 2

    def test_get_payment_collection_metrics(self, odoo_client, mock_xmlrpc):
        """Test payment collection metrics report (T121)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: return invoices with payment status
        mock_xmlrpc['models'].execute_kw.return_value = [
            {
                "id": 100,
                "name": "INV/2026/0001",
                "state": "posted",
                "amount_total": 300.00,
                "amount_residual": 0.00  # Fully paid
            },
            {
                "id": 101,
                "name": "INV/2026/0002",
                "state": "posted",
                "amount_total": 500.00,
                "amount_residual": 250.00  # Partially paid
            },
            {
                "id": 102,
                "name": "INV/2026/0003",
                "state": "posted",
                "amount_total": 200.00,
                "amount_residual": 200.00  # Unpaid
            }
        ]

        result = odoo_client.get_financial_report(
            report_type="payment_collection",
            date_from="2026-03-01",
            date_to="2026-03-31"
        )

        assert result['report_type'] == "payment_collection"
        assert result['total_invoiced'] == 1000.00
        assert result['total_collected'] == 550.00
        assert result['collection_rate'] == 55.0

    def test_financial_report_empty_period(self, odoo_client, mock_xmlrpc):
        """Test financial report with no data in period (T122)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: return empty list
        mock_xmlrpc['models'].execute_kw.return_value = []

        result = odoo_client.get_financial_report(
            report_type="revenue_summary",
            date_from="2026-01-01",
            date_to="2026-01-31"
        )

        assert result['report_type'] == "revenue_summary"
        assert result['total_revenue'] == 0.00
        assert result['invoice_count'] == 0

