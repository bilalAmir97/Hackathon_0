---
id: 0002
title: Gmail Approval Workflow Plan
stage: plan
date: 2026-02-25
surface: agent
model: claude-sonnet-4-5
feature: 001-gmail-approval-workflow
branch: 001-gmail-approval-workflow
user: User
command: /sp.plan
labels: ["plan", "gmail", "approval-workflow", "silver-tier", "python", "watchdog", "oauth", "idempotent", "local-first"]
links:
  spec: specs/001-gmail-approval-workflow/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-gmail-approval-workflow/plan.md
  - specs/001-gmail-approval-workflow/data-model.md
  - specs/001-gmail-approval-workflow/research.md
  - specs/001-gmail-approval-workflow/quickstart.md
  - specs/001-gmail-approval-workflow/contracts/email-action.schema.json
  - specs/001-gmail-approval-workflow/contracts/log-entry.schema.json
  - specs/001-gmail-approval-workflow/contracts/approval-request.schema.json
  - CLAUDE.md
tests:
  - none
---

## Prompt

Goals:
- Implement Gmail Watcher (idempotent, restart-safe) + File-based Approval Workflow following Perception → Reasoning → Approval → Action → Done pipeline.

Architecture & Technical Design:
- Python-based Watcher (Gmail API + OAuth refresh) with persistent processed_ids store.
- Vault-driven state machine using /Needs_Action, /Pending_Approval, /Approved, /Rejected, /Done.
- Orchestrator monitors folder transitions and invokes MCP only after approval.
- Structured logging to /Logs/YYYY-MM-DD.json.
- Configurable polling interval + retry with exponential backoff.

Constraints:
- Local-first (Obsidian = source of truth).
- No hardcoded credentials (.env only).
- Max 3 retries for transient errors.
- Dry-run mode required.
- Idempotency guaranteed across restarts.

Edge Cases:
- Expired tokens, API rate limits, network failure.
- Duplicate email detection after crash.
- Corrupted approval files.
- Partial MCP execution failure.

Success Criteria & Testing Strategy:
- Email → Needs_Action (no duplicates).
- Approval required before send.
- Approved → MCP executes → Done.
- Rejected → Done without execution.
- End-to-end reproducible from vault state with log validation.

## Response snapshot

Created comprehensive implementation plan for Gmail Watcher + Approval Workflow (Silver Tier) with complete Phase 0 and Phase 1 artifacts:

**Plan Document (322 lines)**:
- Technical Context: Python 3.10+, google-auth-oauthlib, watchdog, pytest
- Constitution Check: All 10 principles satisfied (no violations)
- Project Structure: Analyzed existing codebase, documented actual architecture
- Phase 0 Research: 7 technical decisions documented with alternatives
- Phase 1 Design: Data model, contracts, quickstart guide
- Risk Analysis: High/medium/low risks with mitigations
- Success Metrics: Functional, reliability, auditability measures

**Phase 0: Research (7 decisions)**:
1. Gmail API: Polling with `users().messages().list()` (rejected Pub/Sub)
2. Idempotency: Persistent JSON state file (rejected SQLite, in-memory)
3. File Monitoring: Watchdog library (rejected polling, inotify)
4. OAuth: Auto-refresh before API calls (rejected manual, on-failure)
5. Retry: Exponential backoff with jitter (rejected fixed, immediate)
6. Logging: JSON Lines format (rejected JSON array, CSV)
7. Dry-Run: Environment variable flag (rejected separate paths, mocks)

**Phase 1: Data Model & Contracts**:
- 5 entities defined: Email Action Item, Approval Request, Log Entry, Watcher State, Action Plan
- 3 JSON schemas created: email-action, approval-request, log-entry
- Data flow documented: Gmail → Watcher → Vault → Orchestrator → MCP → Logs
- Storage estimates: 450 KB/day, 40 MB/90 days

**Phase 1: Quickstart Guide**:
- 8-step setup process: Gmail API credentials, OAuth token, environment config, vault validation
- Production deployment: PM2 or nohup for background processes
- Troubleshooting: 6 common issues with solutions
- Testing checklist: 10 verification steps

**Agent Context Updated**:
- Added Python 3.10+ to active technologies
- Added File-based storage to active technologies
- Updated CLAUDE.md with feature-specific context

## Outcome

- ✅ Impact: Production-ready implementation plan created; all constitution principles satisfied; 7 technical decisions documented with rationale; complete Phase 0 research and Phase 1 design artifacts
- 🧪 Tests: Testing strategy defined (unit, integration, manual); 3 test files planned (gmail_watcher, gmail_state, approval_executor)
- 📁 Files: 8 files created (plan.md, data-model.md, research.md, quickstart.md, 3 JSON schemas, CLAUDE.md updated)
- 🔁 Next prompts: Run `/sp.tasks` to generate actionable task list; Implement P1 (Email Detection) → P2 (Approval Workflow) → P3 (Action Execution) → P4 (System Resilience)
- 🧠 Reflection: Planning phase successfully completed with zero constitution violations. All technical decisions justified with alternatives considered. Idempotency strategy (persistent JSON state) and file-based state machine align perfectly with local-first architecture. Watchdog library enables event-driven approval workflow. OAuth auto-refresh ensures autonomous operation. Ready for task generation and implementation.

## Evaluation notes (flywheel)

- Failure modes observed: None - planning completed successfully with all Phase 0 and Phase 1 artifacts
- Graders run and results (PASS/FAIL): Constitution Check PASS (10/10 principles satisfied); Technical decisions PASS (7/7 with documented alternatives); Data model PASS (5 entities with validation rules); Contracts PASS (3 JSON schemas with proper validation)
- Prompt variant (if applicable): Standard /sp.plan command with user-provided goals and constraints
- Next experiment (smallest change to try): Generate tasks with `/sp.tasks` and verify task breakdown aligns with 4 user stories (P1-P4); validate that constitution-driven tasks are included in foundational phase
