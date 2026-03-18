# Implementation Tasks: Odoo MCP Server

**Feature**: 006-odoo-mcp-server
**Branch**: `006-odoo-mcp-server`
**Approach**: Test-Driven Development (TDD)
**Created**: 2026-03-17

## Overview

This document contains atomic, testable tasks for implementing the Odoo MCP Server. Tasks are organized by user story priority (P1-P4) following TDD methodology: write tests first (Red), implement to pass tests (Green), refactor if needed.

**Total Tasks**: 159
**Estimated Effort**: 10-13 hours (per Gold Tier roadmap)

---

## Task Organization

### Phase Structure

- **Phase 1**: Setup & Environment (T001-T010)
- **Phase 2**: Foundational Infrastructure (T011-T030)
- **Phase 3**: User Story 1 - Create Customer Invoices [P1 MVP] (T031-T065)
- **Phase 4**: User Story 2 - Record Payments [P2] (T066-T095)
- **Phase 5**: User Story 3 - Query Invoices [P3] (T096-T118)
- **Phase 6**: User Story 4 - Financial Reports [P4] (T119-T140)
- **Phase 7**: Polish & Cross-Cutting Concerns (T141-T159)

### Task Format

```
- [ ] [TaskID] [P?] [Story?] Description with file path
```

- **[P]**: Parallelizable (can run concurrently with other [P] tasks)
- **[Story]**: User story label ([US1], [US2], [US3], [US4])

---

## Phase 1: Setup & Environment

**Goal**: Initialize project structure, configure environment, install dependencies

**Duration**: ~30 minutes

### Tasks

- [X] T001 Update .env.example with Odoo credentials (ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
- [X] T002 Verify Odoo 17 Docker container is running and accessible at localhost:8069
- [X] T003 Verify Odoo Accounting module is installed via docker exec odoo odoo shell
- [X] T004 Create test customer in Odoo for integration tests via Odoo web interface
- [X] T005 Create test products in Odoo for invoice line items via Odoo web interface
- [X] T006 [P] Create mcp_servers/odoo_client.py skeleton file with OdooClient class stub
- [X] T007 [P] Create mcp_servers/odoo_mcp_server.py skeleton file with MCP server structure
- [X] T008 [P] Create tests/test_odoo_client.py with pytest fixtures for Odoo connection
- [X] T009 [P] Create tests/test_odoo_mcp_server.py with pytest fixtures for MCP server
- [X] T010 [P] Create tests/test_integration_odoo.py for end-to-end workflow tests

**Acceptance**: All skeleton files created, Odoo accessible, test data available

---

## Phase 2: Foundational Infrastructure

**Goal**: Implement shared utilities and base infrastructure needed by all user stories

**Duration**: ~1.5 hours

### Utility Functions

- [X] T011 [P] Write test for mask_financial_data() utility function in tests/test_odoo_client.py
- [X] T012 [P] Implement mask_financial_data() utility in mcp_servers/odoo_client.py to replace amounts with "***"
- [X] T013 [P] Write test for generate_approval_id() utility function in tests/test_odoo_client.py
- [X] T014 [P] Implement generate_approval_id() utility in mcp_servers/odoo_client.py (format: approval_YYYYMMDD_HHMMSS_type)

### Odoo Client - Authentication

- [X] T015 Write test_authenticate_success() in tests/test_odoo_client.py
- [X] T016 Write test_authenticate_failure_invalid_credentials() in tests/test_odoo_client.py
- [X] T017 Write test_authenticate_with_retry_on_network_error() in tests/test_odoo_client.py
- [X] T018 Implement OdooClient.__init__() with environment variable loading in mcp_servers/odoo_client.py
- [X] T019 Implement OdooClient.authenticate() with xmlrpc.client in mcp_servers/odoo_client.py
- [X] T020 Apply @with_retry decorator to OdooClient.authenticate() in mcp_servers/odoo_client.py
- [X] T021 Apply @with_circuit_breaker decorator to OdooClient.authenticate() in mcp_servers/odoo_client.py
- [X] T022 Run tests: pytest tests/test_odoo_client.py::test_authenticate* -v

### Odoo Client - Session Management

- [X] T023 Write test_session_renewal_on_expiration() in tests/test_odoo_client.py
- [X] T024 Write test_session_reuse_across_calls() in tests/test_odoo_client.py
- [X] T025 Implement OdooClient._ensure_authenticated() helper method in mcp_servers/odoo_client.py
- [X] T026 Implement session UID storage and reuse in OdooClient in mcp_servers/odoo_client.py
- [X] T027 Run tests: pytest tests/test_odoo_client.py::test_session* -v

### Approval Request Generation

- [X] T028 Write test for create_approval_request_file() utility in tests/test_odoo_client.py
- [X] T029 Implement create_approval_request_file() in mcp_servers/odoo_client.py (Markdown with YAML frontmatter)
- [X] T030 Run tests: pytest tests/test_odoo_client.py -v (all foundational tests)

**Acceptance**: Authentication works, session management functional, utilities tested

---

## Phase 3: User Story 1 - Create Customer Invoices [P1 MVP] 🎯

**Goal**: Enable invoice creation via MCP tool with approval workflow

**Duration**: ~3 hours

**Independent Test**: Create draft invoice → approve → verify in Odoo

### Odoo Client - Invoice Creation (TDD)

- [X] T031 [US1] Write test_create_draft_invoice_success() in tests/test_odoo_client.py
- [X] T032 [US1] Write test_create_draft_invoice_invalid_customer() in tests/test_odoo_client.py
- [X] T033 [US1] Write test_create_draft_invoice_invalid_product() in tests/test_odoo_client.py
- [X] T034 [US1] Write test_create_draft_invoice_with_multiple_line_items() in tests/test_odoo_client.py
- [X] T035 [US1] Write test_create_draft_invoice_idempotency() in tests/test_odoo_client.py
- [X] T036 [US1] Implement OdooClient.create_draft_invoice() in mcp_servers/odoo_client.py
- [X] T037 [US1] Implement customer validation in OdooClient.create_draft_invoice()
- [X] T038 [US1] Implement product validation in OdooClient.create_draft_invoice()
- [X] T039 [US1] Implement line item creation in OdooClient.create_draft_invoice()
- [X] T040 [US1] Implement idempotency check (search by approval_id in ref field) in OdooClient.create_draft_invoice()
- [X] T041 [US1] Apply @with_retry and @with_circuit_breaker decorators to create_draft_invoice()
- [X] T042 [US1] Run tests: pytest tests/test_odoo_client.py::test_create_draft_invoice* -v

### Odoo Client - Invoice Finalization (TDD)

- [X] T043 [US1] Write test_finalize_invoice_success() in tests/test_odoo_client.py
- [X] T044 [US1] Write test_finalize_invoice_not_found() in tests/test_odoo_client.py
- [X] T045 [US1] Write test_finalize_invoice_already_posted() in tests/test_odoo_client.py
- [X] T046 [US1] Implement OdooClient.finalize_invoice() to post invoice in mcp_servers/odoo_client.py
- [X] T047 [US1] Apply @with_retry and @with_circuit_breaker decorators to finalize_invoice()
- [X] T048 [US1] Run tests: pytest tests/test_odoo_client.py::test_finalize_invoice* -v

### MCP Server - create_invoice Tool (TDD)

- [X] T049 [US1] Write test_create_invoice_tool_success() in tests/test_odoo_mcp_server.py
- [X] T050 [US1] Write test_create_invoice_tool_validation_errors() in tests/test_odoo_mcp_server.py
- [X] T051 [US1] Write test_create_invoice_tool_approval_file_created() in tests/test_odoo_mcp_server.py
- [X] T052 [US1] Implement @app.list_tools() in mcp_servers/odoo_mcp_server.py with create_invoice tool definition
- [X] T053 [US1] Implement create_invoice() handler in mcp_servers/odoo_mcp_server.py
- [X] T054 [US1] Implement input validation in create_invoice() handler
- [X] T055 [US1] Integrate OdooClient.create_draft_invoice() in create_invoice() handler
- [X] T056 [US1] Implement approval request generation in create_invoice() handler
- [X] T057 [US1] Implement audit logging with amount masking in create_invoice() handler
- [X] T058 [US1] Run tests: pytest tests/test_odoo_mcp_server.py::test_create_invoice* -v

### Approval Workflow Integration (TDD)

- [X] T059 [US1] Write test_execute_invoice_finalize() in tests/test_approval_executor.py
- [X] T060 [US1] Implement execute_invoice_finalize() in scripts/approval_executor.py
- [X] T061 [US1] Update on_file_moved_to_approved() to handle invoice_finalize action type
- [X] T062 [US1] Run tests: pytest tests/test_approval_executor.py::test_execute_invoice_finalize -v

### End-to-End Workflow Test

- [X] T063 [US1] Write test_invoice_creation_workflow_e2e() in tests/test_integration_odoo.py
- [X] T064 [US1] Run test: pytest tests/test_integration_odoo.py::test_invoice_creation_workflow_e2e -v
- [X] T065 [US1] Manual test: Create invoice via MCP tool, approve, verify in Odoo web interface

**Acceptance**: Invoice creation works end-to-end with approval workflow, all tests pass ✅

---

## Phase 4: User Story 2 - Record Payments [P2]

**Goal**: Enable payment recording via MCP tool with approval workflow

**Duration**: ~2 hours

**Independent Test**: Create invoice → record payment → approve → verify in Odoo

### Odoo Client - Payment Recording (TDD)

- [X] T066 [US2] Write test_record_payment_success() in tests/test_odoo_client.py
- [X] T067 [US2] Write test_record_payment_invoice_not_found() in tests/test_odoo_client.py
- [X] T068 [US2] Write test_record_payment_invoice_not_posted() in tests/test_odoo_client.py
- [X] T069 [US2] Write test_record_payment_amount_exceeds_balance() in tests/test_odoo_client.py
- [X] T070 [US2] Write test_record_payment_partial_payment() in tests/test_odoo_client.py
- [X] T071 [US2] Write test_record_payment_idempotency() in tests/test_odoo_client.py
- [X] T072 [US2] Implement OdooClient.get_invoice_details() in mcp_servers/odoo_client.py
- [X] T073 [US2] Implement OdooClient.record_payment() in mcp_servers/odoo_client.py
- [X] T074 [US2] Implement invoice validation (exists, posted) in record_payment()
- [X] T075 [US2] Implement amount validation (≤ outstanding balance) in record_payment()
- [X] T076 [US2] Implement idempotency check in record_payment()
- [X] T077 [US2] Apply @with_retry and @with_circuit_breaker decorators to record_payment()
- [X] T078 [US2] Run tests: pytest tests/test_odoo_client.py::test_record_payment* -v

### MCP Server - record_payment Tool (TDD)

- [X] T079 [US2] Write test_record_payment_tool_success() in tests/test_odoo_mcp_server.py
- [X] T080 [US2] Write test_record_payment_tool_validation_errors() in tests/test_odoo_mcp_server.py
- [X] T081 [US2] Write test_record_payment_tool_approval_file_created() in tests/test_odoo_mcp_server.py
- [X] T082 [US2] Add record_payment tool definition to @app.list_tools() in mcp_servers/odoo_mcp_server.py
- [X] T083 [US2] Implement record_payment() handler in mcp_servers/odoo_mcp_server.py
- [X] T084 [US2] Implement input validation in record_payment() handler
- [X] T085 [US2] Integrate OdooClient.record_payment() in record_payment() handler
- [X] T086 [US2] Implement approval request generation in record_payment() handler
- [X] T087 [US2] Implement audit logging with amount masking in record_payment() handler
- [X] T088 [US2] Run tests: pytest tests/test_odoo_mcp_server.py::test_record_payment* -v

### Approval Workflow Integration (TDD)

- [X] T089 [US2] Write test_execute_payment_record() in tests/test_approval_executor.py
- [X] T090 [US2] Implement execute_payment_record() in scripts/approval_executor.py
- [X] T091 [US2] Update on_file_moved_to_approved() to handle payment_record action type
- [X] T092 [US2] Run tests: pytest tests/test_approval_executor.py::test_execute_payment_record -v

### End-to-End Workflow Test

- [X] T093 [US2] Write test_payment_recording_workflow_e2e() in tests/test_integration_odoo.py
- [X] T094 [US2] Run test: pytest tests/test_integration_odoo.py::test_payment_recording_workflow_e2e -v
- [X] T095 [US2] Manual test: Record payment via MCP tool, approve, verify in Odoo

**Acceptance**: Payment recording works end-to-end with approval workflow, all tests pass

---

## Phase 5: User Story 3 - Query Invoices [P3]

**Goal**: Enable invoice querying via MCP tool (no approval required)

**Duration**: ~1.5 hours

**Independent Test**: Create invoices with different filters → query → verify results

### Odoo Client - Invoice Querying (TDD)

- [X] T096 [US3] Write test_search_invoices_no_filters() in tests/test_odoo_client.py
- [X] T097 [US3] Write test_search_invoices_by_date_range() in tests/test_odoo_client.py
- [X] T098 [US3] Write test_search_invoices_by_customer() in tests/test_odoo_client.py
- [X] T099 [US3] Write test_search_invoices_by_status() in tests/test_odoo_client.py
- [X] T100 [US3] Write test_search_invoices_pagination() in tests/test_odoo_client.py
- [X] T101 [US3] Write test_search_invoices_empty_results() in tests/test_odoo_client.py
- [X] T102 [US3] Implement OdooClient.search_invoices() in mcp_servers/odoo_client.py
- [X] T103 [US3] Implement Odoo domain filter building in search_invoices()
- [X] T104 [US3] Implement pagination (limit, offset) in search_invoices()
- [X] T105 [US3] Apply @with_retry and @with_circuit_breaker decorators to search_invoices()
- [X] T106 [US3] Run tests: pytest tests/test_odoo_client.py::test_search_invoices* -v

### MCP Server - list_invoices Tool (TDD)

- [X] T107 [US3] Write test_list_invoices_tool_success() in tests/test_odoo_mcp_server.py
- [X] T108 [US3] Write test_list_invoices_tool_with_filters() in tests/test_odoo_mcp_server.py
- [X] T109 [US3] Write test_list_invoices_tool_amount_masking() in tests/test_odoo_mcp_server.py
- [X] T110 [US3] Add list_invoices tool definition to @app.list_tools() in mcp_servers/odoo_mcp_server.py
- [X] T111 [US3] Implement list_invoices() handler in mcp_servers/odoo_mcp_server.py
- [X] T112 [US3] Integrate OdooClient.search_invoices() in list_invoices() handler
- [X] T113 [US3] Implement amount masking in list_invoices() response
- [X] T114 [US3] Implement audit logging in list_invoices() handler
- [X] T115 [US3] Run tests: pytest tests/test_odoo_mcp_server.py::test_list_invoices* -v

### End-to-End Query Test

- [X] T116 [US3] Write test_invoice_query_workflow_e2e() in tests/test_integration_odoo.py
- [X] T117 [US3] Run test: pytest tests/test_integration_odoo.py::test_invoice_query_workflow_e2e -v
- [X] T118 [US3] Manual test: Query invoices with various filters via MCP tool

**Acceptance**: Invoice querying works with all filters, amounts masked, all tests pass

---

## Phase 6: User Story 4 - Financial Reports [P4]

**Goal**: Enable financial report generation via MCP tool (no approval required)

**Duration**: ~1.5 hours

**Independent Test**: Create invoices/payments → generate reports → verify calculations

### Odoo Client - Financial Reporting (TDD)

- [X] T119 [US4] Write test_get_revenue_summary() in tests/test_odoo_client.py
- [X] T120 [US4] Write test_get_receivables_report() in tests/test_odoo_client.py
- [X] T121 [US4] Write test_get_payment_collection_metrics() in tests/test_odoo_client.py
- [X] T122 [US4] Write test_financial_report_empty_period() in tests/test_odoo_client.py
- [X] T123 [US4] Implement OdooClient.get_financial_report() in mcp_servers/odoo_client.py
- [X] T124 [US4] Implement revenue_summary report type in get_financial_report()
- [X] T125 [US4] Implement receivables report type in get_financial_report()
- [X] T126 [US4] Implement payment_collection report type in get_financial_report()
- [X] T127 [US4] Apply @with_retry and @with_circuit_breaker decorators to get_financial_report()
- [X] T128 [US4] Run tests: pytest tests/test_odoo_client.py::test_get_*_report* -v

### MCP Server - get_financial_report Tool (TDD)

- [X] T129 [US4] Write test_get_financial_report_tool_success() in tests/test_odoo_mcp_server.py
- [X] T130 [US4] Write test_get_financial_report_tool_all_types() in tests/test_odoo_mcp_server.py
- [X] T131 [US4] Write test_get_financial_report_tool_amount_masking() in tests/test_odoo_mcp_server.py
- [X] T132 [US4] Add get_financial_report tool definition to @app.list_tools() in mcp_servers/odoo_mcp_server.py
- [X] T133 [US4] Implement get_financial_report() handler in mcp_servers/odoo_mcp_server.py
- [X] T134 [US4] Integrate OdooClient.get_financial_report() in handler
- [X] T135 [US4] Implement amount masking in get_financial_report() response
- [X] T136 [US4] Implement audit logging in get_financial_report() handler
- [X] T137 [US4] Run tests: pytest tests/test_odoo_mcp_server.py::test_get_financial_report* -v

### End-to-End Report Test

- [X] T138 [US4] Write test_financial_report_workflow_e2e() in tests/test_integration_odoo.py
- [X] T139 [US4] Run test: pytest tests/test_integration_odoo.py::test_financial_report_workflow_e2e -v
- [X] T140 [US4] Manual test: Generate all report types via MCP tool

**Acceptance**: Financial reports generate correctly, amounts masked, all tests pass

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Error handling, documentation, performance optimization

**Duration**: ~1 hour

### Error Handling & Edge Cases

- [X] T141 [P] Write test_circuit_breaker_opens_on_odoo_failure() in tests/test_odoo_client.py
- [X] T142 [P] Write test_retry_on_network_timeout() in tests/test_odoo_client.py
- [X] T143 [P] Write test_session_renewal_on_401_error() in tests/test_odoo_client.py
- [X] T144 [P] Write test_concurrent_invoice_creation() in tests/test_integration_odoo.py
- [X] T145 Run all error handling tests: pytest tests/ -k "circuit_breaker or retry or session_renewal" -v

### Documentation

- [X] T146 [P] Update specs/006-odoo-mcp-server/quickstart.md with real code examples
- [X] T147 [P] Add docstrings to all OdooClient methods in mcp_servers/odoo_client.py
- [X] T148 [P] Add docstrings to all MCP tool handlers in mcp_servers/odoo_mcp_server.py
- [X] T149 [P] Create README.md in mcp_servers/ with Odoo MCP server usage

### Performance & Optimization

- [X] T150 Verify invoice creation completes in <2 minutes (SC-001)
- [X] T151 Verify invoice queries return in <3 seconds for 100 results (SC-005)
- [X] T152 Verify payment recording completes in <30 seconds (SC-004)
- [X] T153 Verify financial reports generate in <10 seconds (SC-009)

### Final Validation

- [X] T154 Run full test suite: pytest tests/ -v --cov=mcp_servers --cov=scripts
- [X] T155 Verify test coverage ≥90% for odoo_client.py and odoo_mcp_server.py
- [X] T156 Run integration tests against real Odoo instance
- [X] T157 Verify all audit logs contain masked amounts (grep for "***" in logs)
- [X] T158 Verify approval workflow works for all financial operations
- [X] T159 Update CLAUDE.md with Odoo MCP server information

**Acceptance**: All tests pass, documentation complete, performance targets met

---

## Dependencies & Execution Order

### Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational)
                      ↓
    ┌─────────────────┴─────────────────┐
    ↓                                   ↓
Phase 3 (US1 - Invoices)          Phase 5 (US3 - Query)
    ↓                                   ↓
Phase 4 (US2 - Payments)          Phase 6 (US4 - Reports)
    ↓                                   ↓
    └─────────────────┬─────────────────┘
                      ↓
              Phase 7 (Polish)
```

**Critical Path**: Phase 1 → Phase 2 → Phase 3 (US1) → Phase 4 (US2) → Phase 7

**Parallel Opportunities**:
- US3 (Query) and US4 (Reports) can be implemented in parallel after Phase 2
- US3 and US4 are independent of US1 and US2
- Documentation tasks (T146-T149) can be done in parallel with testing

### Blocking Tasks

- **T001-T010** (Setup): Must complete before any implementation
- **T011-T030** (Foundational): Must complete before any user story
- **T031-T065** (US1): Must complete before US2 (payments depend on invoices)
- **T066-T095** (US2): Depends on US1 completion

### Parallelizable Tasks

Within each phase, tasks marked with **[P]** can run concurrently:
- Setup: T006-T010 (file creation)
- Foundational: T011-T014 (utility functions)
- US1: Test writing tasks can be done in parallel
- US2: Test writing tasks can be done in parallel
- US3: Test writing tasks can be done in parallel
- US4: Test writing tasks can be done in parallel
- Polish: T141-T144, T146-T149 (documentation)

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Phase 3 (User Story 1) ONLY** - Create Customer Invoices

This delivers immediate business value:
- Create invoices via Claude Code
- Approval workflow integration
- Audit logging
- Error recovery

**Estimated MVP Time**: ~5 hours (Setup + Foundational + US1)

### Incremental Delivery

1. **Week 1**: MVP (US1 - Invoice Creation)
2. **Week 2**: US2 (Payment Recording)
3. **Week 3**: US3 (Query) + US4 (Reports) in parallel
4. **Week 4**: Polish, optimization, documentation

### Testing Strategy

**TDD Workflow** (for each user story):
1. Write all tests first (Red phase)
2. Run tests - they should fail
3. Implement minimum code to pass tests (Green phase)
4. Refactor if needed
5. Verify all tests pass

**Test Coverage Targets**:
- Unit tests: ≥90% coverage for odoo_client.py
- Integration tests: ≥80% coverage for odoo_mcp_server.py
- E2E tests: All user story acceptance scenarios covered

---

## Success Metrics

### Test Coverage

- [ ] Unit test coverage ≥90% for OdooClient
- [ ] Integration test coverage ≥80% for MCP server
- [ ] All 20 acceptance scenarios from spec.md have tests
- [ ] All edge cases from spec.md have tests

### Performance

- [ ] Invoice creation: <2 minutes (SC-001)
- [ ] Invoice queries: <3 seconds for 100 results (SC-005)
- [ ] Payment recording: <30 seconds (SC-004)
- [ ] Financial reports: <10 seconds (SC-009)

### Quality

- [ ] All tests pass: pytest tests/ -v
- [ ] No linting errors: pylint mcp_servers/odoo*.py
- [ ] Type hints added: mypy mcp_servers/odoo*.py
- [ ] Documentation complete: All public methods have docstrings

### Compliance

- [ ] All financial amounts masked in audit logs (SR-009)
- [ ] All operations require approval (SR-001, SR-002)
- [ ] Idempotency enforced (SR-006, SR-007)
- [ ] Error recovery decorators applied (FR-015, FR-016)

---

## Notes

- **TDD Discipline**: Write tests BEFORE implementation for every component
- **Atomic Tasks**: Each task should take 10-30 minutes maximum
- **Test First**: Run tests after each implementation to verify correctness
- **Incremental**: Commit after each passing test phase
- **Documentation**: Update as you go, not at the end

**Ready for implementation**: All tasks defined, dependencies clear, MVP identified
