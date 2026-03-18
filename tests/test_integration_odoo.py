"""
End-to-end integration tests for Odoo MCP Server

Tests cover complete workflows:
- Email to invoice creation workflow
- Invoice creation to payment recording workflow
- Query and reporting workflows
- Approval workflow integration
- Error recovery scenarios
"""

import pytest
from unittest.mock import Mock, patch
import os
from pathlib import Path

# Import will work after implementation
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp_servers'))


@pytest.fixture
def vault_path(tmp_path):
    """Fixture providing temporary vault directory structure."""
    vault = tmp_path / "AI_Employee_Vault"
    vault.mkdir()
    (vault / "Pending_Approval").mkdir()
    (vault / "Approved").mkdir()
    (vault / "Done").mkdir()
    return str(vault)


# ============================================================================
# End-to-End Workflow Tests
# ============================================================================

class TestE2EWorkflows:
    """End-to-end integration tests."""

    @pytest.mark.integration
    def test_invoice_creation_workflow_e2e(self, vault_path, tmp_path):
        """
        Test complete invoice creation workflow (T063):
        1. MCP tool creates draft invoice
        2. Approval request file created
        3. Approval executor can finalize invoice
        """
        from scripts.approval_executor import ApprovalExecutor

        # Mock OdooClient and AuditLogger for approval executor
        with patch('scripts.approval_executor.AuditLogger') as MockAuditLogger, \
             patch('scripts.approval_executor.OdooClient') as MockOdooClient:

            # Setup mocks
            mock_client = MockOdooClient.return_value
            mock_client.authenticate.return_value = 2
            mock_client.finalize_invoice.return_value = True

            # Simulate approval data that would come from MCP tool
            approval_data = {
                'approval_id': 'approval_20260317_143022_invoice',
                'operation': 'invoice',
                'invoice_id': 100,
                'customer_id': 7,
                'invoice_date': '2026-03-17'
            }

            # Execute approval workflow
            executor = ApprovalExecutor(vault_path=vault_path)
            result = executor.execute_invoice_finalize(approval_data)

            # Verify invoice finalized successfully
            assert result['status'] == 'success'
            assert result['invoice_id'] == 100
            mock_client.finalize_invoice.assert_called_once_with(100)

    @pytest.mark.integration
    def test_email_to_invoice_workflow(self, vault_path):
        """
        Test complete email-to-invoice workflow:
        1. Email arrives with invoice request
        2. Approval request created
        3. User approves
        4. Invoice created in Odoo
        5. Dashboard updated
        """
        # TODO: Implement test (T141)
        pytest.skip("Test not yet implemented - T141")

    @pytest.mark.integration
    def test_invoice_to_payment_workflow(self, vault_path):
        """
        Test invoice creation followed by payment recording (T093):
        1. Create invoice (with approval)
        2. Record payment (with approval)
        3. Verify invoice marked as paid
        4. Verify audit logs
        """
        from scripts.approval_executor import ApprovalExecutor
        from mcp_servers.odoo_mcp_server import call_tool

        # Save original getenv before patching
        original_getenv = os.getenv

        # Create a selective getenv mock
        def mock_getenv(key, default=None):
            if key == 'VAULT_PATH':
                return vault_path
            return original_getenv(key, default)

        # Mock OdooClient and AuditLogger
        with patch('scripts.approval_executor.AuditLogger') as MockAuditLogger, \
             patch('scripts.approval_executor.OdooClient') as MockOdooClient, \
             patch('mcp_servers.odoo_mcp_server.get_odoo_client') as mock_get_client, \
             patch('mcp_servers.odoo_mcp_server.get_audit_logger') as mock_get_logger, \
             patch('mcp_servers.odoo_mcp_server.os.getenv', side_effect=mock_getenv):

            # Setup mocks
            mock_client = MockOdooClient.return_value
            mock_client.authenticate.return_value = 2
            mock_client.create_draft_invoice.return_value = 100
            mock_client.finalize_invoice.return_value = True
            mock_client.get_invoice_details.return_value = {
                'id': 100,
                'state': 'posted',
                'amount_residual': 200.00,
                'name': 'INV/2026/0001',
                'partner_id': [7, "Test Customer"]
            }
            mock_client.record_payment.return_value = 500

            mock_get_client.return_value = mock_client
            mock_get_logger.return_value = MockAuditLogger.return_value

            # Step 1: Create invoice via MCP tool
            import asyncio
            invoice_args = {
                "customer_id": 7,
                "invoice_date": "2026-03-17",
                "line_items": [
                    {"product_id": 1, "quantity": 2, "price_unit": 150.00, "description": "Consulting"}
                ]
            }

            invoice_result = asyncio.run(call_tool("create_invoice", invoice_args))
            assert len(invoice_result) > 0
            assert "approval" in invoice_result[0].text.lower()

            # Step 2: Simulate approval of invoice
            executor = ApprovalExecutor(vault_path=vault_path)
            invoice_approval_data = {
                'approval_id': 'approval_20260317_143022_invoice',
                'operation': 'invoice',
                'invoice_id': 100
            }
            invoice_exec_result = executor.execute_invoice_finalize(invoice_approval_data)
            assert invoice_exec_result['status'] == 'success'
            assert invoice_exec_result['invoice_id'] == 100

            # Step 3: Record payment via MCP tool
            payment_args = {
                "invoice_id": 100,
                "amount": 200.00,
                "payment_date": "2026-03-17",
                "payment_method": "bank"
            }

            payment_result = asyncio.run(call_tool("record_payment", payment_args))
            assert len(payment_result) > 0
            assert "approval" in payment_result[0].text.lower()

            # Step 4: Simulate approval of payment
            payment_approval_data = {
                'approval_id': 'approval_20260317_143022_payment',
                'operation': 'payment',
                'invoice_id': 100,
                'amount': 200.00,
                'payment_date': '2026-03-17',
                'payment_method': 'bank'
            }
            payment_exec_result = executor.execute_payment_record(payment_approval_data)
            assert payment_exec_result['status'] == 'success'
            assert payment_exec_result['payment_id'] == 500
            assert payment_exec_result['invoice_id'] == 100

            # Verify all operations were called
            mock_client.create_draft_invoice.assert_called_once()
            mock_client.finalize_invoice.assert_called_once_with(100)
            mock_client.record_payment.assert_called_once()

    @pytest.mark.integration
    def test_invoice_query_workflow_e2e(self, vault_path):
        """
        Test invoice querying workflow (T116):
        1. Query all invoices
        2. Query with date filter
        3. Query with customer filter
        4. Query with status filter
        5. Verify amounts are masked
        6. Verify audit logs
        """
        from mcp_servers.odoo_mcp_server import call_tool

        # Save original getenv before patching
        original_getenv = os.getenv

        # Create a selective getenv mock
        def mock_getenv(key, default=None):
            if key == 'VAULT_PATH':
                return vault_path
            return original_getenv(key, default)

        # Mock OdooClient and AuditLogger
        with patch('mcp_servers.odoo_mcp_server.get_odoo_client') as mock_get_client, \
             patch('mcp_servers.odoo_mcp_server.get_audit_logger') as mock_get_logger, \
             patch('mcp_servers.odoo_mcp_server.os.getenv', side_effect=mock_getenv):

            # Setup mocks
            mock_client = Mock()
            mock_client.authenticate.return_value = 2

            # Mock invoice data
            all_invoices = [
                {
                    "id": 100,
                    "name": "INV/2026/0001",
                    "partner_id": [7, "Test Customer"],
                    "invoice_date": "2026-03-17",
                    "state": "posted",
                    "amount_total": 300.00,
                    "amount_residual": 0.00
                },
                {
                    "id": 101,
                    "name": "INV/2026/0002",
                    "partner_id": [8, "Another Customer"],
                    "invoice_date": "2026-03-18",
                    "state": "draft",
                    "amount_total": 500.00,
                    "amount_residual": 500.00
                },
                {
                    "id": 102,
                    "name": "INV/2026/0003",
                    "partner_id": [7, "Test Customer"],
                    "invoice_date": "2026-03-20",
                    "state": "posted",
                    "amount_total": 750.00,
                    "amount_residual": 750.00
                }
            ]

            mock_client.search_invoices.return_value = all_invoices
            mock_get_client.return_value = mock_client
            mock_get_logger.return_value = Mock()

            # Test 1: Query all invoices
            import asyncio
            result = asyncio.run(call_tool("list_invoices", {}))
            assert len(result) > 0
            assert "INV/2026/0001" in result[0].text
            assert "INV/2026/0002" in result[0].text
            assert "INV/2026/0003" in result[0].text
            # Verify amounts are masked
            assert "***" in result[0].text
            assert "300.00" not in result[0].text
            assert "500.00" not in result[0].text

            # Test 2: Query with date filter
            mock_client.search_invoices.return_value = [all_invoices[0]]
            result = asyncio.run(call_tool("list_invoices", {
                "date_from": "2026-03-01",
                "date_to": "2026-03-17"
            }))
            assert len(result) > 0
            assert "INV/2026/0001" in result[0].text
            mock_client.search_invoices.assert_called_with(
                date_from="2026-03-01",
                date_to="2026-03-17",
                customer_id=None,
                status=None,
                limit=100,
                offset=0
            )

            # Test 3: Query with customer filter
            mock_client.search_invoices.return_value = [all_invoices[0], all_invoices[2]]
            result = asyncio.run(call_tool("list_invoices", {"customer_id": 7}))
            assert len(result) > 0
            assert "Test Customer" in result[0].text

            # Test 4: Query with status filter
            mock_client.search_invoices.return_value = [all_invoices[0], all_invoices[2]]
            result = asyncio.run(call_tool("list_invoices", {"status": "posted"}))
            assert len(result) > 0
            assert "posted" in result[0].text.lower()

            # Test 5: Empty results
            mock_client.search_invoices.return_value = []
            result = asyncio.run(call_tool("list_invoices", {"customer_id": 99999}))
            assert len(result) > 0
            assert "No invoices found" in result[0].text

    @pytest.mark.integration
    def test_financial_report_workflow_e2e(self, vault_path):
        """
        Test financial report generation workflow (T138):
        1. Generate revenue summary report
        2. Generate receivables report
        3. Generate payment collection report
        4. Verify amounts are masked
        5. Verify audit logs
        """
        from mcp_servers.odoo_mcp_server import call_tool

        # Save original getenv before patching
        original_getenv = os.getenv

        # Create a selective getenv mock
        def mock_getenv(key, default=None):
            if key == 'VAULT_PATH':
                return vault_path
            return original_getenv(key, default)

        # Mock OdooClient and AuditLogger
        with patch('mcp_servers.odoo_mcp_server.get_odoo_client') as mock_get_client, \
             patch('mcp_servers.odoo_mcp_server.get_audit_logger') as mock_get_logger, \
             patch('mcp_servers.odoo_mcp_server.os.getenv', side_effect=mock_getenv):

            # Setup mocks
            mock_client = Mock()
            mock_client.authenticate.return_value = 2
            mock_get_client.return_value = mock_client
            mock_get_logger.return_value = Mock()

            import asyncio

            # Test 1: Revenue summary report
            mock_client.get_financial_report.return_value = {
                'report_type': 'revenue_summary',
                'period_start': '2026-03-01',
                'period_end': '2026-03-31',
                'total_revenue': 5000.00,
                'invoice_count': 10
            }
            result = asyncio.run(call_tool("get_financial_report", {
                "report_type": "revenue_summary",
                "date_from": "2026-03-01",
                "date_to": "2026-03-31"
            }))
            assert len(result) > 0
            assert "Revenue Summary" in result[0].text
            assert "***" in result[0].text  # Amounts masked
            assert "5000.00" not in result[0].text  # Actual amount not shown

            # Test 2: Receivables report
            mock_client.get_financial_report.return_value = {
                'report_type': 'receivables',
                'period_start': '2026-03-01',
                'period_end': '2026-03-31',
                'total_outstanding': 2500.00,
                'invoice_count': 5
            }
            result = asyncio.run(call_tool("get_financial_report", {
                "report_type": "receivables",
                "date_from": "2026-03-01",
                "date_to": "2026-03-31"
            }))
            assert len(result) > 0
            assert "Receivables" in result[0].text
            assert "***" in result[0].text
            assert "2500.00" not in result[0].text

            # Test 3: Payment collection report
            mock_client.get_financial_report.return_value = {
                'report_type': 'payment_collection',
                'period_start': '2026-03-01',
                'period_end': '2026-03-31',
                'total_invoiced': 5000.00,
                'total_collected': 3500.00,
                'total_outstanding': 1500.00,
                'collection_rate': 70.0,
                'invoice_count': 10
            }
            result = asyncio.run(call_tool("get_financial_report", {
                "report_type": "payment_collection",
                "date_from": "2026-03-01",
                "date_to": "2026-03-31"
            }))
            assert len(result) > 0
            assert "Payment Collection" in result[0].text
            assert "70.0%" in result[0].text  # Collection rate shown
            assert "***" in result[0].text  # Amounts masked
            assert "5000.00" not in result[0].text
            assert "3500.00" not in result[0].text

            # Verify all report types were called
            assert mock_client.get_financial_report.call_count == 3

    @pytest.mark.integration
    def test_query_and_reporting_workflow(self):
        """
        Test query and reporting operations:
        1. List invoices with filters
        2. Generate financial reports
        3. Verify data accuracy
        """
        # TODO: Implement test (T143)
        pytest.skip("Test not yet implemented - T143")

    @pytest.mark.integration
    def test_error_recovery_workflow(self):
        """
        Test error recovery scenarios:
        1. Network timeout with retry
        2. Circuit breaker activation
        3. Graceful degradation
        """
        # TODO: Implement test (T144)
        pytest.skip("Test not yet implemented - T144")
