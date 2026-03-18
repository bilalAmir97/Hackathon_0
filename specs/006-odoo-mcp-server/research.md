# Research: Odoo MCP Server

**Feature**: 006-odoo-mcp-server
**Date**: 2026-03-17
**Phase**: 0 (Research & Technology Selection)

## Research Questions

### Q1: How does Odoo API authentication work?

**Answer**: Odoo uses RPC-based authentication with session management.

**Authentication Flow**:
1. Connect to Odoo server via XML-RPC or JSON-RPC
2. Call `authenticate()` method with database, username, password
3. Receive user ID (uid) as session token
4. Use uid for all subsequent API calls
5. Session persists until server restart or explicit logout

**Python Implementation**:
```python
import xmlrpc.client

# Connect to Odoo
url = 'http://localhost:8069'
db = 'odoo'
username = 'admin'
password = 'admin'

# Authenticate
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

# Use uid for API calls
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
```

**Session Management**:
- Sessions are stateless from client perspective
- Re-authentication required on connection loss
- No explicit token refresh needed (uid remains valid)

**Decision**: Use `xmlrpc.client` (Python standard library) for RPC communication.

---

### Q2: What is the Odoo invoice data model?

**Answer**: Odoo uses `account.move` model for invoices (Odoo 13+).

**Key Fields**:
- `partner_id`: Customer (res.partner)
- `move_type`: 'out_invoice' for customer invoices
- `invoice_date`: Invoice date
- `invoice_date_due`: Due date
- `state`: draft → posted → paid
- `invoice_line_ids`: One2many relation to account.move.line
- `amount_total`: Total invoice amount
- `amount_residual`: Outstanding balance

**Line Item Model** (`account.move.line`):
- `product_id`: Product reference
- `name`: Description
- `quantity`: Quantity
- `price_unit`: Unit price
- `tax_ids`: Applied taxes
- `price_subtotal`: Line subtotal

**State Transitions**:
- `draft`: Editable, not posted
- `posted`: Finalized, immutable
- `cancel`: Cancelled invoice

**Decision**: Use `account.move` model with `move_type='out_invoice'` for customer invoices.

---

### Q3: How to implement idempotent invoice creation?

**Answer**: Use custom reference field to store approval_id and check before creation.

**Strategy**:
1. Generate unique `approval_id` for each operation
2. Store `approval_id` in invoice `ref` field (reference/memo)
3. Before creating invoice, search for existing invoice with same `ref`
4. If found, return existing invoice instead of creating duplicate

**Implementation**:
```python
def create_invoice_idempotent(approval_id, invoice_data):
    # Check if invoice already exists
    existing = models.execute_kw(db, uid, password,
        'account.move', 'search_read',
        [[('ref', '=', approval_id)]],
        {'fields': ['id', 'name', 'state']}
    )

    if existing:
        return existing[0]  # Return existing invoice

    # Create new invoice with approval_id in ref field
    invoice_data['ref'] = approval_id
    invoice_id = models.execute_kw(db, uid, password,
        'account.move', 'create',
        [invoice_data]
    )
    return invoice_id
```

**Benefits**:
- Safe retries after network failures
- Prevents duplicate invoices on approval executor restart
- Audit trail via approval_id reference

**Decision**: Implement idempotency via `ref` field with approval_id.

---

### Q4: What error recovery patterns should be used?

**Answer**: Use existing error recovery decorators from `scripts/error_recovery/`.

**Decorators Available**:
1. `@with_retry(max_attempts=3, base_delay=2.0)` - Exponential backoff retry
2. `@with_circuit_breaker(service_name='odoo_api')` - Circuit breaker pattern

**Application Pattern** (from gmail_watcher.py):
```python
from scripts.error_recovery.decorators import with_retry, with_circuit_breaker

class OdooClient:
    @with_retry(max_attempts=3, base_delay=2.0)
    @with_circuit_breaker(service_name='odoo_api')
    def create_invoice(self, invoice_data):
        # Odoo API call
        pass
```

**Error Scenarios**:
- **Network timeout**: Retry with exponential backoff
- **Connection refused**: Circuit breaker opens after 5 failures
- **Authentication failure**: Re-authenticate and retry
- **Invalid data**: Fail fast, return validation error

**Circuit Breaker Behavior**:
- Closed: Normal operation
- Open: Fail fast after threshold (5 failures)
- Half-open: Test recovery after cooldown (60 seconds)

**Decision**: Apply both decorators to all Odoo API calls.

---

### Q5: How to integrate with existing approval workflow?

**Answer**: Follow existing pattern from `approval_executor.py` and `email_mcp_server.py`.

**Approval Workflow Pattern**:
1. MCP tool creates draft invoice in Odoo
2. MCP tool generates approval request file in `Pending_Approval/`
3. Return approval file path to Claude Code
4. Human reviews and moves file to `Approved/` or `Rejected/`
5. `approval_executor.py` detects file movement (watchdog)
6. Executor calls finalization method (post invoice to Odoo)
7. Executor logs action and moves file to `Done/`

**Approval Request Format** (YAML frontmatter + Markdown):
```markdown
---
approval_id: approval_20260317_120000_invoice_123
action_type: invoice_finalize
odoo_invoice_id: 123
action_params:
  invoice_id: 123
  customer_name: "Acme Corp"
  total_amount: "***"
risk_assessment: low
reasoning: "Standard customer invoice"
created_at: 2026-03-17T12:00:00Z
status: pending
---

# Invoice Finalization Approval
...
```

**Integration Points**:
1. Add `execute_invoice_finalize()` to `approval_executor.py`
2. Add `execute_payment_record()` to `approval_executor.py`
3. Update `on_file_moved_to_approved()` to handle Odoo actions

**Decision**: Extend `approval_executor.py` with Odoo action handlers.

---

### Q6: How to mask financial amounts in audit logs?

**Answer**: Replace all amount values with "***" before logging.

**Implementation**:
```python
def mask_financial_data(data):
    """Mask financial amounts in data dictionary."""
    masked = data.copy()

    # Fields to mask
    amount_fields = ['amount', 'total_amount', 'price', 'unit_price',
                     'subtotal', 'amount_residual', 'amount_total']

    for field in amount_fields:
        if field in masked:
            masked[field] = "***"

    # Recursively mask nested structures
    for key, value in masked.items():
        if isinstance(value, dict):
            masked[key] = mask_financial_data(value)
        elif isinstance(value, list):
            masked[key] = [mask_financial_data(item) if isinstance(item, dict) else item
                          for item in value]

    return masked

# Usage in audit logging
audit_logger.log_action(
    action_type="invoice_create",
    actor="odoo_mcp",
    target=customer_name,
    parameters=mask_financial_data(invoice_data),
    result="success"
)
```

**Masked Fields**:
- All amount fields (total, subtotal, unit price, etc.)
- Payment amounts
- Outstanding balances
- Financial report totals

**Not Masked**:
- Invoice numbers
- Customer names
- Dates
- Quantities
- Approval IDs

**Decision**: Implement `mask_financial_data()` utility function, apply to all audit log calls.

---

## Technology Stack Summary

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| RPC Client | `xmlrpc.client` (stdlib) | Standard library, no dependencies, well-documented |
| MCP Framework | `mcp` (existing) | Already in use for email MCP server |
| Error Recovery | Existing decorators | Proven pattern, consistent with codebase |
| Audit Logging | `AuditLogger` (existing) | Consistent logging across all services |
| Approval Workflow | File-based (existing) | Constitution requirement, proven pattern |
| Testing | `pytest` (existing) | Existing test infrastructure |

---

## Best Practices from Odoo Documentation

### Invoice Creation Best Practices

1. **Always validate customer exists** before creating invoice
2. **Set move_type='out_invoice'** for customer invoices
3. **Use draft state** for initial creation, post after approval
4. **Include line items** with product_id, quantity, price_unit
5. **Let Odoo calculate taxes** automatically based on product configuration

### Payment Recording Best Practices

1. **Validate invoice is posted** before recording payment
2. **Check outstanding balance** to prevent overpayment
3. **Use account.payment model** for payment recording
4. **Link payment to invoice** via invoice_ids field
5. **Reconcile automatically** by setting appropriate payment method

### Query Optimization

1. **Use domain filters** instead of fetching all records
2. **Limit fields** in search_read to only needed fields
3. **Paginate results** for large datasets (limit + offset)
4. **Use search_count** for count-only queries
5. **Cache frequently accessed data** (customers, products)

---

## Security Considerations

### Credential Management

- Store credentials in environment variables only
- Never log passwords or API keys
- Use read-only user for query operations if possible
- Rotate credentials every 90 days

### Data Protection

- Mask all financial amounts in logs (SR-009)
- Approval requests contain full details (not logged)
- Audit trail tracks operations without sensitive data
- GDPR compliance via data masking

### Access Control

- Odoo user should have minimal required permissions
- Accounting module access required
- No admin privileges needed for normal operations
- Separate user for production vs development

---

## Performance Considerations

### Connection Pooling

- Reuse xmlrpc.client connections
- Authenticate once per server instance
- Handle connection timeouts gracefully

### Query Optimization

- Use domain filters to reduce data transfer
- Limit fields in search_read queries
- Paginate large result sets (100 records per page)
- Cache customer/product lookups

### Concurrency

- MCP server is stateless (supports concurrent requests)
- Odoo handles concurrent API calls
- No shared state between requests
- Circuit breaker prevents cascading failures

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Odoo API changes | High | Version lock Odoo 17, integration tests |
| Session expiration | Medium | Retry decorator re-authenticates automatically |
| Duplicate invoices | High | Idempotency via approval_id in ref field |
| Network failures | Medium | Retry with exponential backoff, circuit breaker |
| Approval bottleneck | Low | Clear approval format, 5-minute target |
| Data masking errors | Medium | Unit tests for masking function |

---

## Research Conclusions

1. **Odoo API is well-suited** for MCP integration via XML-RPC
2. **Existing patterns** (email MCP, approval workflow) apply directly
3. **Error recovery infrastructure** already in place and proven
4. **Idempotency achievable** via approval_id in reference field
5. **Security requirements met** via environment variables and data masking
6. **Performance targets achievable** with proper query optimization

**Ready to proceed to Phase 1: Design & Contracts**
