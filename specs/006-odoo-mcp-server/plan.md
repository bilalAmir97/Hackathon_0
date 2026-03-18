# Implementation Plan: Odoo MCP Server

**Branch**: `006-odoo-mcp-server` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-odoo-mcp-server/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create an MCP server that exposes Odoo accounting operations to Claude Code via four primary tools: create_invoice, record_payment, list_invoices, and get_financial_report. The server implements a JSON-RPC client for Odoo API communication, integrates with the existing approval workflow for financial operations, uses error recovery decorators for reliability, and logs all actions via the audit system. All invoice finalization and payment recording require human approval before execution.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**:
- `mcp` (MCP server framework - already in use)
- `requests` or `xmlrpc.client` (Odoo JSON-RPC/XML-RPC client)
- `google-auth`, `googleapiclient` (existing Gmail dependencies)
- Error recovery decorators from `scripts/error_recovery/`
- Audit logger from `scripts/audit_logger.py`

**Storage**:
- Odoo 17 database (PostgreSQL backend via Docker)
- Vault files for approval workflow (`Pending_Approval/`, `Approved/`, `Done/`)
- Audit logs in `AI_Employee_Vault/Logs/`

**Testing**: pytest (existing test infrastructure)
**Target Platform**: Linux server (WSL2 environment)
**Project Type**: Single project (MCP server + Odoo client library)
**Performance Goals**:
- Invoice creation: <2 minutes end-to-end (per SC-001)
- Invoice queries: <3 seconds for 100 results (per SC-005)
- Payment recording: <30 seconds after approval (per SC-004)

**Constraints**:
- All financial operations require human approval (no auto-posting)
- Idempotent operations to prevent duplicate invoices/payments
- Session management with automatic token renewal
- Circuit breaker pattern for Odoo API failures
- Financial amounts masked in audit logs (SR-009)

**Scale/Scope**:
- 4 MCP tools (create_invoice, record_payment, list_invoices, get_financial_report)
- 50 concurrent invoice creation requests without degradation (per SC-010)
- 99% uptime target (per SC-006)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with project constitution (`.specify/memory/constitution.md`):

- [X] **Local-First Architecture**: Approval requests stored in vault (`Pending_Approval/`), audit logs in `Logs/`, state persisted in vault files
- [X] **Safety Before Autonomy**: All invoice finalization (FR-004) and payment recording (FR-008) require explicit human approval before execution
- [X] **File-Based State Transitions**: Approval workflow uses file movements: `Pending_Approval/` → `Approved/` → `Done/`
- [X] **Idempotent Watchers**: Not applicable (MCP server, not watcher). However, idempotent operations enforced via SR-006 (invoice) and SR-007 (payment) to prevent duplicates
- [X] **Explicit Reasoning**: Claude Code creates Plan.md before invoking MCP tools (existing pattern from email MCP server). Note: This principle applies to Claude Code users of the MCP server, not the server implementation itself.
- [X] **Human Accountability**: Approval boundaries defined in SR-001 (invoices) and SR-002 (payments), no programmatic override capability
- [X] **Auditability**: All operations logged via FR-017 using existing `AuditLogger` class with timestamp, action type, inputs, outputs, approval reference
- [X] **Secrets Management**: Odoo credentials stored in environment variables only (SR-004): ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
- [X] **Tier Isolation**: Gold tier feature, code organized in `mcp_servers/odoo_mcp_server.py` following existing pattern
- [X] **Error Handling**: Circuit breaker (FR-016) and retry with exponential backoff (FR-015) using existing error recovery decorators from `scripts/error_recovery/`

**Violations Requiring Justification**: None - all constitution principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/006-odoo-mcp-server/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output - Odoo API research, JSON-RPC patterns
├── data-model.md        # Phase 1 output - Invoice, Payment, Customer entities
├── quickstart.md        # Phase 1 output - Quick start guide for Odoo MCP
├── contracts/           # Phase 1 output - MCP tool schemas
│   ├── create_invoice.schema.json
│   ├── record_payment.schema.json
│   ├── list_invoices.schema.json
│   └── get_financial_report.schema.json
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
mcp_servers/
├── odoo_mcp_server.py   # Main MCP server with tool definitions (@app.list_tools, @app.call_tool)
├── odoo_client.py       # Odoo JSON-RPC client library (authentication, session, API calls)
└── __init__.py          # Existing file

scripts/
├── error_recovery/      # Existing - decorators for retry and circuit breaker
│   ├── decorators.py    # @with_retry, @with_circuit_breaker
│   └── service_health.py
├── audit_logger.py      # Existing - AuditLogger class
└── approval_executor.py # Existing - approval workflow execution

tests/
├── test_odoo_mcp_server.py      # MCP tool integration tests
├── test_odoo_client.py          # Odoo client unit tests
├── test_integration_odoo.py     # End-to-end workflow tests
└── conftest.py                  # Existing - pytest fixtures

AI_Employee_Vault/
├── Pending_Approval/    # Approval requests for invoices/payments
├── Approved/            # Approved actions ready for execution
├── Done/                # Completed actions
└── Logs/                # Audit trail (YYYY-MM-DD.json)

docker-compose.yml       # Existing - Odoo 17 + PostgreSQL containers
.env.example             # Add ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
```

**Structure Decision**: Single project structure following existing MCP server pattern. The Odoo MCP server mirrors the email MCP server architecture with a main server file (`odoo_mcp_server.py`) and a separate client library (`odoo_client.py`) for API communication. This separation allows the client to be reused by other components and simplifies testing.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations identified. All principles satisfied through:
- Approval workflow integration for financial operations
- Vault-based state management
- Error recovery decorators for reliability
- Audit logging for all actions
- Environment variable-based credential management

---

## Phase 0: Research & Technology Selection

### Odoo API Communication

**Decision**: Use Odoo's JSON-RPC API via `xmlrpc.client` (Python standard library)

**Rationale**:
- Odoo 17 supports both XML-RPC and JSON-RPC protocols
- `xmlrpc.client` is part of Python standard library (no additional dependencies)
- Well-documented authentication and session management
- Proven pattern for external integrations

**Alternatives Considered**:
1. **OdooRPC library** (third-party)
   - Pros: Higher-level abstraction, easier to use
   - Cons: Additional dependency, less control over session management
   - Rejected: Adds dependency complexity, standard library sufficient

2. **Direct REST API** (if available)
   - Pros: Modern HTTP-based approach
   - Cons: Odoo primarily uses RPC, REST API limited
   - Rejected: RPC is the primary supported interface

### Authentication Strategy

**Decision**: Session-based authentication with automatic token renewal

**Implementation**:
```python
# Authenticate once, reuse session
uid = models.execute_kw(db, uid, password, 'res.users', 'authenticate', [db, username, password, {}])
# Store uid and reuse for subsequent calls
# Implement token refresh on 401/403 errors
```

**Session Management**:
- Authenticate on first API call
- Store session UID in memory (not persisted - stateless server)
- Retry authentication on session expiration (401/403 errors)
- Use `@with_retry` decorator for automatic retry with backoff

### Idempotency Strategy

**Decision**: Client-side idempotency keys for invoice/payment operations

**Implementation**:
- Generate unique `approval_id` for each operation (already in approval workflow)
- Store `approval_id` in invoice/payment reference field
- Before creating invoice/payment, search Odoo for existing record with same `approval_id`
- If found, return existing record instead of creating duplicate

**Rationale**: Prevents duplicate invoices/payments on retry after network failure or approval executor restart

### Error Recovery Integration

**Decision**: Use existing error recovery decorators from `scripts/error_recovery/`

**Decorators to Apply**:
1. `@with_retry(max_attempts=3, base_delay=2.0)` - For transient network errors
2. `@with_circuit_breaker(service_name='odoo_api')` - For Odoo service failures

**Application Pattern** (following gmail_watcher.py pattern):
```python
@with_retry(max_attempts=3, base_delay=2.0)
@with_circuit_breaker(service_name='odoo_api')
def create_invoice_in_odoo(self, invoice_data):
    # Odoo API call
    pass
```

### Audit Logging Integration

**Decision**: Use existing `AuditLogger` class from `scripts/audit_logger.py`

**Log Events**:
- `odoo_authenticate` - Authentication success/failure
- `invoice_create` - Invoice creation (draft)
- `invoice_finalize` - Invoice posting (after approval)
- `payment_record` - Payment recording (after approval)
- `invoice_query` - Invoice list queries
- `financial_report` - Financial report generation

**Sensitive Data Masking** (per SR-009):
- Mask all financial amounts in audit logs
- Replace amounts with `"***"` or hash
- Log operation type and approval ID for traceability

---

## Phase 1: Design & Contracts

### Data Model

**Core Entities** (from spec.md):

1. **Invoice**
   - Fields: invoice_id, customer_id, date, due_date, total_amount, status, line_items[]
   - States: draft → posted → paid → cancelled
   - Odoo Model: `account.move` (type='out_invoice')

2. **Payment**
   - Fields: payment_id, invoice_id, amount, date, payment_method, reference
   - Odoo Model: `account.payment`

3. **Customer**
   - Fields: customer_id, name, email, address
   - Odoo Model: `res.partner`
   - Assumption: Customers already exist in Odoo (creation out of scope per spec)

4. **Line Item**
   - Fields: product_id, description, quantity, unit_price, tax_ids[], subtotal
   - Odoo Model: `account.move.line`

5. **Approval Request**
   - Fields: approval_id, action_type, invoice_data/payment_data, risk_assessment, reasoning
   - Storage: Vault file in `Pending_Approval/`
   - Format: Markdown with YAML frontmatter (existing pattern)

### MCP Tool Contracts

#### Tool 1: create_invoice

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "customer_id": {"type": "integer", "description": "Odoo partner ID"},
    "invoice_date": {"type": "string", "format": "date", "description": "Invoice date (YYYY-MM-DD)"},
    "due_date": {"type": "string", "format": "date", "description": "Payment due date (YYYY-MM-DD)"},
    "line_items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "product_id": {"type": "integer", "description": "Odoo product ID"},
          "description": {"type": "string"},
          "quantity": {"type": "number"},
          "unit_price": {"type": "number"}
        },
        "required": ["product_id", "quantity", "unit_price"]
      }
    }
  },
  "required": ["customer_id", "invoice_date", "line_items"]
}
```

**Output**:
```json
{
  "status": "approval_required",
  "approval_file": "APPROVAL_20260317_120000_invoice.md",
  "draft_invoice_id": 123,
  "total_amount": "***",
  "message": "Invoice draft created. Approval required before posting."
}
```

**Workflow**:
1. Validate input parameters (customer exists, products exist)
2. Create draft invoice in Odoo (state='draft')
3. Generate approval request file in `Pending_Approval/`
4. Return approval file path and draft invoice ID
5. Wait for human to move file to `Approved/`
6. Approval executor finalizes invoice (posts to Odoo)

#### Tool 2: record_payment

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "invoice_id": {"type": "integer", "description": "Odoo invoice ID"},
    "amount": {"type": "number", "description": "Payment amount"},
    "payment_date": {"type": "string", "format": "date"},
    "payment_method": {"type": "string", "enum": ["cash", "bank_transfer", "check", "credit_card"]}
  },
  "required": ["invoice_id", "amount", "payment_date", "payment_method"]
}
```

**Output**:
```json
{
  "status": "approval_required",
  "approval_file": "APPROVAL_20260317_120100_payment.md",
  "invoice_id": 123,
  "amount": "***",
  "message": "Payment prepared. Approval required before recording."
}
```

**Workflow**:
1. Validate invoice exists and is posted
2. Validate payment amount ≤ outstanding balance (FR-006)
3. Generate approval request file in `Pending_Approval/`
4. Return approval file path
5. Wait for human approval
6. Approval executor records payment in Odoo

#### Tool 3: list_invoices

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "date_from": {"type": "string", "format": "date", "optional": true},
    "date_to": {"type": "string", "format": "date", "optional": true},
    "customer_id": {"type": "integer", "optional": true},
    "status": {"type": "string", "enum": ["draft", "posted", "paid", "cancelled"], "optional": true},
    "limit": {"type": "integer", "default": 100, "optional": true}
  }
}
```

**Output**:
```json
{
  "status": "success",
  "count": 25,
  "invoices": [
    {
      "invoice_id": 123,
      "invoice_number": "INV/2026/0001",
      "customer_name": "Acme Corp",
      "date": "2026-03-15",
      "due_date": "2026-04-15",
      "total_amount": "***",
      "status": "posted",
      "outstanding_balance": "***"
    }
  ]
}
```

**Workflow**:
1. Build Odoo domain filter from input parameters
2. Query `account.move` model with filters
3. Mask financial amounts in response (SR-009)
4. Return invoice list with metadata

#### Tool 4: get_financial_report

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "report_type": {"type": "string", "enum": ["revenue_summary", "receivables", "payment_collection"]},
    "date_from": {"type": "string", "format": "date"},
    "date_to": {"type": "string", "format": "date"}
  },
  "required": ["report_type", "date_from", "date_to"]
}
```

**Output**:
```json
{
  "status": "success",
  "report_type": "revenue_summary",
  "period": "2026-03-01 to 2026-03-31",
  "total_revenue": "***",
  "paid_amount": "***",
  "outstanding_balance": "***",
  "invoice_count": 42
}
```

**Workflow**:
1. Query Odoo for invoices in date range
2. Aggregate data based on report_type
3. Mask all financial amounts (SR-009)
4. Return aggregated report

### Approval Request Format

Following existing pattern from `approval_executor.py`:

```markdown
---
approval_id: approval_20260317_120000_invoice_123
action_type: invoice_finalize
odoo_invoice_id: 123
action_params:
  invoice_id: 123
  customer_name: "Acme Corp"
  total_amount: "***"
  line_items_count: 3
risk_assessment: low
reasoning: "Customer invoice for completed project work. Standard payment terms."
created_at: 2026-03-17T12:00:00Z
status: pending
---

# Invoice Finalization Approval

**Customer:** Acme Corp
**Invoice ID:** 123
**Total Amount:** [MASKED]
**Line Items:** 3

## Invoice Details

- Product 1: Consulting Services (10 hours @ [MASKED])
- Product 2: Software License (1 unit @ [MASKED])
- Product 3: Support Package (1 month @ [MASKED])

## Risk Assessment

**Level:** Low
**Reasoning:** Standard customer invoice for completed work. Customer has good payment history.

## Actions Required

- [ ] Review invoice details
- [ ] Verify customer and amounts
- [ ] Move to Approved/ to finalize invoice
- [ ] Move to Rejected/ to cancel

## Notes

(Add your review notes here)
```

---

## Phase 2: Implementation Approach

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code (User)                       │
└────────────────────┬────────────────────────────────────────┘
                     │ MCP Protocol
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              odoo_mcp_server.py (MCP Server)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ @app.list_tools() - Expose 4 tools                   │  │
│  │ @app.call_tool() - Route to handlers                 │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Tool Handlers:                                        │  │
│  │ - create_invoice() → approval workflow               │  │
│  │ - record_payment() → approval workflow               │  │
│  │ - list_invoices() → direct query                     │  │
│  │ - get_financial_report() → direct query              │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              odoo_client.py (Odoo API Client)               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ OdooClient class:                                     │  │
│  │ - authenticate() - Session management                │  │
│  │ - create_draft_invoice() - Create invoice            │  │
│  │ - finalize_invoice() - Post invoice                  │  │
│  │ - record_payment() - Record payment                  │  │
│  │ - search_invoices() - Query with filters             │  │
│  │ - get_invoice_details() - Fetch invoice data         │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Error Recovery:                                       │  │
│  │ - @with_retry decorator on all API calls             │  │
│  │ - @with_circuit_breaker for service health           │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │ JSON-RPC (xmlrpc.client)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Odoo 17 (Docker Container)                     │
│  - PostgreSQL database                                      │
│  - Accounting module installed                              │
│  - Models: account.move, account.payment, res.partner       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│           Approval Workflow (File-Based)                    │
│  Pending_Approval/ → Approved/ → Done/                      │
│  (Monitored by approval_executor.py)                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│           Audit Logging (audit_logger.py)                   │
│  Logs/ → YYYY-MM-DD.json (all operations logged)            │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Sequence

**Step 1: Odoo Client Library** (`odoo_client.py`)
- Implement `OdooClient` class with authentication
- Add methods for invoice operations (create, finalize, query)
- Add methods for payment operations (record, query)
- Apply error recovery decorators
- Unit tests for each method

**Step 2: MCP Server** (`odoo_mcp_server.py`)
- Implement MCP server structure (following `email_mcp_server.py` pattern)
- Define 4 tools with input schemas
- Implement tool handlers
- Integrate with `OdooClient`
- Integration tests for each tool

**Step 3: Approval Workflow Integration**
- Create approval request generation functions
- Update `approval_executor.py` to handle Odoo actions
- Add `execute_invoice_finalize()` method
- Add `execute_payment_record()` method
- End-to-end workflow tests

**Step 4: Audit Logging Integration**
- Add audit log calls to all operations
- Implement amount masking (SR-009)
- Verify log format matches existing pattern
- Test log generation and masking

**Step 5: Error Recovery Testing**
- Test retry behavior on network failures
- Test circuit breaker on Odoo service failures
- Test session renewal on token expiration
- Test idempotency on duplicate operations

### Key Architectural Decisions

**Decision 1: Separate Client Library**
- **Rationale**: Separation of concerns - MCP server handles protocol, client handles Odoo API
- **Benefit**: Client can be reused by other components (future watchers, skills)
- **Pattern**: Mirrors `email_client.py` / `email_mcp_server.py` separation

**Decision 2: Approval Workflow for All Financial Operations**
- **Rationale**: Constitution principle "Safety Before Autonomy" + spec requirements SR-001, SR-002
- **Benefit**: Human oversight prevents costly financial errors
- **Trade-off**: Adds latency (approval time), but acceptable for financial operations

**Decision 3: Amount Masking in Audit Logs**
- **Rationale**: Spec requirement SR-009 (maximum security approach selected by user)
- **Benefit**: Protects sensitive financial data in logs
- **Trade-off**: Reduces debugging capability, but approval files contain full details

**Decision 4: Idempotency via Approval ID**
- **Rationale**: Prevents duplicate invoices/payments on retry (SR-006, SR-007)
- **Implementation**: Store `approval_id` in Odoo reference field, check before creating
- **Benefit**: Safe retries after network failures or system restarts

**Decision 5: Session Management in Memory**
- **Rationale**: Stateless MCP server, session recreated on each startup
- **Benefit**: Simpler implementation, no session persistence needed
- **Trade-off**: Re-authentication on server restart (acceptable overhead)

### Risk Mitigation

**Risk 1: Odoo API Changes**
- **Mitigation**: Use stable Odoo 17 API, version lock in dependencies
- **Monitoring**: Integration tests will catch API changes
- **Fallback**: Document API version in code comments

**Risk 2: Session Expiration Mid-Operation**
- **Mitigation**: Retry decorator automatically re-authenticates on 401/403
- **Testing**: Simulate session expiration in tests
- **Monitoring**: Audit logs track authentication failures

**Risk 3: Duplicate Invoice Creation**
- **Mitigation**: Idempotency check via approval_id before creation
- **Testing**: Test duplicate creation attempts
- **Monitoring**: Audit logs track all invoice creation attempts

**Risk 4: Approval Workflow Bottleneck**
- **Mitigation**: Clear approval request format with all necessary details
- **Monitoring**: Track approval time in audit logs (SC-003: <5 minutes target)
- **Escalation**: Alert if approval requests accumulate

**Risk 5: Circuit Breaker False Positives**
- **Mitigation**: Tune circuit breaker thresholds (5 failures before opening)
- **Testing**: Test circuit breaker behavior under load
- **Monitoring**: Service health dashboard tracks circuit breaker state

---

## Quickstart Guide Preview

The quickstart guide (`quickstart.md`) will include:

1. **Prerequisites**
   - Odoo 17 running (Docker)
   - Python 3.10+ environment
   - Environment variables configured

2. **Installation**
   ```bash
   # Install dependencies
   pip install mcp requests

   # Configure environment
   cp .env.example .env
   # Edit .env: ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
   ```

3. **Running the MCP Server**
   ```bash
   python mcp_servers/odoo_mcp_server.py
   ```

4. **Example Usage from Claude Code**
   ```python
   # Create invoice (requires approval)
   result = mcp.call_tool("create_invoice", {
       "customer_id": 123,
       "invoice_date": "2026-03-17",
       "line_items": [
           {"product_id": 1, "quantity": 10, "unit_price": 100.00}
       ]
   })
   # Returns approval file path

   # Human reviews and approves (moves file to Approved/)
   # Approval executor finalizes invoice in Odoo
   ```

5. **Testing**
   ```bash
   pytest tests/test_odoo_mcp_server.py -v
   pytest tests/test_odoo_client.py -v
   pytest tests/test_integration_odoo.py -v
   ```

---

## Success Criteria Verification

Mapping implementation to spec success criteria:

- **SC-001**: Invoice creation <2 minutes → Approval workflow optimized, clear request format
- **SC-002**: 95% success rate → Error recovery decorators, idempotency, validation
- **SC-003**: Approval workflow <5 minutes → Clear approval request with all details
- **SC-004**: Payment recording <30 seconds → Direct API call after approval
- **SC-005**: Query results <3 seconds → Efficient Odoo domain filters, pagination
- **SC-006**: 99% uptime → Circuit breaker, retry logic, graceful degradation
- **SC-007**: Circuit breaker fails fast <5 seconds → Configured threshold
- **SC-008**: 100% audit coverage → AuditLogger on all operations
- **SC-009**: Financial reports <10 seconds → Optimized aggregation queries
- **SC-010**: 50 concurrent requests → Stateless server, connection pooling
- **SC-011**: 80% self-service resolution → Clear error messages, validation
- **SC-012**: 95% approval on first review → Comprehensive approval request format

---

## Next Steps

After `/sp.plan` completion:

1. **Review and validate** this plan against spec requirements
2. **Run `/sp.tasks`** to generate implementation tasks from this plan
3. **Implement in order**: odoo_client.py → odoo_mcp_server.py → approval integration → tests
4. **Test incrementally**: Unit tests → Integration tests → End-to-end workflow tests
5. **Document**: Update quickstart.md with real examples after implementation
