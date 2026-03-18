"""
Odoo MCP Server for AI Employee System

This MCP server exposes Odoo accounting operations as tools for Claude Code.
It provides four main tools:
1. create_invoice - Create customer invoices (requires approval)
2. record_payment - Record payments against invoices (requires approval)
3. list_invoices - Query invoices with filters (read-only, no approval)
4. get_financial_report - Retrieve financial summaries (read-only, no approval)

All write operations integrate with the approval workflow system.
All operations are logged via the audit logging system.
Error recovery decorators provide resilience against transient failures.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.audit_logger import AuditLogger

from odoo_client import (
    OdooClient,
    mask_financial_data,
    generate_approval_id,
    create_approval_request_file
)

# Initialize MCP server
app = Server("odoo-mcp-server")

# Vault path for approval workflow (can be overridden in tests)
VAULT_PATH = os.getenv("VAULT_PATH", "./AI_Employee_Vault")

# Initialize Odoo client (lazy initialization)
odoo_client = None

# Audit logger (initialized on first use)
_audit_logger = None


def get_audit_logger():
    """Get or create AuditLogger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def get_odoo_client():
    """Get or create OdooClient instance."""
    global odoo_client
    if odoo_client is None:
        odoo_client = OdooClient()
    return odoo_client


@app.list_tools()
async def list_tools() -> List[Tool]:
    """
    List all available Odoo MCP tools.

    Returns:
        List of Tool definitions for MCP protocol
    """
    return [
        Tool(
            name="create_invoice",
            description="Create a customer invoice in Odoo (requires approval)",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "Odoo customer ID (res.partner)"
                    },
                    "invoice_date": {
                        "type": "string",
                        "description": "Invoice date (YYYY-MM-DD format)"
                    },
                    "line_items": {
                        "type": "array",
                        "description": "Invoice line items",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "integer"},
                                "quantity": {"type": "number"},
                                "price_unit": {"type": "number"},
                                "description": {"type": "string"}
                            },
                            "required": ["product_id", "quantity", "price_unit"]
                        }
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Payment due date (YYYY-MM-DD format, optional)"
                    }
                },
                "required": ["customer_id", "invoice_date", "line_items"]
            }
        ),
        Tool(
            name="record_payment",
            description="Record a payment against an invoice (requires approval)",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {
                        "type": "integer",
                        "description": "Odoo invoice ID (account.move)"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Payment amount"
                    },
                    "payment_date": {
                        "type": "string",
                        "description": "Payment date (YYYY-MM-DD format)"
                    },
                    "payment_method": {
                        "type": "string",
                        "description": "Payment method (bank, cash, check, etc.)"
                    }
                },
                "required": ["invoice_id", "amount", "payment_date", "payment_method"]
            }
        ),
        Tool(
            name="list_invoices",
            description="Query invoices with filters (read-only, no approval required)",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Start date filter (YYYY-MM-DD format, optional)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date filter (YYYY-MM-DD format, optional)"
                    },
                    "customer_id": {
                        "type": "integer",
                        "description": "Filter by customer ID (optional)"
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by status: draft, posted, paid (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)"
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Pagination offset (default: 0)"
                    }
                }
            }
        ),
        Tool(
            name="get_financial_report",
            description="Retrieve financial summary reports (read-only, no approval required)",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "description": "Report type: revenue_summary, receivables, payment_collection",
                        "enum": ["revenue_summary", "receivables", "payment_collection"]
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD format)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD format)"
                    }
                },
                "required": ["report_type", "date_from", "date_to"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Handle MCP tool calls.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of TextContent responses
    """
    audit_logger = get_audit_logger()
    client = get_odoo_client()

    try:
        if name == "create_invoice":
            # Generate approval ID for idempotency
            approval_id = generate_approval_id("invoice")

            # Extract arguments
            customer_id = arguments["customer_id"]
            invoice_date = arguments["invoice_date"]
            line_items = arguments["line_items"]
            due_date = arguments.get("due_date")

            # Create draft invoice
            invoice_id = client.create_draft_invoice(
                customer_id=customer_id,
                invoice_date=invoice_date,
                line_items=line_items,
                approval_id=approval_id,
                due_date=due_date
            )

            # Create approval request file
            vault_path = os.getenv("VAULT_PATH", "./AI_Employee_Vault")
            approval_file = create_approval_request_file(
                operation_type="invoice",
                data={
                    "invoice_id": invoice_id,
                    "customer_id": customer_id,
                    "invoice_date": invoice_date,
                    "line_items": line_items,
                    "due_date": due_date
                },
                approval_id=approval_id,
                vault_path=vault_path
            )

            # Log action with masked amounts
            masked_data = mask_financial_data({
                "invoice_id": invoice_id,
                "customer_id": customer_id,
                "line_items": line_items
            })
            audit_logger.log_action(
                action="create_invoice_draft",
                details=masked_data,
                status="pending_approval"
            )

            return [TextContent(
                type="text",
                text=f"✅ Draft invoice created (ID: {invoice_id})\n\n"
                     f"📋 Approval required: {approval_file}\n\n"
                     f"The invoice is in draft state and requires approval before finalization.\n"
                     f"Move the approval file to the Approved/ directory to finalize the invoice."
            )]

        elif name == "record_payment":
            # Generate approval ID for idempotency
            approval_id = generate_approval_id("payment")

            # Extract arguments
            invoice_id = arguments["invoice_id"]
            amount = arguments["amount"]
            payment_date = arguments["payment_date"]
            payment_method = arguments["payment_method"]

            # Validate payment can be made (get invoice details)
            invoice = client.get_invoice_details(invoice_id)

            # Validate invoice is posted
            if invoice['state'] != 'posted':
                raise ValueError(f"Invoice {invoice_id} is not posted (current state: {invoice['state']})")

            # Validate amount doesn't exceed outstanding balance
            if amount > invoice['amount_residual']:
                raise ValueError(
                    f"Payment amount {amount} exceeds outstanding balance {invoice['amount_residual']}"
                )

            # Create approval request file
            approval_file = create_approval_request_file(
                operation_type="payment",
                data={
                    "invoice_id": invoice_id,
                    "amount": amount,
                    "payment_date": payment_date,
                    "payment_method": payment_method,
                    "invoice_name": invoice.get('name', f'Invoice {invoice_id}'),
                    "outstanding_balance": invoice['amount_residual']
                },
                approval_id=approval_id,
                vault_path=VAULT_PATH
            )

            # Log action with masked amounts
            masked_data = mask_financial_data({
                "invoice_id": invoice_id,
                "amount": amount,
                "payment_date": payment_date,
                "payment_method": payment_method
            })
            audit_logger.log_action(
                action="record_payment_request",
                details=masked_data,
                status="pending_approval"
            )

            return [TextContent(
                type="text",
                text=f"✅ Payment request created for invoice {invoice_id}\n\n"
                     f"📋 Approval required: {approval_file}\n\n"
                     f"The payment will be recorded in Odoo after approval.\n"
                     f"Move the approval file to the Approved/ directory to record the payment."
            )]

        elif name == "list_invoices":
            # Extract filter arguments (all optional)
            date_from = arguments.get("date_from")
            date_to = arguments.get("date_to")
            customer_id = arguments.get("customer_id")
            status = arguments.get("status")
            limit = arguments.get("limit", 100)
            offset = arguments.get("offset", 0)

            # Search invoices with filters
            invoices = client.search_invoices(
                date_from=date_from,
                date_to=date_to,
                customer_id=customer_id,
                status=status,
                limit=limit,
                offset=offset
            )

            # Mask financial amounts in response (SR-009 requirement)
            masked_invoices = [mask_financial_data(inv) for inv in invoices]

            # Log action to audit log
            audit_logger.log_action(
                action="list_invoices",
                details={
                    "filters": {
                        "date_from": date_from,
                        "date_to": date_to,
                        "customer_id": customer_id,
                        "status": status,
                        "limit": limit,
                        "offset": offset
                    },
                    "result_count": len(invoices)
                },
                status="success"
            )

            # Format response
            if not invoices:
                return [TextContent(
                    type="text",
                    text="No invoices found matching the specified filters."
                )]

            # Build formatted invoice list with masked amounts
            invoice_lines = []
            for inv in masked_invoices:
                partner_name = inv['partner_id'][1] if isinstance(inv['partner_id'], list) else "Unknown"
                invoice_lines.append(
                    f"- **{inv['name']}** | Customer: {partner_name} | "
                    f"Date: {inv['invoice_date']} | Status: {inv['state']} | "
                    f"Total: {inv['amount_total']} | Outstanding: {inv['amount_residual']}"
                )

            invoice_list = "\n".join(invoice_lines)

            return [TextContent(
                type="text",
                text=f"📋 Found {len(invoices)} invoice(s)\n\n{invoice_list}\n\n"
                     f"**Note**: Financial amounts are masked (***) for security."
            )]

        elif name == "get_financial_report":
            # Extract arguments
            report_type = arguments["report_type"]
            date_from = arguments["date_from"]
            date_to = arguments["date_to"]

            # Generate financial report
            report = client.get_financial_report(
                report_type=report_type,
                date_from=date_from,
                date_to=date_to
            )

            # Mask financial amounts in response (SR-009 requirement)
            masked_report = mask_financial_data(report)

            # Log action to audit log
            audit_logger.log_action(
                action="get_financial_report",
                details={
                    "report_type": report_type,
                    "date_from": date_from,
                    "date_to": date_to
                },
                status="success"
            )

            # Format response based on report type
            if report_type == "revenue_summary":
                response_text = (
                    f"📊 **Revenue Summary Report**\n\n"
                    f"**Period:** {report['period_start']} to {report['period_end']}\n"
                    f"**Total Revenue:** {masked_report['total_revenue']}\n"
                    f"**Invoice Count:** {report['invoice_count']}\n\n"
                    f"**Note**: Financial amounts are masked (***) for security."
                )
            elif report_type == "receivables":
                response_text = (
                    f"📊 **Receivables Report**\n\n"
                    f"**Period:** {report['period_start']} to {report['period_end']}\n"
                    f"**Total Outstanding:** {masked_report['total_outstanding']}\n"
                    f"**Invoice Count:** {report['invoice_count']}\n\n"
                    f"**Note**: Financial amounts are masked (***) for security."
                )
            elif report_type == "payment_collection":
                response_text = (
                    f"📊 **Payment Collection Report**\n\n"
                    f"**Period:** {report['period_start']} to {report['period_end']}\n"
                    f"**Total Invoiced:** {masked_report['total_invoiced']}\n"
                    f"**Total Collected:** {masked_report['total_collected']}\n"
                    f"**Total Outstanding:** {masked_report['total_outstanding']}\n"
                    f"**Collection Rate:** {report['collection_rate']}%\n"
                    f"**Invoice Count:** {report['invoice_count']}\n\n"
                    f"**Note**: Financial amounts are masked (***) for security."
                )
            else:
                response_text = f"Report generated: {masked_report}"

            return [TextContent(
                type="text",
                text=response_text
            )]

        else:
            return [TextContent(
                type="text",
                text=f"❌ Unknown tool: {name}"
            )]

    except ValueError as e:
        # Validation errors
        audit_logger.log_action(
            action=f"{name}_failed",
            details={"error": str(e), "arguments": mask_financial_data(arguments)},
            status="error"
        )
        return [TextContent(
            type="text",
            text=f"❌ Validation error: {str(e)}"
        )]

    except Exception as e:
        # Unexpected errors
        audit_logger.log_action(
            action=f"{name}_failed",
            details={"error": str(e), "arguments": mask_financial_data(arguments)},
            status="error"
        )
        return [TextContent(
            type="text",
            text=f"❌ Error: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
