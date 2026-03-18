"""
Unit tests for Odoo MCP Server

Tests cover:
- MCP tool registration and listing
- Tool call handling for all four tools
- Approval workflow integration
- Error handling and responses
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio
import os

# Import will work after odoo_mcp_server.py is in place
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp_servers'))


@pytest.fixture
def mock_odoo_client():
    """Fixture providing mocked OdooClient."""
    with patch('odoo_mcp_server.odoo_client') as mock_client:
        yield mock_client


# ============================================================================
# MCP Server Tests (Phase 3: create_invoice tool)
# ============================================================================

class TestMCPServer:
    """Tests for MCP server functionality."""

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test that all four tools are registered (T049)."""
        from odoo_mcp_server import list_tools

        # Call the function directly (not through the decorator)
        tools = await list_tools()

        # Verify all 4 tools are present
        tool_names = [tool.name for tool in tools]
        assert "create_invoice" in tool_names
        assert "record_payment" in tool_names
        assert "list_invoices" in tool_names
        assert "get_financial_report" in tool_names

        # Verify create_invoice tool has correct schema
        create_invoice_tool = next(t for t in tools if t.name == "create_invoice")
        assert "customer_id" in create_invoice_tool.inputSchema["properties"]
        assert "invoice_date" in create_invoice_tool.inputSchema["properties"]
        assert "line_items" in create_invoice_tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_create_invoice_tool_success(self, tmp_path):
        """Test create_invoice tool successful execution (T050)."""
        from odoo_mcp_server import call_tool

        # Mock OdooClient
        mock_client = MagicMock()
        mock_client.create_draft_invoice.return_value = 100

        # Mock AuditLogger
        mock_logger = MagicMock()

        # Set vault path to temp directory
        vault_path = str(tmp_path / "AI_Employee_Vault")
        os.makedirs(f"{vault_path}/Pending_Approval", exist_ok=True)

        with patch('odoo_mcp_server.get_odoo_client', return_value=mock_client), \
             patch('odoo_mcp_server.get_audit_logger', return_value=mock_logger), \
             patch('odoo_mcp_server.os.getenv', return_value=vault_path):

            arguments = {
                "customer_id": 7,
                "invoice_date": "2026-03-17",
                "line_items": [
                    {"product_id": 1, "quantity": 2, "price_unit": 150.00, "description": "Consulting"}
                ]
            }

            result = await call_tool("create_invoice", arguments)

            # Verify response
            assert len(result) > 0
            assert "approval" in result[0].text.lower()
            assert "draft invoice created" in result[0].text.lower()

            # Verify client was called
            mock_client.create_draft_invoice.assert_called_once()

            # Verify audit log was called
            mock_logger.log_action.assert_called()

    @pytest.mark.asyncio
    async def test_create_invoice_tool_validation_errors(self):
        """Test create_invoice tool with validation errors (T051)."""
        from odoo_mcp_server import call_tool

        # Mock OdooClient with validation error
        mock_client = MagicMock()
        mock_client.create_draft_invoice.side_effect = ValueError("Customer with ID 99999 not found")

        # Mock AuditLogger
        mock_logger = MagicMock()

        with patch('odoo_mcp_server.get_odoo_client', return_value=mock_client), \
             patch('odoo_mcp_server.get_audit_logger', return_value=mock_logger):

            arguments = {
                "customer_id": 99999,
                "invoice_date": "2026-03-17",
                "line_items": [{"product_id": 1, "quantity": 1, "price_unit": 100.00}]
            }

            result = await call_tool("create_invoice", arguments)

            # Verify error response
            assert len(result) > 0
            assert "validation error" in result[0].text.lower() or "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_create_invoice_tool_approval_file_created(self, tmp_path):
        """Test that approval file is created (T052)."""
        from odoo_mcp_server import call_tool

        # Mock OdooClient
        mock_client = MagicMock()
        mock_client.create_draft_invoice.return_value = 100

        # Mock AuditLogger
        mock_logger = MagicMock()

        vault_path = str(tmp_path / "AI_Employee_Vault")
        os.makedirs(f"{vault_path}/Pending_Approval", exist_ok=True)

        with patch('odoo_mcp_server.get_odoo_client', return_value=mock_client), \
             patch('odoo_mcp_server.get_audit_logger', return_value=mock_logger), \
             patch('odoo_mcp_server.os.getenv', return_value=vault_path):

            arguments = {
                "customer_id": 7,
                "invoice_date": "2026-03-17",
                "line_items": [{"product_id": 1, "quantity": 1, "price_unit": 100.00}]
            }

            await call_tool("create_invoice", arguments)

            # Verify approval file was created
            approval_files = list((tmp_path / "AI_Employee_Vault" / "Pending_Approval").glob("APPROVAL_invoice_*.md"))
            assert len(approval_files) > 0

    @pytest.mark.asyncio
    async def test_record_payment_tool_success(self, tmp_path):
        """Test successful payment recording via MCP tool (T079)."""
        from mcp_servers.odoo_mcp_server import call_tool
        
        # Mock OdooClient and AuditLogger
        with patch('mcp_servers.odoo_mcp_server.OdooClient') as MockOdooClient, \
             patch('mcp_servers.odoo_mcp_server.AuditLogger') as MockAuditLogger:
            
            mock_client = MockOdooClient.return_value
            mock_client.authenticate.return_value = 2
            mock_client.get_invoice_details.return_value = {
                'id': 100,
                'state': 'posted',
                'amount_residual': 200.00,
                'name': 'INV/2026/0001'
            }

            # Override vault path
            import mcp_servers.odoo_mcp_server as mcp_module
            original_vault = mcp_module.VAULT_PATH
            mcp_module.VAULT_PATH = str(tmp_path / "AI_Employee_Vault")
            (tmp_path / "AI_Employee_Vault" / "Pending_Approval").mkdir(parents=True)

            try:
                payment_data = {
                    "invoice_id": 100,
                    "amount": 200.00,
                    "payment_date": "2026-03-17",
                    "payment_method": "bank"
                }

                result = await call_tool("record_payment", payment_data)

                # Verify approval required response
                assert result[0].text is not None
                assert "Approval required" in result[0].text or "approval" in result[0].text.lower()
                
            finally:
                mcp_module.VAULT_PATH = original_vault

    @pytest.mark.asyncio
    async def test_record_payment_tool_validation_errors(self, tmp_path):
        """Test payment recording validation errors (T080)."""
        from mcp_servers.odoo_mcp_server import call_tool
        
        with patch('mcp_servers.odoo_mcp_server.OdooClient') as MockOdooClient, \
             patch('mcp_servers.odoo_mcp_server.AuditLogger') as MockAuditLogger:
            
            import mcp_servers.odoo_mcp_server as mcp_module
            original_vault = mcp_module.VAULT_PATH
            mcp_module.VAULT_PATH = str(tmp_path / "AI_Employee_Vault")
            
            try:
                # Test missing required fields
                invalid_data = {
                    "invoice_id": 100
                    # Missing amount, payment_date, payment_method
                }

                result = await call_tool("record_payment", invalid_data)
                assert result[0].text is not None
                assert "error" in result[0].text.lower() or "required" in result[0].text.lower()
                
            finally:
                mcp_module.VAULT_PATH = original_vault

    @pytest.mark.asyncio
    async def test_record_payment_tool_approval_file_created(self, tmp_path):
        """Test that payment recording creates approval file (T081)."""
        from mcp_servers.odoo_mcp_server import call_tool
        
        with patch('mcp_servers.odoo_mcp_server.OdooClient') as MockOdooClient, \
             patch('mcp_servers.odoo_mcp_server.AuditLogger') as MockAuditLogger:
            
            mock_client = MockOdooClient.return_value
            mock_client.authenticate.return_value = 2
            mock_client.get_invoice_details.return_value = {
                'id': 100,
                'state': 'posted',
                'amount_residual': 200.00,
                'name': 'INV/2026/0001'
            }

            import mcp_servers.odoo_mcp_server as mcp_module
            original_vault = mcp_module.VAULT_PATH
            mcp_module.VAULT_PATH = str(tmp_path / "AI_Employee_Vault")
            (tmp_path / "AI_Employee_Vault" / "Pending_Approval").mkdir(parents=True)

            try:
                payment_data = {
                    "invoice_id": 100,
                    "amount": 200.00,
                    "payment_date": "2026-03-17",
                    "payment_method": "bank"
                }

                result = await call_tool("record_payment", payment_data)

                # Verify approval file was created
                approval_files = list((tmp_path / "AI_Employee_Vault" / "Pending_Approval").glob("APPROVAL_payment_*.md"))
                assert len(approval_files) > 0

            finally:
                mcp_module.VAULT_PATH = original_vault

    @pytest.mark.asyncio
    async def test_list_invoices_tool_success(self, tmp_path):
        """Test successful invoice listing via MCP tool (T107)."""
        import mcp_servers.odoo_mcp_server as mcp_module
        from mcp_servers.odoo_mcp_server import call_tool

        original_vault = mcp_module.VAULT_PATH
        mcp_module.VAULT_PATH = str(tmp_path / "AI_Employee_Vault")

        try:
            with patch('mcp_servers.odoo_mcp_server.get_odoo_client') as mock_get_client, \
                 patch('mcp_servers.odoo_mcp_server.get_audit_logger') as mock_get_logger:

                mock_client = Mock()
                mock_client.authenticate.return_value = 2
                mock_client.search_invoices.return_value = [
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
                    }
                ]

                mock_get_client.return_value = mock_client
                mock_get_logger.return_value = Mock()

                result = await call_tool("list_invoices", {})

                assert len(result) > 0
                assert "INV/2026/0001" in result[0].text
                assert "INV/2026/0002" in result[0].text
                mock_client.search_invoices.assert_called_once()

        finally:
            mcp_module.VAULT_PATH = original_vault

    @pytest.mark.asyncio
    async def test_list_invoices_tool_with_filters(self, tmp_path):
        """Test invoice listing with filters (T108)."""
        import mcp_servers.odoo_mcp_server as mcp_module
        from mcp_servers.odoo_mcp_server import call_tool

        original_vault = mcp_module.VAULT_PATH
        mcp_module.VAULT_PATH = str(tmp_path / "AI_Employee_Vault")

        try:
            with patch('mcp_servers.odoo_mcp_server.get_odoo_client') as mock_get_client, \
                 patch('mcp_servers.odoo_mcp_server.get_audit_logger') as mock_get_logger:

                mock_client = Mock()
                mock_client.authenticate.return_value = 2
                mock_client.search_invoices.return_value = [
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

                mock_get_client.return_value = mock_client
                mock_get_logger.return_value = Mock()

                filters = {
                    "date_from": "2026-03-01",
                    "date_to": "2026-03-31",
                    "customer_id": 7,
                    "status": "posted"
                }

                result = await call_tool("list_invoices", filters)

                assert len(result) > 0
                mock_client.search_invoices.assert_called_once_with(
                    date_from="2026-03-01",
                    date_to="2026-03-31",
                    customer_id=7,
                    status="posted",
                    limit=100,
                    offset=0
                )

        finally:
            mcp_module.VAULT_PATH = original_vault

    @pytest.mark.asyncio
    async def test_list_invoices_tool_amount_masking(self, tmp_path):
        """Test that amounts are masked in list_invoices response (T109)."""
        import mcp_servers.odoo_mcp_server as mcp_module
        from mcp_servers.odoo_mcp_server import call_tool

        original_vault = mcp_module.VAULT_PATH
        mcp_module.VAULT_PATH = str(tmp_path / "AI_Employee_Vault")

        try:
            with patch('mcp_servers.odoo_mcp_server.get_odoo_client') as mock_get_client, \
                 patch('mcp_servers.odoo_mcp_server.get_audit_logger') as mock_get_logger:

                mock_client = Mock()
                mock_client.authenticate.return_value = 2
                mock_client.search_invoices.return_value = [
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

                mock_get_client.return_value = mock_client
                mock_get_logger.return_value = Mock()

                result = await call_tool("list_invoices", {})

                assert len(result) > 0
                # Verify amounts are masked with ***
                assert "***" in result[0].text
                # Verify actual amounts are NOT in response
                assert "300.00" not in result[0].text
                assert "0.00" not in result[0].text

        finally:
            mcp_module.VAULT_PATH = original_vault

    @pytest.mark.asyncio
    async def test_get_financial_report_tool_success(self, tmp_path):
        """Test successful financial report generation via MCP tool (T129)."""
        import mcp_servers.odoo_mcp_server as mcp_module
        from mcp_servers.odoo_mcp_server import call_tool

        original_vault = mcp_module.VAULT_PATH
        mcp_module.VAULT_PATH = str(tmp_path / "AI_Employee_Vault")

        try:
            with patch('mcp_servers.odoo_mcp_server.get_odoo_client') as mock_get_client, \
                 patch('mcp_servers.odoo_mcp_server.get_audit_logger') as mock_get_logger:

                mock_client = Mock()
                mock_client.authenticate.return_value = 2
                mock_client.get_financial_report.return_value = {
                    'report_type': 'revenue_summary',
                    'period_start': '2026-03-01',
                    'period_end': '2026-03-31',
                    'total_revenue': 1500.00,
                    'invoice_count': 5
                }

                mock_get_client.return_value = mock_client
                mock_get_logger.return_value = Mock()

                report_args = {
                    "report_type": "revenue_summary",
                    "date_from": "2026-03-01",
                    "date_to": "2026-03-31"
                }

                result = await call_tool("get_financial_report", report_args)

                assert len(result) > 0
                assert "Revenue Summary" in result[0].text
                mock_client.get_financial_report.assert_called_once()

        finally:
            mcp_module.VAULT_PATH = original_vault

    @pytest.mark.asyncio
    async def test_get_financial_report_tool_all_types(self, tmp_path):
        """Test all financial report types (T130)."""
        import mcp_servers.odoo_mcp_server as mcp_module
        from mcp_servers.odoo_mcp_server import call_tool

        original_vault = mcp_module.VAULT_PATH
        mcp_module.VAULT_PATH = str(tmp_path / "AI_Employee_Vault")

        try:
            with patch('mcp_servers.odoo_mcp_server.get_odoo_client') as mock_get_client, \
                 patch('mcp_servers.odoo_mcp_server.get_audit_logger') as mock_get_logger:

                mock_client = Mock()
                mock_client.authenticate.return_value = 2
                mock_get_client.return_value = mock_client
                mock_get_logger.return_value = Mock()

                # Test revenue_summary
                mock_client.get_financial_report.return_value = {
                    'report_type': 'revenue_summary',
                    'period_start': '2026-03-01',
                    'period_end': '2026-03-31',
                    'total_revenue': 1500.00,
                    'invoice_count': 5
                }
                result = await call_tool("get_financial_report", {
                    "report_type": "revenue_summary",
                    "date_from": "2026-03-01",
                    "date_to": "2026-03-31"
                })
                assert "Revenue Summary" in result[0].text

                # Test receivables
                mock_client.get_financial_report.return_value = {
                    'report_type': 'receivables',
                    'period_start': '2026-03-01',
                    'period_end': '2026-03-31',
                    'total_outstanding': 800.00,
                    'invoice_count': 3
                }
                result = await call_tool("get_financial_report", {
                    "report_type": "receivables",
                    "date_from": "2026-03-01",
                    "date_to": "2026-03-31"
                })
                assert "Receivables" in result[0].text

                # Test payment_collection
                mock_client.get_financial_report.return_value = {
                    'report_type': 'payment_collection',
                    'period_start': '2026-03-01',
                    'period_end': '2026-03-31',
                    'total_invoiced': 1000.00,
                    'total_collected': 600.00,
                    'total_outstanding': 400.00,
                    'collection_rate': 60.0,
                    'invoice_count': 4
                }
                result = await call_tool("get_financial_report", {
                    "report_type": "payment_collection",
                    "date_from": "2026-03-01",
                    "date_to": "2026-03-31"
                })
                assert "Payment Collection" in result[0].text

        finally:
            mcp_module.VAULT_PATH = original_vault

    @pytest.mark.asyncio
    async def test_get_financial_report_tool_amount_masking(self, tmp_path):
        """Test that amounts are masked in financial report response (T131)."""
        import mcp_servers.odoo_mcp_server as mcp_module
        from mcp_servers.odoo_mcp_server import call_tool

        original_vault = mcp_module.VAULT_PATH
        mcp_module.VAULT_PATH = str(tmp_path / "AI_Employee_Vault")

        try:
            with patch('mcp_servers.odoo_mcp_server.get_odoo_client') as mock_get_client, \
                 patch('mcp_servers.odoo_mcp_server.get_audit_logger') as mock_get_logger:

                mock_client = Mock()
                mock_client.authenticate.return_value = 2
                mock_client.get_financial_report.return_value = {
                    'report_type': 'revenue_summary',
                    'period_start': '2026-03-01',
                    'period_end': '2026-03-31',
                    'total_revenue': 1500.00,
                    'invoice_count': 5
                }

                mock_get_client.return_value = mock_client
                mock_get_logger.return_value = Mock()

                result = await call_tool("get_financial_report", {
                    "report_type": "revenue_summary",
                    "date_from": "2026-03-01",
                    "date_to": "2026-03-31"
                })

                assert len(result) > 0
                # Verify amounts are masked with ***
                assert "***" in result[0].text
                # Verify actual amounts are NOT in response
                assert "1500.00" not in result[0].text

        finally:
            mcp_module.VAULT_PATH = original_vault
