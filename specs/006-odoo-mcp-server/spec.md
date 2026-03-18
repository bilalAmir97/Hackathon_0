# Feature Specification: Odoo MCP Server

**Feature Branch**: `006-odoo-mcp-server`
**Created**: 2026-03-17
**Status**: Draft
**Input**: User description: "Create Odoo MCP Server that provides Claude Code with tools to interact with Odoo accounting system. The server must implement JSON-RPC client to communicate with Odoo API and expose MCP tools for: (1) create_invoice - create customer invoices with line items, (2) record_payment - record payments against invoices, (3) list_invoices - query invoices with filters (date range, customer, status), (4) get_financial_report - retrieve financial summaries. All operations must integrate with existing approval workflow (require approval before finalizing invoices/payments), use error recovery decorators (retry + circuit breaker), and log all actions via audit system. Server must handle authentication, session management, and proper error responses."

## User Scenarios & Testing

### User Story 1 - Create Customer Invoices (Priority: P1) 🎯 MVP

Claude Code user needs to create invoices for customers directly from the AI Employee system without manually logging into Odoo. The user provides customer details, invoice line items (products/services, quantities, prices), and the system creates a draft invoice in Odoo, routes it through the approval workflow, and finalizes it upon approval.

**Why this priority**: Invoice creation is the core accounting function and the primary reason for Odoo integration. Without this, the integration has no value. This is the MVP that delivers immediate business value.

**Independent Test**: Can be fully tested by creating a draft invoice via Claude Code, approving it through the approval workflow, and verifying the invoice appears in Odoo with correct line items and totals. Delivers standalone value by automating invoice creation.

**Acceptance Scenarios**:

1. **Given** Claude Code user has customer information and line items, **When** user requests invoice creation via MCP tool, **Then** system creates draft invoice in Odoo and creates approval request in Needs_Action/
2. **Given** draft invoice approval request exists, **When** user approves the request, **Then** system finalizes invoice in Odoo and updates invoice status to "posted"
3. **Given** draft invoice approval request exists, **When** user rejects the request, **Then** system cancels draft invoice in Odoo and logs rejection reason
4. **Given** invoice creation fails due to invalid customer, **When** system attempts to create invoice, **Then** system returns clear error message identifying the issue
5. **Given** invoice with multiple line items, **When** invoice is created, **Then** all line items appear correctly with accurate subtotals and total amount

---

### User Story 2 - Record Payments Against Invoices (Priority: P2)

Claude Code user needs to record customer payments against existing invoices to track accounts receivable and cash flow. The user specifies the invoice, payment amount, payment date, and payment method, and the system records the payment in Odoo after approval.

**Why this priority**: Payment recording completes the invoice lifecycle and is essential for accurate financial tracking. This is the second most critical function after invoice creation.

**Independent Test**: Can be tested by creating an invoice (using Story 1), recording a payment against it via Claude Code, approving the payment, and verifying the invoice status changes to "paid" in Odoo. Delivers value by automating payment tracking.

**Acceptance Scenarios**:

1. **Given** posted invoice exists in Odoo, **When** user records payment via MCP tool, **Then** system creates payment approval request in Needs_Action/
2. **Given** payment approval request exists, **When** user approves the request, **Then** system records payment in Odoo and updates invoice status
3. **Given** partial payment is recorded, **When** payment amount is less than invoice total, **Then** invoice status shows as "partially paid" with remaining balance
4. **Given** payment exceeds invoice amount, **When** user attempts to record overpayment, **Then** system rejects payment with clear error message
5. **Given** payment for non-existent invoice, **When** user attempts to record payment, **Then** system returns error identifying invoice not found

---

### User Story 3 - Query and List Invoices (Priority: P3)

Claude Code user needs to search and retrieve invoice information to answer questions about billing status, outstanding amounts, and customer payment history. The user can filter by date range, customer name, and invoice status (draft, posted, paid, cancelled).

**Why this priority**: Invoice querying enables visibility into financial data and supports decision-making. While valuable, it's not required for the core create-and-pay workflow to function.

**Independent Test**: Can be tested by creating several invoices with different statuses and customers, then querying with various filters to verify correct results are returned. Delivers value by providing financial visibility without manual Odoo access.

**Acceptance Scenarios**:

1. **Given** multiple invoices exist in Odoo, **When** user queries invoices by date range, **Then** system returns all invoices within specified date range
2. **Given** invoices for multiple customers, **When** user filters by customer name, **Then** system returns only invoices for that customer
3. **Given** invoices with various statuses, **When** user filters by status "paid", **Then** system returns only fully paid invoices
4. **Given** no invoices match filter criteria, **When** user queries with filters, **Then** system returns empty result set with informative message
5. **Given** large number of invoices, **When** user queries without filters, **Then** system returns paginated results with reasonable page size

---

### User Story 4 - Retrieve Financial Reports (Priority: P4)

Claude Code user needs to access financial summaries and reports to understand business performance without manually generating reports in Odoo. The user can request revenue summaries, outstanding receivables, and payment collection metrics for specified time periods.

**Why this priority**: Financial reporting provides valuable business insights but is not required for day-to-day invoice and payment operations. This is a "nice to have" that enhances the system but isn't critical for MVP.

**Independent Test**: Can be tested by creating invoices and payments over a time period, then requesting financial reports and verifying the calculated totals match the underlying transactions. Delivers value by automating financial analysis.

**Acceptance Scenarios**:

1. **Given** invoices and payments exist for a time period, **When** user requests revenue summary, **Then** system returns total revenue, paid amount, and outstanding balance
2. **Given** multiple customers with outstanding invoices, **When** user requests receivables report, **Then** system returns list of customers with amounts owed
3. **Given** payments recorded in time period, **When** user requests payment collection metrics, **Then** system returns total collected, average payment time, and collection rate
4. **Given** no financial data for requested period, **When** user requests report, **Then** system returns report with zero values and informative message
5. **Given** report generation fails, **When** system encounters error, **Then** system returns clear error message and logs failure for debugging

---

### Edge Cases

- What happens when Odoo API is unreachable or times out during invoice creation?
- How does system handle authentication token expiration mid-operation?
- What happens when user attempts to create invoice with invalid product/service codes?
- How does system handle concurrent modifications to the same invoice?
- What happens when approval request expires or is abandoned?
- How does system handle invoices with zero or negative amounts?
- What happens when customer record doesn't exist in Odoo?
- How does system handle network interruptions during payment recording?
- What happens when invoice currency doesn't match payment currency?
- How does system handle very large result sets from invoice queries?

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide MCP tool "create_invoice" that accepts customer identifier, line items (description, quantity, unit price), invoice date, and due date
- **FR-002**: System MUST create draft invoices in Odoo that require explicit approval before finalization
- **FR-003**: System MUST generate approval request in Needs_Action/ directory for each invoice creation with invoice details and total amount
- **FR-004**: System MUST finalize (post) invoice in Odoo only after approval is granted
- **FR-005**: System MUST provide MCP tool "record_payment" that accepts invoice identifier, payment amount, payment date, and payment method
- **FR-006**: System MUST validate payment amount does not exceed invoice outstanding balance
- **FR-007**: System MUST generate approval request in Needs_Action/ directory for each payment with payment details
- **FR-008**: System MUST record payment in Odoo only after approval is granted
- **FR-009**: System MUST provide MCP tool "list_invoices" that accepts optional filters for date range, customer, and status
- **FR-010**: System MUST return invoice list with key fields: invoice number, customer name, date, due date, amount, status, outstanding balance
- **FR-011**: System MUST provide MCP tool "get_financial_report" that accepts report type and date range
- **FR-012**: System MUST calculate and return financial summaries including total revenue, paid amount, outstanding receivables
- **FR-013**: System MUST authenticate with Odoo using credentials from environment variables
- **FR-014**: System MUST maintain session with Odoo and handle session renewal automatically
- **FR-015**: System MUST retry failed operations using exponential backoff (via error recovery decorators)
- **FR-016**: System MUST implement circuit breaker pattern to prevent cascading failures when Odoo is unavailable
- **FR-017**: System MUST log all invoice creation, payment recording, and query operations to audit system
- **FR-018**: System MUST return structured error responses with clear error messages and error codes
- **FR-019**: System MUST validate all input parameters before making Odoo API calls
- **FR-020**: System MUST handle Odoo API errors gracefully and translate them to user-friendly messages

### Security & Approval Requirements

- **SR-001**: System MUST require human approval for all invoice finalization operations (no auto-posting)
- **SR-002**: System MUST require human approval for all payment recording operations
- **SR-003**: System MUST log all invoice and payment operations to audit trail with timestamp, actor, action, and result
- **SR-004**: System MUST store Odoo credentials only in environment variables (ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
- **SR-005**: System MUST create approval requests with sufficient detail for informed decision-making (customer, amount, line items)
- **SR-006**: System MUST prevent duplicate invoice creation through idempotent operations
- **SR-007**: System MUST prevent duplicate payment recording through idempotent operations
- **SR-008**: System MUST validate user has permission to perform financial operations before executing
- **SR-009**: System MUST mask all financial amounts in audit logs to protect sensitive data (amounts replaced with "***" or hash)
- **SR-010**: System MUST implement rate limiting to prevent abuse of Odoo API

### Key Entities

- **Invoice**: Represents a customer invoice with header information (customer, date, due date, total) and line items (product/service, quantity, price, subtotal). Has lifecycle states: draft, posted, paid, cancelled.
- **Payment**: Represents a payment transaction against an invoice with amount, date, payment method, and reference to invoice. Links invoice to cash receipt.
- **Customer**: Represents a business entity that receives invoices. Contains name, contact information, and billing details. Must exist in Odoo before invoice creation.
- **Line Item**: Represents a single product or service on an invoice with description, quantity, unit price, taxes, and calculated subtotal.
- **Approval Request**: Represents a pending approval for invoice or payment operation. Contains operation details, requester, timestamp, and approval status.
- **Financial Report**: Represents aggregated financial data for a time period including revenue totals, payment totals, outstanding balances, and collection metrics.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can create a complete invoice (with 3-5 line items) via Claude Code in under 2 minutes
- **SC-002**: System successfully creates and posts 95% of invoices without errors on first attempt
- **SC-003**: Invoice approval workflow completes within 5 minutes of approval request creation
- **SC-004**: Payment recording operations complete within 30 seconds after approval
- **SC-005**: Invoice queries return results within 3 seconds for result sets up to 100 invoices
- **SC-006**: System maintains 99% uptime for invoice and payment operations
- **SC-007**: Circuit breaker prevents system degradation when Odoo is unavailable (fails fast within 5 seconds)
- **SC-008**: All financial operations are logged to audit trail with 100% coverage
- **SC-009**: Users can retrieve financial reports for any date range within 10 seconds
- **SC-010**: System handles at least 50 concurrent invoice creation requests without performance degradation
- **SC-011**: Error messages are clear enough that users can resolve 80% of issues without support
- **SC-012**: Approval requests contain sufficient detail that 95% are approved or rejected on first review (no clarification needed)

## Assumptions

- Odoo 17 is already installed and accessible via network
- Odoo Accounting module is installed and configured
- Customer records already exist in Odoo (customer creation is out of scope)
- Product/service catalog already exists in Odoo (product creation is out of scope)
- Single currency operations (multi-currency is out of scope for MVP)
- Standard Odoo invoice workflow is acceptable (no custom workflow modifications)
- Approval workflow infrastructure already exists in AI Employee system
- Audit logging infrastructure already exists in AI Employee system
- Error recovery decorators already exist and are tested
- MCP server protocol and infrastructure are understood and available

## Out of Scope

- Customer creation or modification in Odoo
- Product/service catalog management
- Multi-currency invoice support
- Credit notes or refunds
- Recurring invoices or subscriptions
- Invoice templates or custom layouts
- Email delivery of invoices to customers
- Payment gateway integration (only recording of payments, not processing)
- Bank reconciliation
- Tax calculation customization (uses Odoo defaults)
- Multi-company operations
- Odoo module installation or configuration
- Custom Odoo workflow modifications

## Dependencies

- Odoo 17 with Accounting module installed and running
- Odoo API accessible via JSON-RPC
- Environment variables configured with Odoo credentials
- Existing approval workflow system in AI Employee
- Existing audit logging system in AI Employee
- Error recovery decorators (retry_policy, circuit_breaker) from 005-error-recovery
- MCP server framework and protocol implementation

## Risks

- **Odoo API changes**: Odoo API may change between versions, requiring updates to integration
- **Authentication complexity**: Odoo session management may be complex and require careful handling
- **Performance at scale**: Large invoice queries may be slow without proper pagination and caching
- **Approval workflow bottleneck**: Manual approval requirement may slow down high-volume operations
- **Data consistency**: Concurrent operations may cause race conditions without proper locking
- **Error recovery complexity**: Partial failures (e.g., invoice created but approval request failed) may require manual cleanup
