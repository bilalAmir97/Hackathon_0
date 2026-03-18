---
id: 0002
title: odoo-mcp-server-implementation-plan
stage: plan
date: 2026-03-17
surface: agent
model: claude-sonnet-4-5
feature: 006-odoo-mcp-server
branch: 006-odoo-mcp-server
user: system
command: /sp.plan
labels: ["odoo", "mcp-server", "accounting", "json-rpc", "planning", "approval-workflow"]
links:
  spec: specs/006-odoo-mcp-server/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-odoo-mcp-server/plan.md
  - specs/006-odoo-mcp-server/research.md
  - specs/006-odoo-mcp-server/data-model.md
  - specs/006-odoo-mcp-server/quickstart.md
  - specs/006-odoo-mcp-server/contracts/create_invoice.schema.json
  - specs/006-odoo-mcp-server/contracts/record_payment.schema.json
  - specs/006-odoo-mcp-server/contracts/list_invoices.schema.json
  - specs/006-odoo-mcp-server/contracts/get_financial_report.schema.json
  - CLAUDE.md (updated with Python 3.10+)
tests:
  - N/A (planning phase - no code implementation yet)
---

## Prompt

User requested to continue with `/sp.plan` after reviewing the current codebase architecture. The planning phase follows the completed specification phase (0001-odoo-mcp-server-specification.spec.prompt.md) which defined 4 prioritized user stories, 30 requirements, and 12 success criteria for the Odoo MCP Server integration.

The user first asked to review the codebase architecture before proceeding with planning, to understand existing patterns for MCP servers, error recovery, audit logging, and approval workflows.

## Response snapshot

Created comprehensive implementation plan for Odoo MCP Server following existing architecture patterns:

**Phase 0: Research & Technology Selection**
- Researched Odoo JSON-RPC API authentication and session management
- Selected `xmlrpc.client` (Python stdlib) for RPC communication
- Designed idempotency strategy using approval_id in invoice reference field
- Confirmed error recovery decorator integration (@with_retry, @with_circuit_breaker)
- Defined approval workflow integration pattern (following email MCP server)
- Designed financial data masking for audit logs (SR-009 requirement)

**Phase 1: Design & Contracts**
- Defined 6 core entities: Invoice, Payment, Customer, LineItem, ApprovalRequest, FinancialReport
- Created 4 MCP tool contracts with JSON schemas:
  - create_invoice: Requires approval, creates draft invoice
  - record_payment: Requires approval, validates amount ≤ outstanding balance
  - list_invoices: No approval (read-only), supports filters and pagination
  - get_financial_report: No approval (read-only), 3 report types
- Designed approval request format (Markdown with YAML frontmatter)
- Mapped Odoo models: account.move (invoices), account.payment (payments), res.partner (customers)

**Architecture Decisions**:
1. Separate client library (odoo_client.py) from MCP server (odoo_mcp_server.py)
2. Approval workflow for all financial operations (invoice finalization, payment recording)
3. Amount masking in audit logs (all financial amounts replaced with "***")
4. Idempotency via approval_id stored in Odoo reference field
5. Session management in memory (stateless server, re-authenticate on startup)

**Constitution Compliance**: All 10 principles satisfied - no violations identified

## Outcome

- ✅ Impact: Complete implementation plan for Gold Tier Odoo integration - enables automated invoice creation and payment tracking via Claude Code with human-in-the-loop approval
- 🧪 Tests: Planning phase complete - test strategy defined (unit tests for odoo_client.py, integration tests for MCP tools, end-to-end workflow tests)
- 📁 Files: Created plan.md (comprehensive architecture), research.md (6 research questions answered), data-model.md (6 entities defined), quickstart.md (usage guide), 4 JSON schema contracts
- 🔁 Next prompts: `/sp.tasks` to generate implementation tasks from this plan, then implement in sequence: odoo_client.py → odoo_mcp_server.py → approval integration → tests
- 🧠 Reflection: Planning successfully leveraged existing patterns (email MCP server, approval workflow, error recovery decorators, audit logging). Architecture mirrors proven email MCP implementation. All constitution principles satisfied through approval workflow, vault-based state, error recovery, and audit logging. Ready for task generation and implementation.

## Evaluation notes (flywheel)

- Failure modes observed: None - planning phase completed successfully with comprehensive research and design
- Graders run and results (PASS/FAIL): Constitution Check - ALL PASS (10/10 principles satisfied)
- Prompt variant (if applicable): Standard /sp.plan workflow with codebase architecture review first
- Next experiment (smallest change to try): Proceed to /sp.tasks for task generation, then implement odoo_client.py as first component
