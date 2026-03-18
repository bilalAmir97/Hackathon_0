---
id: 0001
title: odoo-mcp-server-specification
stage: spec
date: 2026-03-17
surface: agent
model: claude-sonnet-4-5
feature: 006-odoo-mcp-server
branch: 006-odoo-mcp-server
user: system
command: /sp.specify
labels: ["odoo", "mcp-server", "accounting", "invoicing", "json-rpc"]
links:
  spec: specs/006-odoo-mcp-server/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-odoo-mcp-server/spec.md
  - specs/006-odoo-mcp-server/checklists/requirements.md
tests:
  - N/A (specification phase)
---

## Prompt

Create Odoo MCP Server that provides Claude Code with tools to interact with Odoo accounting system. The server must implement JSON-RPC client to communicate with Odoo API and expose MCP tools for: (1) create_invoice - create customer invoices with line items, (2) record_payment - record payments against invoices, (3) list_invoices - query invoices with filters (date range, customer, status), (4) get_financial_report - retrieve financial summaries. All operations must integrate with existing approval workflow (require approval before finalizing invoices/payments), use error recovery decorators (retry + circuit breaker), and log all actions via audit system. Server must handle authentication, session management, and proper error responses.

## Response snapshot

Created comprehensive specification for Odoo MCP Server integration with the following structure:

**User Stories (Prioritized)**:
- P1 (MVP): Create Customer Invoices - Core accounting function with approval workflow
- P2: Record Payments Against Invoices - Complete invoice lifecycle
- P3: Query and List Invoices - Financial visibility and reporting
- P4: Retrieve Financial Reports - Business intelligence and analytics

**Requirements**:
- 20 Functional Requirements (FR-001 to FR-020) covering MCP tools, authentication, error recovery, and validation
- 10 Security & Approval Requirements (SR-001 to SR-010) covering human approval, audit logging, credential management, and data masking

**Key Decisions**:
- All invoice finalization and payment recording require human approval (no auto-posting)
- All financial amounts masked in audit logs for maximum security (SR-009)
- Error recovery decorators (retry + circuit breaker) integrated from 005-error-recovery
- Idempotent operations to prevent duplicate invoices/payments
- Session management with automatic renewal

**Success Criteria**: 12 measurable outcomes including performance targets (2-minute invoice creation, 3-second queries), reliability targets (99% uptime, 95% success rate), and user experience targets (80% self-service issue resolution)

**Validation**: Specification quality checklist created and all items pass. One clarification resolved (SR-009: mask all amounts for security). Ready for planning phase.

## Outcome

- ✅ Impact: Complete specification for critical financial integration - enables automated invoice creation and payment tracking via Claude Code
- 🧪 Tests: Specification includes 20 acceptance scenarios across 4 user stories, all independently testable
- 📁 Files: Created spec.md (206 lines) and requirements.md checklist
- 🔁 Next prompts: `/sp.plan` to design JSON-RPC client architecture and MCP tool implementation
- 🧠 Reflection: Specification successfully balances security (approval workflow, data masking) with usability (clear error messages, fast queries). MVP clearly identified as P1 invoice creation. All requirements testable and technology-agnostic.

## Evaluation notes (flywheel)

- Failure modes observed: None - specification process completed successfully with one clarification
- Graders run and results (PASS/FAIL): Specification quality checklist - ALL PASS
- Prompt variant (if applicable): Standard /sp.specify workflow
- Next experiment (smallest change to try): Proceed to /sp.plan for architecture design
