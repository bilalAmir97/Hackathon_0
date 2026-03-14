---
id: 0003
title: whatsapp-watcher-tasks-tdd
stage: tasks
date: 2026-02-25
surface: agent
model: claude-sonnet-4-5-20250929
feature: 002-whatsapp-watcher
branch: 002-whatsapp-watcher
user: user
command: /sp.tasks
labels: ["whatsapp", "watcher", "tasks", "tdd", "test-driven-development", "silver-tier", "playwright", "browser-automation"]
links:
  spec: specs/002-whatsapp-watcher/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-whatsapp-watcher/tasks.md
tests:
  - N/A (task generation phase)
---

## Prompt

Create atomic tasks using TDD approach

## Response snapshot

Generated comprehensive task breakdown for WhatsApp Watcher implementation following Test-Driven Development methodology:

**Task Organization**:
- 72 total tasks organized by user story for independent implementation
- 22 test tasks (write FIRST - Red phase)
- 40 implementation tasks (make tests pass - Green phase)
- 10 polish tasks (refactor and production readiness)

**Phase Structure**:
1. **Phase 1 - Setup** (4 tasks): Playwright installation, .gitignore updates, vault verification
2. **Phase 2 - Foundational** (11 tasks): Core infrastructure with test fixtures, state management, message ID generation, filename sanitization
3. **Phase 3 - US1: Priority Detection** (16 tasks): Browser automation, WhatsApp Web navigation, unread chat scanning, keyword matching, action file creation
4. **Phase 4 - US2: Restart-Safe** (10 tasks): Duplicate detection, state persistence, corrupted state recovery, large backlog handling
5. **Phase 5 - US3: Failure Recovery** (12 tasks): Exponential backoff retry, network timeout handling, session expiration detection, DOM selector fallbacks, graceful shutdown
6. **Phase 6 - US4: Dry-Run Mode** (8 tasks): Testing mode implementation, detection logging without file creation
7. **Phase 7 - Polish** (10 tasks): Documentation, integration tests, 24-hour stability test, PM2 configuration

**TDD Workflow**:
- Red Phase: Write all tests for user story, verify they FAIL
- Green Phase: Implement minimal code to make tests PASS
- Refactor Phase: Clean up while keeping tests passing
- Checkpoint: Manual validation before next story

**Key Implementation Details**:
- Reference pattern: `watchers/gmail_watcher.py` (470+ lines)
- State management: Reuse `watchers/gmail_state.py` utilities
- Browser automation: Playwright with persistent_context for session management
- Message deduplication: Composite ID (sender + timestamp + preview[:50])
- Logging: JSON Lines format to `AI_Employee_Vault/Logs/YYYY-MM-DD.json`
- Action files: YAML frontmatter + Markdown to `AI_Employee_Vault/Needs_Action/`

**Independent Test Criteria**:
- US1: Send "urgent" message → Action file created within 60s
- US2: Process message → Restart → No duplicate file
- US3: Network interruption → Auto-retry and recovery
- US4: Dry-run mode → Logs but no files

**Parallel Opportunities**: 35 tasks marked [P] can run concurrently within phases

**MVP Scope**: Phases 1-3 (31 tasks) deliver core priority message detection

## Outcome

- ✅ Impact: Complete task breakdown with 72 atomic tasks organized by user story, enabling independent implementation and testing with TDD approach
- 🧪 Tests: 22 test tasks defined (write first, verify fail, then implement to pass)
- 📁 Files: tasks.md (72 tasks with checklist format, file paths, dependencies, parallel markers)
- 🔁 Next prompts: `/sp.implement` to execute tasks, or start with MVP (Phases 1-3: T001-T031)
- 🧠 Reflection: TDD approach ensures quality through test-first development. Task organization by user story enables incremental delivery (MVP → Idempotency → Resilience → Validation). Estimated 16-24 hours for full implementation, 8-12 hours for MVP.

## Evaluation notes (flywheel)

- Failure modes observed: None - task generation completed successfully with all required format validation
- Graders run and results (PASS/FAIL): Format Validation: PASS (all 72 tasks follow checklist format), Organization: PASS (grouped by user story), TDD Structure: PASS (tests before implementation)
- Prompt variant (if applicable): Standard /sp.tasks with explicit TDD approach request
- Next experiment (smallest change to try): Execute MVP tasks (T001-T031) to validate task granularity and time estimates
