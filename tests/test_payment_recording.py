"""
Payment recording tests for Odoo Client (Phase 4: T066-T078)

Tests cover:
- Payment recording with validation
- Invoice state verification
- Amount validation
- Idempotency
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp_servers'))


@pytest.fixture
def odoo_client():
    """Fixture providing OdooClient instance."""
    from odoo_client import OdooClient
    return OdooClient()


@pytest.fixture
def mock_xmlrpc():
    """Fixture providing mocked XML-RPC connections."""
    with patch('xmlrpc.client.ServerProxy') as mock_proxy:
        mock_common = MagicMock()
        mock_models = MagicMock()

        def server_proxy_side_effect(url):
            if 'common' in url:
                return mock_common
            elif 'object' in url:
                return mock_models
            return MagicMock()

        mock_proxy.side_effect = server_proxy_side_effect

        yield {
            'proxy': mock_proxy,
            'common': mock_common,
            'models': mock_models
        }


# ============================================================================
# Payment Recording Tests (T066-T071)
# ============================================================================

class TestPaymentRecording:
    """Test payment recording functionality."""

    def test_record_payment_success(self, odoo_client, mock_xmlrpc):
        """Test successful payment recording (T066)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock sequential calls:
        # 1. Get invoice details (exists, posted, has balance)
        # 2. Check for existing payment (idempotency)
        # 3. Create payment
        # 4. Post payment (action_post)
        mock_xmlrpc['models'].execute_kw.side_effect = [
            [{"id": 100, "state": "posted", "amount_residual": 200.00, "partner_id": [7, "Test Customer"]}],  # Invoice details
            [],  # No existing payment
            500,  # Payment ID created
            True  # action_post successful
        ]

        payment_id = odoo_client.record_payment(
            invoice_id=100,
            amount=200.00,
            payment_date="2026-03-17",
            payment_method="bank",
            approval_id="approval_20260317_143022_payment"
        )

        assert payment_id == 500

    def test_record_payment_invoice_not_found(self, odoo_client, mock_xmlrpc):
        """Test payment recording with non-existent invoice (T067)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: invoice not found
        mock_xmlrpc['models'].execute_kw.return_value = []

        with pytest.raises(ValueError, match="Invoice.*not found"):
            odoo_client.record_payment(
                invoice_id=99999,
                amount=100.00,
                payment_date="2026-03-17",
                payment_method="bank",
                approval_id="approval_test"
            )

    def test_record_payment_invoice_not_posted(self, odoo_client, mock_xmlrpc):
        """Test payment recording for draft invoice (T068)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: invoice in draft state
        mock_xmlrpc['models'].execute_kw.return_value = [
            {"id": 100, "state": "draft", "amount_residual": 200.00}
        ]

        with pytest.raises(ValueError, match="not posted"):
            odoo_client.record_payment(
                invoice_id=100,
                amount=100.00,
                payment_date="2026-03-17",
                payment_method="bank",
                approval_id="approval_test"
            )

    def test_record_payment_amount_exceeds_balance(self, odoo_client, mock_xmlrpc):
        """Test payment recording with amount exceeding balance (T069)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: invoice with lower balance
        mock_xmlrpc['models'].execute_kw.return_value = [
            {"id": 100, "state": "posted", "amount_residual": 50.00}
        ]

        with pytest.raises(ValueError, match="exceeds.*balance"):
            odoo_client.record_payment(
                invoice_id=100,
                amount=100.00,
                payment_date="2026-03-17",
                payment_method="bank",
                approval_id="approval_test"
            )

    def test_record_payment_partial_payment(self, odoo_client, mock_xmlrpc):
        """Test partial payment recording (T070)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: invoice with higher balance, partial payment
        mock_xmlrpc['models'].execute_kw.side_effect = [
            [{"id": 100, "state": "posted", "amount_residual": 200.00, "partner_id": [7, "Test Customer"]}],  # Invoice details
            [],  # No existing payment
            500,  # Payment ID created
            True  # action_post successful
        ]

        payment_id = odoo_client.record_payment(
            invoice_id=100,
            amount=50.00,  # Partial payment
            payment_date="2026-03-17",
            payment_method="bank",
            approval_id="approval_test"
        )

        assert payment_id == 500

    def test_record_payment_idempotency(self, odoo_client, mock_xmlrpc):
        """Test payment recording idempotency (T071)."""
        mock_xmlrpc['common'].authenticate.return_value = 2
        odoo_client.authenticate()

        # Mock: payment already exists with same approval_id
        mock_xmlrpc['models'].execute_kw.side_effect = [
            [{"id": 100, "state": "posted", "amount_residual": 200.00, "partner_id": [7, "Test Customer"]}],  # Invoice details
            [{"id": 500}]  # Existing payment found
        ]

        payment_id = odoo_client.record_payment(
            invoice_id=100,
            amount=200.00,
            payment_date="2026-03-17",
            payment_method="bank",
            approval_id="approval_20260317_143022_payment"
        )

        # Should return existing payment ID
        assert payment_id == 500
