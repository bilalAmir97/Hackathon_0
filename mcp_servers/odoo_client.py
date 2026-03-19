"""
Odoo JSON-RPC Client for AI Employee System

This module provides a client library for interacting with Odoo 17 ERP system
via XML-RPC protocol. It handles authentication, session management, and provides
methods for invoice and payment operations.

Architecture:
- Uses xmlrpc.client for RPC communication
- Integrates with error recovery decorators (@with_retry, @with_circuit_breaker)
- Implements idempotency via approval_id tracking
- Masks financial data in audit logs per SR-009 requirement
"""

import os
import sys
import xmlrpc.client
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from pathlib import Path

# Add scripts directory to path for error recovery imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from error_recovery.decorators import with_retry, with_circuit_breaker

# Load environment variables
load_dotenv()


class OdooClient:
    """
    Client for interacting with Odoo ERP system via XML-RPC.

    Handles authentication, session management, and provides methods for:
    - Creating customer invoices
    - Recording payments
    - Querying invoices
    - Generating financial reports

    All financial operations require approval workflow integration.
    """

    def __init__(self):
        """Initialize Odoo client with configuration from environment variables."""
        self.url = os.getenv("ODOO_URL", "http://localhost:8069")
        self.db = os.getenv("ODOO_DB", "odoo")
        self.username = os.getenv("ODOO_USERNAME", "admin")
        self.password = os.getenv("ODOO_PASSWORD", "admin")

        # Session state
        self.uid: Optional[int] = None
        self.common: Optional[xmlrpc.client.ServerProxy] = None
        self.models: Optional[xmlrpc.client.ServerProxy] = None

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(service_name="odoo_auth")
    def authenticate(self) -> int:
        """
        Authenticate with Odoo and establish session.

        Returns:
            int: User ID (uid) for authenticated session

        Raises:
            Exception: If authentication fails
        """
        # Initialize XML-RPC connections (allow_none=True to handle None returns)
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common', allow_none=True)
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object', allow_none=True)

        # Authenticate
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})

        if not self.uid:
            raise Exception("Authentication failed: Invalid credentials")

        return self.uid

    def _ensure_authenticated(self) -> None:
        """
        Ensure client is authenticated, re-authenticate if needed.

        This helper method checks if a valid session exists and
        re-authenticates if the session has expired.
        """
        if not self.uid or not self.common or not self.models:
            self.authenticate()

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(service_name="odoo_invoice")
    def create_draft_invoice(
        self,
        customer_id: int,
        invoice_date: str,
        line_items: List[Dict[str, Any]],
        approval_id: str,
        due_date: Optional[str] = None
    ) -> int:
        """
        Create a draft invoice in Odoo.

        Args:
            customer_id: Odoo customer ID (res.partner)
            invoice_date: Invoice date (YYYY-MM-DD format)
            line_items: List of line items with product_id, quantity, price_unit, description
            approval_id: Unique approval ID for idempotency tracking
            due_date: Optional payment due date (YYYY-MM-DD format)

        Returns:
            int: Created invoice ID (account.move)

        Raises:
            ValueError: If customer or products are invalid
        """
        self._ensure_authenticated()

        # Check idempotency: search for existing invoice with this approval_id
        existing_invoices = self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.move', 'search_read',
            [[['ref', '=', approval_id], ['move_type', '=', 'out_invoice']]],
            {'fields': ['id'], 'limit': 1}
        )

        if existing_invoices:
            # Invoice already exists, return existing ID
            return existing_invoices[0]['id']

        # Validate customer exists
        customer = self.models.execute_kw(
            self.db, self.uid, self.password,
            'res.partner', 'search_read',
            [[['id', '=', customer_id]]],
            {'fields': ['id', 'name'], 'limit': 1}
        )

        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found")

        # Validate all products exist
        for item in line_items:
            product = self.models.execute_kw(
                self.db, self.uid, self.password,
                'product.product', 'search_read',
                [[['id', '=', item['product_id']]]],
                {'fields': ['id', 'name'], 'limit': 1}
            )

            if not product:
                raise ValueError(f"Product with ID {item['product_id']} not found")

        # Prepare invoice line items
        invoice_lines = []
        for item in line_items:
            line_vals = {
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'price_unit': item['price_unit'],
                'name': item.get('description', '')
            }
            invoice_lines.append((0, 0, line_vals))

        # Prepare invoice data
        invoice_vals = {
            'partner_id': customer_id,
            'move_type': 'out_invoice',
            'invoice_date': invoice_date,
            'ref': approval_id,  # Store approval_id for idempotency
            'invoice_line_ids': invoice_lines
        }

        if due_date:
            invoice_vals['invoice_date_due'] = due_date

        # Create invoice
        invoice_id = self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.move', 'create',
            [invoice_vals]
        )

        return invoice_id

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(service_name="odoo_invoice")
    def finalize_invoice(self, invoice_id: int) -> bool:
        """
        Finalize (post) a draft invoice in Odoo.

        Args:
            invoice_id: Invoice ID to finalize

        Returns:
            bool: True if successful

        Raises:
            ValueError: If invoice not found or already posted
        """
        self._ensure_authenticated()

        # Check if invoice exists and is in draft state
        invoice = self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.move', 'search_read',
            [[['id', '=', invoice_id]]],
            {'fields': ['id', 'state'], 'limit': 1}
        )

        if not invoice:
            raise ValueError(f"Invoice with ID {invoice_id} not found")

        if invoice[0]['state'] == 'posted':
            raise ValueError(f"Invoice {invoice_id} is already posted")

        # Post the invoice
        self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.move', 'action_post',
            [[invoice_id]]
        )

        return True

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(service_name="odoo_invoice")
    def get_invoice_details(self, invoice_id: int) -> Dict[str, Any]:
        """Get invoice details from Odoo.

        Args:
            invoice_id: Odoo invoice ID

        Returns:
            Dict with invoice details (id, state, amount_residual, etc.)

        Raises:
            ValueError: If invoice not found
        """
        self._ensure_authenticated()

        # Search for invoice
        invoices = self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.move', 'search_read',
            [[['id', '=', invoice_id], ['move_type', '=', 'out_invoice']]],
            {'fields': ['id', 'state', 'amount_residual', 'amount_total', 'partner_id', 'name']}
        )

        if not invoices:
            raise ValueError(f"Invoice with ID {invoice_id} not found")

        return invoices[0]

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(service_name="odoo_payment")
    def record_payment(
        self,
        invoice_id: int,
        amount: float,
        payment_date: str,
        payment_method: str,
        approval_id: str
    ) -> int:
        """Record payment for an invoice in Odoo.

        Args:
            invoice_id: Odoo invoice ID
            amount: Payment amount
            payment_date: Payment date (YYYY-MM-DD)
            payment_method: Payment method (bank, cash, etc.)
            approval_id: Unique approval ID for idempotency

        Returns:
            Payment ID

        Raises:
            ValueError: If invoice not found, not posted, or amount exceeds balance
        """
        self._ensure_authenticated()

        # Step 1: Get invoice details and validate
        invoice = self.get_invoice_details(invoice_id)

        # Validate invoice is posted
        if invoice['state'] != 'posted':
            raise ValueError(f"Invoice {invoice_id} is not posted (current state: {invoice['state']})")

        # Validate amount doesn't exceed outstanding balance
        if amount > invoice['amount_residual']:
            raise ValueError(
                f"Payment amount {amount} exceeds outstanding balance {invoice['amount_residual']}"
            )

        # Step 2: Check for existing payment (idempotency)
        existing_payments = self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.payment', 'search_read',
            [[['ref', '=', approval_id]]],
            {'fields': ['id'], 'limit': 1}
        )

        if existing_payments:
            # Payment already exists, return existing ID
            return existing_payments[0]['id']

        # Step 3: Create payment using payment register wizard (Odoo 17 best practice)
        # This approach automatically posts and reconciles the payment
        wizard_vals = {
            'payment_date': payment_date,
            'amount': amount,
            'journal_id': 6,  # Bank journal (configured in Odoo)
            'payment_method_line_id': 1,  # Manual payment method
        }

        # Create wizard in context of the invoice
        wizard_id = self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.payment.register', 'create',
            [wizard_vals],
            {'context': {'active_model': 'account.move', 'active_ids': [invoice_id]}}
        )

        # Execute the wizard to create and post the payment
        result = self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.payment.register', 'action_create_payments',
            [[wizard_id]]
        )

        # Get the created payment ID from the result
        # The wizard returns a dict with payment IDs
        if isinstance(result, dict) and 'res_id' in result:
            payment_id = result['res_id']
        else:
            # Fallback: search for the payment by ref
            payments = self.models.execute_kw(
                self.db, self.uid, self.password,
                'account.payment', 'search',
                [[['ref', '=', approval_id]]],
                {'limit': 1}
            )
            payment_id = payments[0] if payments else None

        if not payment_id:
            raise Exception("Failed to retrieve payment ID after creation")

        # Update payment ref for idempotency tracking
        self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.payment', 'write',
            [[payment_id], {'ref': approval_id}]
        )

        return payment_id

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(service_name="odoo_invoice_query")
    def search_invoices(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        customer_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for invoices with optional filters.

        Args:
            date_from: Start date for filtering (YYYY-MM-DD format)
            date_to: End date for filtering (YYYY-MM-DD format)
            customer_id: Filter by customer/partner ID
            status: Filter by invoice state (draft, posted, cancel)
            limit: Maximum number of results to return (default: 100)
            offset: Number of results to skip (default: 0)

        Returns:
            List of invoice dictionaries with fields:
            - id, name, partner_id, invoice_date, state,
              amount_total, amount_residual

        Example:
            >>> client.search_invoices(status="posted", limit=10)
            [{"id": 100, "name": "INV/2026/0001", ...}]
        """
        # Build Odoo domain filters
        domain = [('move_type', '=', 'out_invoice')]  # Only customer invoices

        if date_from:
            domain.append(('invoice_date', '>=', date_from))

        if date_to:
            domain.append(('invoice_date', '<=', date_to))

        if customer_id:
            domain.append(('partner_id', '=', customer_id))

        if status:
            domain.append(('state', '=', status))

        # Fields to retrieve
        fields = [
            'id', 'name', 'partner_id', 'invoice_date',
            'state', 'amount_total', 'amount_residual'
        ]

        # Search invoices with pagination
        invoices = self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.move', 'search_read',
            [domain],
            {
                'fields': fields,
                'limit': limit,
                'offset': offset,
                'order': 'invoice_date desc, id desc'
            }
        )

        return invoices

    def list_invoices(
        self,
        filters: Optional[List] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List invoices with optional Odoo domain filters.

        This is a convenience wrapper around search_invoices that accepts
        Odoo domain filters directly for more advanced queries.

        Args:
            filters: Optional Odoo domain filters (e.g., [['state', '=', 'posted']])
            limit: Maximum number of results to return (default: 100)
            offset: Number of results to skip (default: 0)

        Returns:
            List of invoice dictionaries

        Example:
            >>> client.list_invoices(filters=[['state', '=', 'posted']], limit=10)
            [{"id": 100, "name": "INV/2026/0001", ...}]
        """
        # If no filters provided, just return all invoices
        if not filters:
            return self.search_invoices(limit=limit, offset=offset)

        # Parse common filter patterns and convert to search_invoices parameters
        kwargs = {'limit': limit, 'offset': offset}

        for filter_item in filters:
            if len(filter_item) == 3:
                field, operator, value = filter_item

                if field == 'invoice_date' and operator == '>=':
                    kwargs['date_from'] = value
                elif field == 'invoice_date' and operator == '<=':
                    kwargs['date_to'] = value
                elif field == 'partner_id' and operator == '=':
                    kwargs['customer_id'] = value
                elif field == 'state' and operator == '=':
                    kwargs['status'] = value

        return self.search_invoices(**kwargs)

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(service_name="odoo_financial_report")
    def get_financial_report(
        self,
        report_type: str,
        date_from: str,
        date_to: str
    ) -> Dict[str, Any]:
        """
        Generate financial reports from invoice data.

        Args:
            report_type: Type of report (revenue_summary, receivables, payment_collection)
            date_from: Start date for report period (YYYY-MM-DD format)
            date_to: End date for report period (YYYY-MM-DD format)

        Returns:
            Dictionary with report data including metrics and calculations

        Raises:
            ValueError: If report_type is invalid

        Example:
            >>> client.get_financial_report("revenue_summary", "2026-03-01", "2026-03-31")
            {"report_type": "revenue_summary", "total_revenue": 1500.00, ...}
        """
        # Validate report type
        valid_types = ["revenue_summary", "receivables", "payment_collection"]
        if report_type not in valid_types:
            raise ValueError(f"Invalid report type: {report_type}. Must be one of {valid_types}")

        # Get all posted invoices for the period
        invoices = self.search_invoices(
            date_from=date_from,
            date_to=date_to,
            status="posted",
            limit=1000  # High limit for comprehensive reporting
        )

        # Calculate metrics based on report type
        if report_type == "revenue_summary":
            total_revenue = sum(inv['amount_total'] for inv in invoices)
            return {
                'report_type': 'revenue_summary',
                'period_start': date_from,
                'period_end': date_to,
                'total_revenue': total_revenue,
                'invoice_count': len(invoices)
            }

        elif report_type == "receivables":
            total_outstanding = sum(inv['amount_residual'] for inv in invoices)
            return {
                'report_type': 'receivables',
                'period_start': date_from,
                'period_end': date_to,
                'total_outstanding': total_outstanding,
                'invoice_count': len(invoices)
            }

        elif report_type == "payment_collection":
            total_invoiced = sum(inv['amount_total'] for inv in invoices)
            total_collected = sum(inv['amount_total'] - inv['amount_residual'] for inv in invoices)
            collection_rate = (total_collected / total_invoiced * 100) if total_invoiced > 0 else 0.0

            return {
                'report_type': 'payment_collection',
                'period_start': date_from,
                'period_end': date_to,
                'total_invoiced': total_invoiced,
                'total_collected': total_collected,
                'total_outstanding': total_invoiced - total_collected,
                'collection_rate': round(collection_rate, 2),
                'invoice_count': len(invoices)
            }


# Utility Functions

def mask_financial_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mask all financial amounts in data structure for audit logging.

    Per SR-009 requirement, all financial amounts must be replaced with "***"
    in audit logs to protect sensitive financial information.

    Args:
        data: Dictionary containing financial data

    Returns:
        Dictionary with all amount fields masked

    Example:
        >>> mask_financial_data({"amount": 1500.00, "name": "Invoice"})
        {"amount": "***", "name": "Invoice"}
    """
    import copy

    # Financial field names to mask
    financial_fields = {
        'amount', 'total', 'subtotal', 'price', 'cost',
        'balance', 'payment', 'price_unit', 'amount_total',
        'amount_untaxed', 'amount_tax', 'amount_residual',
        'tax', 'discount', 'fee', 'charge', 'revenue', 'expense'
    }

    def mask_recursive(obj):
        """Recursively mask financial fields in nested structures."""
        if isinstance(obj, dict):
            masked = {}
            for key, value in obj.items():
                if key.lower() in financial_fields:
                    masked[key] = "***"
                else:
                    masked[key] = mask_recursive(value)
            return masked
        elif isinstance(obj, list):
            return [mask_recursive(item) for item in obj]
        else:
            return obj

    return mask_recursive(copy.deepcopy(data))


def generate_approval_id(operation_type: str) -> str:
    """
    Generate unique approval ID for idempotency tracking.

    Format: approval_YYYYMMDD_HHMMSS_{operation_type}

    Args:
        operation_type: Type of operation (e.g., "invoice", "payment")

    Returns:
        Unique approval ID string

    Example:
        >>> generate_approval_id("invoice")
        "approval_20260317_143022_invoice"
    """
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")
    return f"approval_{date_str}_{time_str}_{operation_type}"


def create_approval_request_file(
    operation_type: str,
    data: Dict[str, Any],
    approval_id: str,
    vault_path: str = "./AI_Employee_Vault"
) -> str:
    """
    Create approval request file in Pending_Approval/ directory.

    File format: Markdown with YAML frontmatter

    Args:
        operation_type: Type of operation ("invoice" or "payment")
        data: Operation data to include in request
        approval_id: Unique approval ID for tracking
        vault_path: Path to AI Employee Vault

    Returns:
        Path to created approval request file

    Example:
        >>> create_approval_request_file("invoice", {...}, "approval_123")
        "./AI_Employee_Vault/Pending_Approval/APPROVAL_invoice_20260317.md"
    """
    from pathlib import Path
    from datetime import timedelta
    import json

    # Create Pending_Approval directory if it doesn't exist
    pending_dir = Path(vault_path) / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filename = f"APPROVAL_{operation_type}_{timestamp}.md"
    file_path = pending_dir / filename

    # Mask financial data for display
    masked_data = mask_financial_data(data)

    # Calculate expiration time (24 hours from now)
    expires = now + timedelta(hours=24)

    # Create YAML frontmatter with invoice_id for executor
    frontmatter = f"""---
approval_id: {approval_id}
operation: {operation_type}
status: pending
created: {now.isoformat()}
expires: {expires.isoformat()}
invoice_id: {data.get('invoice_id', '')}
---

"""

    # Create markdown body based on operation type
    if operation_type == "invoice":
        body = f"""# Approval Request: Create Invoice

**Approval ID**: `{approval_id}`

## Invoice Details

```yaml
{json.dumps(masked_data, indent=2)}
```

## Action Required

Please review the invoice details above and approve or reject this request.

- To **approve**: Move this file to `Approved/` directory
- To **reject**: Move this file to `Rejected/` directory or delete it

**Note**: Financial amounts are masked for security. Full details will be visible in Odoo after approval.
"""
    elif operation_type == "payment":
        body = f"""# Approval Request: Record Payment

**Approval ID**: `{approval_id}`

## Payment Details

```yaml
{json.dumps(masked_data, indent=2)}
```

## Action Required

Please review the payment details above and approve or reject this request.

- To **approve**: Move this file to `Approved/` directory
- To **reject**: Move this file to `Rejected/` directory or delete it

**Note**: Financial amounts are masked for security. Full details will be visible in Odoo after approval.
"""
    else:
        body = f"""# Approval Request: {operation_type.title()}

**Approval ID**: `{approval_id}`

## Details

```yaml
{json.dumps(masked_data, indent=2)}
```

## Action Required

Please review and approve or reject this request.

- To **approve**: Move this file to `Approved/` directory
- To **reject**: Move this file to `Rejected/` directory or delete it
"""

    # Write file
    with open(file_path, 'w') as f:
        f.write(frontmatter + body)

    return str(file_path)

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(service_name="odoo_invoice")
    def get_invoice_details(self, invoice_id: int) -> Dict[str, Any]:
        """Get invoice details from Odoo.
        
        Args:
            invoice_id: Odoo invoice ID
            
        Returns:
            Dict with invoice details (id, state, amount_residual, etc.)
            
        Raises:
            ValueError: If invoice not found
        """
        self._ensure_authenticated()
        
        # Search for invoice
        invoices = self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.move', 'search_read',
            [[['id', '=', invoice_id], ['move_type', '=', 'out_invoice']]],
            {'fields': ['id', 'state', 'amount_residual', 'amount_total', 'partner_id', 'name']}
        )
        
        if not invoices:
            raise ValueError(f"Invoice with ID {invoice_id} not found")
            
        return invoices[0]

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(service_name="odoo_payment")
    def record_payment(
        self,
        invoice_id: int,
        amount: float,
        payment_date: str,
        payment_method: str,
        approval_id: str
    ) -> int:
        """Record payment for an invoice in Odoo.
        
        Args:
            invoice_id: Odoo invoice ID
            amount: Payment amount
            payment_date: Payment date (YYYY-MM-DD)
            payment_method: Payment method (bank, cash, etc.)
            approval_id: Unique approval ID for idempotency
            
        Returns:
            Payment ID
            
        Raises:
            ValueError: If invoice not found, not posted, or amount exceeds balance
        """
        self._ensure_authenticated()
        
        # Step 1: Get invoice details and validate
        invoice = self.get_invoice_details(invoice_id)
        
        # Validate invoice is posted
        if invoice['state'] != 'posted':
            raise ValueError(f"Invoice {invoice_id} is not posted (current state: {invoice['state']})")
        
        # Validate amount doesn't exceed outstanding balance
        if amount > invoice['amount_residual']:
            raise ValueError(
                f"Payment amount {amount} exceeds outstanding balance {invoice['amount_residual']}"
            )
        
        # Step 2: Check for existing payment (idempotency)
        existing_payments = self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.payment', 'search_read',
            [[['ref', '=', approval_id]]],
            {'fields': ['id'], 'limit': 1}
        )
        
        if existing_payments:
            # Payment already exists, return existing ID
            return existing_payments[0]['id']
        
        # Step 3: Create payment
        payment_vals = {
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': invoice['partner_id'][0],
            'amount': amount,
            'date': payment_date,
            'ref': approval_id,  # Store approval_id for idempotency
            'journal_id': 6,  # Bank journal (configured in Odoo)
        }
        
        payment_id = self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.payment', 'create',
            [payment_vals]
        )
        
        # Step 4: Reconcile payment with invoice
        # Post the payment
        self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.payment', 'action_post',
            [[payment_id]]
        )
        
        return payment_id
