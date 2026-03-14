# Tasks: Gmail Watcher + Approval Workflow

**Input**: Design documents from `/specs/001-gmail-approval-workflow/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/, research.md, quickstart.md

**Tests**: TDD approach requested - tests written BEFORE implementation for each user story

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `watchers/`, `scripts/`, `tests/` at repository root
- Paths shown below use actual project structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Verify Python 3.10+ installation and virtual environment activation
- [x] T002 Install Silver tier dependencies: google-auth-oauthlib google-auth google-api-python-client watchdog python-dotenv pytest
- [x] T003 [P] Verify Gmail API credentials exist at credentials.json
- [x] T004 [P] Verify OAuth token exists at token.json (run test_gmail_oauth.py if missing)
- [x] T005 [P] Create .state directory in AI_Employee_Vault/ for persistent state files
- [x] T006 [P] Verify vault structure has all required folders (Inbox, Needs_Action, Pending_Approval, Approved, Rejected, Done, Plans, Logs)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Create tests/fixtures/ directory for test data and mocks
- [x] T008 [P] Create tests/fixtures/mock_gmail_api.py with Gmail API mock fixtures
- [x] T009 [P] Create tests/fixtures/sample_emails.json with test email data (urgent, normal, spam examples)
- [x] T010 [P] Create watchers/gmail_state.py with GmailState class skeleton (empty methods)
- [x] T011 [P] Update .env.example with Gmail configuration variables (GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH, GMAIL_CHECK_INTERVAL, PRIORITY_KEYWORDS)
- [x] T012 [P] Create AI_Employee_Vault/.state/gmail_watcher_state.json template with initial structure

**Constitution-Driven Tasks**:

- [x] T013 [P] Implement atomic file operations helper in watchers/gmail_state.py (move_file_atomic function)
- [x] T014 [P] Implement logging infrastructure in watchers/gmail_state.py (create_log_entry function for JSON Lines format)
- [x] T015 [P] Create environment variable loader in watchers/gmail_state.py (load_config function with validation)
- [x] T016 [P] Implement retry decorator with exponential backoff in watchers/gmail_state.py (retry_with_backoff decorator, max 3 attempts)
- [x] T017 [P] Create vault structure validator in watchers/gmail_state.py (validate_vault_structure function)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Email Detection and Action Creation (Priority: P1) 🎯 MVP

**Goal**: Gmail watcher detects important emails and creates action files in Needs_Action/ without duplicates

**Independent Test**: Send test email with "urgent" keyword → verify action file created in Needs_Action/ within 2 minutes → restart watcher → verify no duplicate created

### Tests for User Story 1 (TDD - Write FIRST, ensure FAIL) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T018 [P] [US1] Write test_gmail_state_initialization in tests/test_gmail_state.py (test state file creation, loading, saving)
- [x] T019 [P] [US1] Write test_gmail_state_idempotency in tests/test_gmail_state.py (test duplicate email ID detection)
- [x] T020 [P] [US1] Write test_gmail_watcher_authentication in tests/test_gmail_watcher.py (test OAuth token loading and refresh)
- [x] T021 [P] [US1] Write test_gmail_watcher_priority_detection in tests/test_gmail_watcher.py (test keyword matching for urgent emails)
- [x] T022 [P] [US1] Write test_gmail_watcher_action_file_creation in tests/test_gmail_watcher.py (test action file format and location)
- [x] T023 [P] [US1] Write test_gmail_watcher_restart_idempotency in tests/test_gmail_watcher.py (test no duplicates after restart)

### Implementation for User Story 1

- [x] T024 [P] [US1] Implement GmailState.__init__ in watchers/gmail_state.py (load state from JSON, initialize processed_email_ids set)
- [x] T025 [P] [US1] Implement GmailState.is_processed in watchers/gmail_state.py (check if email ID in processed set)
- [x] T026 [P] [US1] Implement GmailState.mark_processed in watchers/gmail_state.py (add email ID to set, save to JSON)
- [x] T027 [P] [US1] Implement GmailState.save in watchers/gmail_state.py (atomic write to state file)
- [x] T028 [US1] Create GmailWatcher class in watchers/gmail_watcher.py inheriting from BaseWatcher
- [x] T029 [US1] Implement GmailWatcher.authenticate in watchers/gmail_watcher.py (OAuth token loading, auto-refresh logic)
- [x] T030 [US1] Implement GmailWatcher._is_priority in watchers/gmail_watcher.py (keyword detection in subject/body)
- [x] T031 [US1] Implement GmailWatcher.check_for_updates in watchers/gmail_watcher.py (poll Gmail API, filter unread, detect priority)
- [x] T032 [US1] Implement GmailWatcher.create_action_file in watchers/gmail_watcher.py (create EMAIL_*.md in Needs_Action/)
- [x] T033 [US1] Implement GmailWatcher.run in watchers/gmail_watcher.py (main polling loop with configurable interval)
- [x] T034 [US1] Add error handling for expired OAuth token in watchers/gmail_watcher.py (pause, create alert, wait for refresh)
- [x] T035 [US1] Add logging for all watcher operations in watchers/gmail_watcher.py (email detected, action created, errors)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Human Approval Workflow (Priority: P2)

**Goal**: File-based approval workflow blocks sensitive actions until human approval

**Independent Test**: Create test action file → move to Pending_Approval → move to Approved → verify execution triggered → test rejection path

### Tests for User Story 2 (TDD - Write FIRST, ensure FAIL) ⚠️

- [x] T036 [P] [US2] Write test_approval_executor_folder_monitoring in tests/test_approval_executor.py (test watchdog detects file movements)
- [x] T037 [P] [US2] Write test_approval_executor_file_validation in tests/test_approval_executor.py (test approval file schema validation)
- [x] T038 [P] [US2] Write test_approval_executor_state_transitions in tests/test_approval_executor.py (test Pending → Approved → Done flow)
- [x] T039 [P] [US2] Write test_approval_executor_rejection_flow in tests/test_approval_executor.py (test Pending → Rejected → Done flow)
- [x] T040 [P] [US2] Write test_approval_executor_corrupted_file_handling in tests/test_approval_executor.py (test quarantine and alert creation)

### Implementation for User Story 2

- [x] T041 [P] [US2] Create ApprovalExecutor class in scripts/approval_executor.py with watchdog Observer setup
- [x] T042 [P] [US2] Implement ApprovalFileHandler in scripts/approval_executor.py (FileSystemEventHandler for file movements)
- [x] T043 [US2] Implement ApprovalExecutor.validate_approval_file in scripts/approval_executor.py (JSON schema validation against contracts/)
- [x] T044 [US2] Implement ApprovalExecutor.on_file_moved_to_approved in scripts/approval_executor.py (detect Approved/ movements)
- [x] T045 [US2] Implement ApprovalExecutor.on_file_moved_to_rejected in scripts/approval_executor.py (detect Rejected/ movements, skip execution)
- [x] T046 [US2] Implement ApprovalExecutor.handle_corrupted_file in scripts/approval_executor.py (move to quarantine, create alert)
- [x] T047 [US2] Implement ApprovalExecutor.run in scripts/approval_executor.py (start watchdog observer, monitor folders)
- [x] T048 [US2] Add logging for all approval workflow transitions in scripts/approval_executor.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Action Execution and Logging (Priority: P3)

**Goal**: Approved actions execute via MCP with complete audit logging

**Independent Test**: Create approved action → verify MCP execution → check log entry in Logs/YYYY-MM-DD.json → verify file moved to Done/

### Tests for User Story 3 (TDD - Write FIRST, ensure FAIL) ⚠️

- [x] T049 [P] [US3] Write test_action_executor_mcp_integration in tests/test_approval_executor.py (test MCP email send with mock)
- [x] T050 [P] [US3] Write test_action_executor_logging in tests/test_approval_executor.py (test log entry creation with all required fields)
- [x] T051 [P] [US3] Write test_action_executor_retry_logic in tests/test_approval_executor.py (test exponential backoff on failure)
- [x] T052 [P] [US3] Write test_action_executor_crash_recovery in tests/test_approval_executor.py (test resume incomplete actions on restart)
- [x] T053 [P] [US3] Write test_action_executor_rate_limit_handling in tests/test_approval_executor.py (test backoff on Gmail API rate limit)

### Implementation for User Story 3

- [x] T054 [P] [US3] Create ActionPlan class in scripts/approval_executor.py (generate Plan.md before MCP execution)
- [x] T055 [P] [US3] Implement ActionExecutor.create_plan in scripts/approval_executor.py (write Plan.md to Plans/ folder)
- [x] T056 [US3] Implement ActionExecutor.execute_approved_action in scripts/approval_executor.py (MCP integration for email send)
- [x] T057 [US3] Implement ActionExecutor.create_log_entry in scripts/approval_executor.py (JSON Lines format to Logs/YYYY-MM-DD.json)
- [x] T058 [US3] Implement ActionExecutor.move_to_done in scripts/approval_executor.py (atomic move to Done/ after execution)
- [x] T059 [US3] Add retry logic with exponential backoff in scripts/approval_executor.py (wrap MCP calls with retry decorator)
- [x] T060 [US3] Implement crash recovery in scripts/approval_executor.py (check Approved/ folder on startup, resume incomplete)
- [x] T061 [US3] Add rate limit detection in scripts/approval_executor.py (detect 429 errors, backoff, queue operations)
- [x] T062 [US3] Implement dry-run mode in scripts/approval_executor.py (check DRY_RUN env var, log intent without execution)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - System Resilience and Recovery (Priority: P4)

**Goal**: System handles errors gracefully and recovers from failures without data loss

**Independent Test**: Simulate network outage → verify queue and resume → simulate crash → verify recovery without duplicates

### Tests for User Story 4 (TDD - Write FIRST, ensure FAIL) ⚠️

- [x] T063 [P] [US4] Write test_watcher_network_outage_recovery in tests/test_resilience.py (test queue and resume on reconnect)
- [x] T064 [P] [US4] Write test_watcher_token_expiration_handling in tests/test_resilience.py (test pause, alert, resume after refresh)
- [x] T065 [P] [US4] Write test_watcher_vault_structure_recovery in tests/test_resilience.py (test recreate missing folders)
- [x] T066 [P] [US4] Write test_executor_consecutive_failures in tests/test_resilience.py (test error report after max retries)
- [x] T067 [P] [US4] Write test_state_persistence_across_restarts in tests/test_resilience.py (test state survives multiple restarts)

### Implementation for User Story 4

- [x] T068 [P] [US4] Implement network error detection in watchers/gmail_watcher.py (catch connection errors, queue operations)
- [x] T069 [P] [US4] Implement operation queue in watchers/gmail_state.py (persist pending operations to state file)
- [x] T070 [US4] Implement token expiration detection in watchers/gmail_watcher.py (check before API call, create alert, pause)
- [x] T071 [US4] Implement vault structure validation on startup in watchers/gmail_watcher.py (recreate missing folders, log recovery)
- [x] T072 [US4] Implement consecutive failure tracking in scripts/approval_executor.py (count failures, create error report after 3)
- [x] T073 [US4] Implement graceful shutdown handlers in watchers/gmail_watcher.py and scripts/approval_executor.py (save state on SIGTERM)
- [x] T074 [US4] Add comprehensive error logging in all modules (network, API, file system, validation errors)

**Checkpoint**: All user stories complete with production-grade resilience

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T075 [P] Update README.md with Silver tier setup instructions
- [x] T076 [P] Create quickstart script in scripts/start_silver_tier.sh (start watcher and executor with PM2)
- [x] T077 [P] Add comprehensive docstrings to all classes and methods
- [x] T078 [P] Run pytest with coverage report: `pytest --cov=watchers --cov=scripts tests/`
- [ ] T079 [P] Validate all action files against JSON schemas in contracts/
- [x] T080 [P] Create log rotation script in scripts/rotate_logs.sh (compress logs older than 7 days)
- [x] T081 [P] Add state file archival logic in watchers/gmail_state.py (trim processed_email_ids after 10,000 entries)
- [x] T082 Code cleanup and refactoring (remove debug prints, optimize imports)
- [x] T083 Run integration test: Send real test email → verify end-to-end flow → check logs
- [x] T084 Update CLAUDE.md with Silver tier implementation notes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 but integrates with it
- **User Story 3 (P3)**: Depends on US2 (needs approval workflow) - Cannot start until US2 complete
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Enhances all stories but independent

### Within Each User Story

- Tests (TDD) MUST be written and FAIL before implementation
- State management before watcher logic
- Watcher before executor
- Core implementation before error handling
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, and US4 can start in parallel (US3 depends on US2)
- All tests for a user story marked [P] can run in parallel
- Models/state management within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (TDD - write first):
Task: "Write test_gmail_state_initialization in tests/test_gmail_state.py"
Task: "Write test_gmail_state_idempotency in tests/test_gmail_state.py"
Task: "Write test_gmail_watcher_authentication in tests/test_gmail_watcher.py"
Task: "Write test_gmail_watcher_priority_detection in tests/test_gmail_watcher.py"

# After tests written and failing, launch parallel implementation:
Task: "Implement GmailState.__init__ in watchers/gmail_state.py"
Task: "Implement GmailState.is_processed in watchers/gmail_state.py"
Task: "Implement GmailState.mark_processed in watchers/gmail_state.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Email Detection)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Email Detection)
   - Developer B: User Story 2 (Approval Workflow)
   - Developer C: User Story 4 (Resilience)
3. After US2 complete, Developer B moves to US3 (Action Execution)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **TDD CRITICAL**: Verify tests fail before implementing (Red → Green → Refactor)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Constitution compliance verified in Foundational phase (T013-T017)
