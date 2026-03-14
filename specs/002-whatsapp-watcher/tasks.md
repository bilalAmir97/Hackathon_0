---
description: "Task breakdown for WhatsApp Watcher implementation (TDD approach)"
---

# Tasks: WhatsApp Watcher (Sensor Layer)

**Input**: Design documents from `/specs/002-whatsapp-watcher/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/
**Approach**: Test-Driven Development (TDD) - Write failing tests first, then implement to make them pass

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Watchers**: `watchers/` at repository root
- **Tests**: `tests/` at repository root
- **Vault**: `AI_Employee_Vault/` at repository root
- **Scripts**: `scripts/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and environment setup

- [ ] T001 Install Playwright browsers with command: `uv run playwright install chromium`
- [X] T002 [P] Update .gitignore to exclude .whatsapp_session/ directory
- [ ] T003 [P] Verify AI_Employee_Vault/.state/ directory exists and is writable
- [ ] T004 [P] Verify pyproject.toml includes playwright>=1.40.0 dependency

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundation (TDD - Write these FIRST)

- [X] T005 [P] Create test fixture for mock WhatsApp Web page in tests/fixtures/mock_whatsapp_web.py (mock elements: unread chat list with data-testid="chat-list", message elements with sender/text/timestamp, QR code screen, login state indicator)
- [X] T006 [P] Create test for state file initialization in tests/test_whatsapp_watcher.py (test_state_initialization)
- [X] T007 [P] Create test for composite message ID generation in tests/test_whatsapp_watcher.py (test_message_id_generation)
- [X] T008 [P] Create test for filename sanitization in tests/test_whatsapp_watcher.py (test_sanitize_sender_name)

### Foundation Implementation

- [X] T009 Create WhatsAppWatcher class skeleton in watchers/whatsapp_watcher.py with __init__ method
- [X] T010 [P] Adapt GmailState class for WhatsApp in watchers/whatsapp_watcher.py (reuse GmailState pattern with WhatsApp-specific message ID format: sender_timestamp_preview)
- [X] T011 [P] Implement _generate_message_id() method (sender + timestamp + preview[:50])
- [X] T012 [P] Implement _sanitize_sender_name() method (filesystem-safe names)
- [X] T013 Implement _load_state() and _save_state() methods using JSON file in AI_Employee_Vault/.state/
- [X] T014 [P] Implement _create_log_entry() method for JSON Lines logging to AI_Employee_Vault/Logs/
- [X] T015 Add default priority keywords configuration (urgent, asap, important, help, invoice, payment, emergency, critical, deadline)

**Checkpoint**: Foundation ready - verify all foundation tests pass before proceeding to user stories

---

## Phase 3: User Story 1 - Priority Message Detection (Priority: P1) 🎯 MVP

**Goal**: Automatically detect important WhatsApp messages and create action files for human review

**Independent Test**: Send WhatsApp message with "urgent" keyword → Verify action file created in /Needs_Action within 60 seconds

### Tests for User Story 1 (TDD - Write these FIRST, ensure they FAIL)

- [X] T016 [P] [US1] Create test for Playwright browser launch in tests/test_whatsapp_watcher.py (test_browser_launch_with_persistent_context)
- [X] T017 [P] [US1] Create test for WhatsApp Web navigation in tests/test_whatsapp_watcher.py (test_navigate_to_whatsapp_web)
- [X] T018 [P] [US1] Create test for unread chat detection in tests/test_whatsapp_watcher.py (test_scan_unread_chats)
- [X] T019 [P] [US1] Create test for keyword matching in tests/test_whatsapp_watcher.py (test_is_priority_message)
- [X] T020 [P] [US1] Create test for action file creation in tests/test_whatsapp_watcher.py (test_create_action_file)
- [X] T021 [P] [US1] Create test for YAML frontmatter validation in tests/test_whatsapp_watcher.py (test_action_file_yaml_format)

### Implementation for User Story 1

- [X] T022 [US1] Implement _launch_browser() method with Playwright persistent_context in watchers/whatsapp_watcher.py
- [X] T023 [US1] Implement _navigate_to_whatsapp_web() method with URL navigation and wait conditions
- [X] T024 [US1] Implement _wait_for_login() method to detect QR code or logged-in state
- [X] T025 [US1] Implement _scan_unread_chats() method using DOM selectors (data-testid with fallbacks)
- [X] T026 [US1] Implement _extract_message_data() method to parse sender, text, timestamp from chat elements
- [X] T027 [US1] Implement _is_priority_message() method for case-insensitive keyword matching
- [X] T028 [US1] Implement _create_action_file() method with YAML frontmatter and markdown body
- [X] T029 [US1] Implement _write_action_file_atomic() method to write to AI_Employee_Vault/Needs_Action/
- [X] T030 [US1] Implement check_for_updates() main loop method that orchestrates detection flow
- [X] T031 [US1] Add logging for all detection events (message found, keyword matched, file created)

**Checkpoint**: Run all US1 tests - they should now PASS. Manual test: Send priority message and verify action file created.

---

## Phase 4: User Story 2 - Restart-Safe Operation (Priority: P2)

**Goal**: Remember processed messages to prevent duplicate action files across restarts

**Independent Test**: Process priority message → Restart watcher → Verify no duplicate action file created

### Tests for User Story 2 (TDD - Write these FIRST, ensure they FAIL)

- [X] T032 [P] [US2] Create test for duplicate detection in tests/test_whatsapp_watcher.py (test_duplicate_message_detection)
- [X] T033 [P] [US2] Create test for state persistence across restarts in tests/test_whatsapp_watcher.py (test_state_persists_after_restart)
- [X] T034 [P] [US2] Create test for corrupted state file recovery in tests/test_whatsapp_watcher.py (test_corrupted_state_recovery)
- [X] T035 [P] [US2] Create test for large backlog processing in tests/test_whatsapp_watcher.py (test_process_large_backlog_once)

### Implementation for User Story 2

- [X] T036 [US2] Implement _is_processed() method to check message ID against state.processed_ids
- [X] T037 [US2] Implement _mark_processed() method to add message ID to state and save
- [X] T038 [US2] Add deduplication check in check_for_updates() before creating action files
- [X] T039 [US2] Implement state file corruption handling with try/except and fresh state initialization
- [X] T040 [US2] Add state.total_messages_processed counter and increment on each new message
- [X] T041 [US2] Add logging for duplicate detection (message already processed, skipping)

**Checkpoint**: Run all US2 tests - they should now PASS. Manual test: Process message, restart, verify no duplicate.

---

## Phase 5: User Story 3 - Automatic Failure Recovery (Priority: P3)

**Goal**: Automatically recover from network issues and WhatsApp Web glitches without manual intervention

**Independent Test**: Simulate network interruption → Verify watcher retries and recovers without crashing

### Tests for User Story 3 (TDD - Write these FIRST, ensure they FAIL)

- [X] T042 [P] [US3] Create test for exponential backoff retry in tests/test_whatsapp_watcher.py (test_retry_with_exponential_backoff)
- [X] T043 [P] [US3] Create test for network timeout handling in tests/test_whatsapp_watcher.py (test_network_timeout_recovery)
- [X] T044 [P] [US3] Create test for session expiration detection in tests/test_whatsapp_watcher.py (test_session_expired_alert)
- [X] T045 [P] [US3] Create test for DOM selector fallback in tests/test_whatsapp_watcher.py (test_dom_selector_fallback)
- [X] T046 [P] [US3] Create test for graceful shutdown in tests/test_whatsapp_watcher.py (test_graceful_shutdown_saves_state)

### Implementation for User Story 3

- [X] T047 [US3] Implement _retry_with_backoff() decorator for transient failure handling (1s, 2s, 4s delays)
- [X] T048 [US3] Add @_retry_with_backoff to _navigate_to_whatsapp_web() and _scan_unread_chats() methods
- [X] T049 [US3] Implement _detect_session_expired() method to check for QR code/login screen
- [X] T050 [US3] Implement _create_session_expired_alert() to write alert file to AI_Employee_Vault/Needs_Action/
- [X] T051 [US3] Add DOM selector fallback logic in _scan_unread_chats() (data-testid → class selectors)
- [X] T052 [US3] Implement signal handlers for SIGTERM and SIGINT to trigger graceful shutdown
- [X] T053 [US3] Implement _shutdown() method to save state, close browser, and log shutdown event
- [X] T054 [US3] Add error logging with detailed context (failing selector, error type, retry attempt)

**Checkpoint**: Run all US3 tests - they should now PASS. Manual test: Kill network, verify retry and recovery.

---

## Phase 6: User Story 4 - Testing and Validation Mode (Priority: P4)

**Goal**: Provide dry-run mode for testing detection logic without creating actual action files

**Independent Test**: Run watcher in dry-run mode with priority messages → Verify detection logged but no files created

### Tests for User Story 4 (TDD - Write these FIRST, ensure they FAIL)

- [X] T055 [P] [US4] Create test for dry-run mode initialization in tests/test_whatsapp_watcher.py (test_dry_run_mode_enabled)
- [X] T056 [P] [US4] Create test for dry-run detection logging in tests/test_whatsapp_watcher.py (test_dry_run_logs_without_files)
- [X] T057 [P] [US4] Create test for dry-run to production mode switch in tests/test_whatsapp_watcher.py (test_disable_dry_run_creates_files)

### Implementation for User Story 4

- [X] T058 [US4] Add dry_run parameter to WhatsAppWatcher.__init__() method (default: False)
- [X] T059 [US4] Add DRY_RUN environment variable support in __init__() method
- [X] T060 [US4] Modify _create_action_file() to skip file write when dry_run=True
- [X] T061 [US4] Add detailed dry-run logging (would create file: WHATSAPP_..., sender: ..., keyword: ...)
- [X] T062 [US4] Add dry-run mode indicator to startup banner output

**Checkpoint**: Run all US4 tests - they should now PASS. Manual test: Run with DRY_RUN=true, verify logs but no files.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Integration, documentation, and production readiness

- [ ] T063 [P] Add comprehensive docstrings to all methods in watchers/whatsapp_watcher.py
- [ ] T064 [P] Create __main__ block with argument parsing (--dry-run, --keywords, --interval flags)
- [ ] T065 [P] Add startup banner with configuration display (vault path, keywords, interval, dry-run status)
- [ ] T066 Update scripts/start_silver_tier.sh to include WhatsApp watcher PM2 configuration (process name: "whatsapp-watcher", interpreter: "python3", restart: "always", log paths: AI_Employee_Vault/Logs/)
- [ ] T067 [P] Create integration test script in tests/test_whatsapp_integration.py for end-to-end workflow
- [ ] T068 [P] Add performance logging (check cycle duration, memory usage, message count)
- [ ] T069 Run full test suite with pytest and verify 100% pass rate
- [ ] T070 Perform manual 24-hour stability test with real WhatsApp account
- [ ] T071 [P] Update specs/002-whatsapp-watcher/quickstart.md with actual implementation details
- [ ] T072 Create example action file in specs/002-whatsapp-watcher/examples/ for reference
- [ ] T073 [P] Add validation test in tests/test_whatsapp_watcher.py that logs contain only metadata (sender, timestamp) not message content (SR-006 compliance)
- [ ] T074 [US3] Implement rate limit detection and polling interval adjustment in watchers/whatsapp_watcher.py (RR-007 compliance)
- [ ] T075 [P] Create performance test in tests/test_whatsapp_watcher.py for 100-message backlog processing (target: <5 minutes, SC-006 validation)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (P1) can start after Foundational - No dependencies on other stories
  - US2 (P2) depends on US1 (needs detection logic to test deduplication)
  - US3 (P3) depends on US1 (needs core logic to add error handling)
  - US4 (P4) depends on US1 (needs action file creation to test dry-run)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (builds on detection logic)
- **User Story 3 (P3)**: Depends on US1 completion (adds error handling to existing logic)
- **User Story 4 (P4)**: Depends on US1 completion (adds mode flag to existing logic)

### Within Each User Story (TDD Approach)

1. **Write Tests FIRST** - All test tasks for the story
2. **Run Tests** - Verify they FAIL (Red phase)
3. **Implement Code** - Write minimal code to make tests pass
4. **Run Tests Again** - Verify they PASS (Green phase)
5. **Refactor** - Clean up code while keeping tests passing
6. **Checkpoint** - Validate story independently before moving to next

### Parallel Opportunities

- **Phase 1 (Setup)**: All tasks marked [P] can run in parallel
- **Phase 2 (Foundation)**: Test tasks (T005-T008) can run in parallel, then implementation tasks (T010-T012, T014-T015) can run in parallel
- **Within Each User Story**: All test tasks marked [P] can be written in parallel
- **User Stories**: After US1 is complete, US2, US3, US4 can be worked on in parallel by different developers (though sequential is recommended for single developer)

---

## Parallel Example: User Story 1

```bash
# Step 1: Write all tests for US1 in parallel (Red phase)
Task T016: "Create test for Playwright browser launch"
Task T017: "Create test for WhatsApp Web navigation"
Task T018: "Create test for unread chat detection"
Task T019: "Create test for keyword matching"
Task T020: "Create test for action file creation"
Task T021: "Create test for YAML frontmatter validation"

# Step 2: Run tests - they should all FAIL
pytest tests/test_whatsapp_watcher.py -v

# Step 3: Implement code sequentially (Green phase)
Task T022 → T023 → T024 → T025 → T026 → T027 → T028 → T029 → T030 → T031

# Step 4: Run tests again - they should all PASS
pytest tests/test_whatsapp_watcher.py -v

# Step 5: Manual validation
Send test message with "urgent" → Verify action file created
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T015)
3. Complete Phase 3: User Story 1 (T016-T031)
4. **STOP and VALIDATE**:
   - Run all tests: `pytest tests/test_whatsapp_watcher.py -v`
   - Manual test: Send priority WhatsApp message
   - Verify action file created in /Needs_Action
5. Deploy/demo if ready

### Incremental Delivery (TDD Approach)

1. **Foundation** (Setup + Foundational) → Tests pass, structure ready
2. **MVP** (Add US1) → Tests pass, detection works → Deploy/Demo
3. **Idempotency** (Add US2) → Tests pass, no duplicates → Deploy/Demo
4. **Resilience** (Add US3) → Tests pass, auto-recovery → Deploy/Demo
5. **Validation** (Add US4) → Tests pass, dry-run mode → Deploy/Demo
6. **Production** (Polish) → All tests pass, 24-hour stable → Production release

### TDD Workflow (Red-Green-Refactor)

For each user story:

1. **Red Phase**: Write all test tasks, run tests, verify they FAIL
2. **Green Phase**: Implement code tasks, run tests, verify they PASS
3. **Refactor Phase**: Clean up code, run tests, verify they still PASS
4. **Checkpoint**: Manual validation of user story independently

---

## Notes

- **[P]** tasks = different files, no dependencies, can run in parallel
- **[Story]** label maps task to specific user story for traceability
- **TDD Approach**: Tests written BEFORE implementation for each story
- Each user story should be independently completable and testable
- Verify tests FAIL before implementing (Red phase)
- Verify tests PASS after implementing (Green phase)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Reference implementation: `watchers/gmail_watcher.py` (470+ lines)
- State management: Reuse patterns from `watchers/gmail_state.py`

---

## Task Count Summary

- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 11 tasks (4 tests + 7 implementation)
- **Phase 3 (US1 - Priority Detection)**: 16 tasks (6 tests + 10 implementation)
- **Phase 4 (US2 - Restart-Safe)**: 10 tasks (4 tests + 6 implementation)
- **Phase 5 (US3 - Failure Recovery)**: 12 tasks (5 tests + 7 implementation)
- **Phase 6 (US4 - Dry-Run Mode)**: 8 tasks (3 tests + 5 implementation)
- **Phase 7 (Polish)**: 13 tasks (includes 3 additional compliance/performance tasks)

**Total**: 75 tasks (22 test tasks + 53 implementation/polish tasks)

**Parallel Opportunities**: 38 tasks marked [P] can run in parallel within their phase

**MVP Scope**: Phases 1-3 (31 tasks) deliver core priority message detection

**Estimated Time**:
- MVP (Phases 1-3): 8-12 hours
- Full Implementation (All phases): 18-26 hours
- Includes TDD approach with test-first development
