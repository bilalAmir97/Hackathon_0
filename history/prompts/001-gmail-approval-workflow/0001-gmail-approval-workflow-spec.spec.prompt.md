---
id: 0001
title: Gmail Approval Workflow Spec
stage: spec
date: 2026-02-25
surface: agent
model: claude-sonnet-4-5
feature: 001-gmail-approval-workflow
branch: 001-gmail-approval-workflow
user: User
command: /sp.specify
labels: ["spec", "gmail", "approval-workflow", "silver-tier", "watcher", "human-in-the-loop", "idempotent", "local-first"]
links:
  spec: specs/001-gmail-approval-workflow/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-gmail-approval-workflow/spec.md
  - specs/001-gmail-approval-workflow/checklists/requirements.md
tests:
  - none
---

## Prompt

Role:
You are a senior backend systems engineer designing a production-grade, local-first automation pipeline for a Personal AI Employee (Silver Tier).

Project:
Silver Tier – Gmail Watcher + Human-in-the-Loop Approval Workflow

Goal:
Design and implement:

1. A restart-safe, idempotent Gmail Watcher that:
   - Polls unread important emails
   - Prevents duplicates
   - Creates structured .md action files in /Needs_Action

2. A file-based Approval Workflow that:
   - Blocks sensitive actions (e.g., send email)
   - Uses /Pending_Approval, /Approved, /Rejected folders
   - Triggers MCP execution only after approval
   - Logs all actions

The system must follow Perception → Reasoning → Approval → Action → Done architecture.

Constraints:
- Local-first (Obsidian vault = single source of truth)
- No hardcoded credentials
- OAuth token refresh supported
- Watcher must survive restarts without duplicating emails
- Poll interval configurable (default 120s)
- All sensitive actions require approval file creation
- Dry-run mode supported for development
- Max 3 retries with exponential backoff for transient API errors
- Logs written to /Logs/YYYY-MM-DD.json
- Completion defined by file move to /Done

Edge Cases:
- Expired OAuth token
- Gmail API rate limits
- Network outage
- Duplicate message detection after restart
- Partial MCP failure after approval
- Corrupted or malformed approval file
- Orchestrator crash during execution
- Email already processed but file missing

Success Criteria:
- New unread important email → structured file created in /Needs_Action
- No duplicate files for same message ID (even after restart)
- Sensitive action creates approval file instead of executing
- Moving file to /Approved triggers MCP send
- Rejected file moves to /Done without execution
- All actions logged with timestamp + status
- System recovers gracefully from transient errors
- End-to-end flow reproducible from vault state

## Response snapshot

Created comprehensive feature specification for Gmail Watcher + Approval Workflow (Silver Tier) with production-grade requirements:

**Branch Created**: 001-gmail-approval-workflow

**User Stories (4 prioritized, independently testable)**:
1. P1: Email Detection and Action Creation (foundation - 5 acceptance scenarios)
2. P2: Human Approval Workflow (safety-first - 5 acceptance scenarios)
3. P3: Action Execution and Logging (automation completion - 5 acceptance scenarios)
4. P4: System Resilience and Recovery (production reliability - 5 acceptance scenarios)

**Requirements**:
- 15 Functional Requirements (FR-001 to FR-015)
- 10 Security & Approval Requirements (SR-001 to SR-010)
- 5 Key Entities defined (Email Action Item, Approval Request, Log Entry, Watcher State, Action Plan)

**Edge Cases**: 12 comprehensive scenarios with handling strategies

**Success Criteria**: 10 measurable, technology-agnostic outcomes (SC-001 to SC-010)

**Assumptions**: 10 documented assumptions for reasonable defaults

**Validation**: Created quality checklist - all items passed (16/16 checks)
- No [NEEDS CLARIFICATION] markers (all decisions made with reasonable defaults)
- All requirements testable and unambiguous
- Success criteria measurable and technology-agnostic
- No implementation details leaked into specification

## Outcome

- ✅ Impact: Production-grade specification created for Silver Tier automation pipeline; 4 independently testable user stories; 25 requirements defined; 12 edge cases covered; ready for planning phase
- 🧪 Tests: 20 acceptance scenarios defined across 4 user stories; quality checklist validation passed 16/16 checks
- 📁 Files: 2 files created (spec.md with 165 lines, requirements.md checklist)
- 🔁 Next prompts: Run `/sp.plan` to create implementation plan; Run `/sp.clarify` if any requirements need refinement (none currently needed)
- 🧠 Reflection: Specification successfully balances completeness with clarity. All critical production concerns addressed (idempotency, crash recovery, rate limits, token expiration). File-based state transitions align with constitution principles. Zero clarifications needed due to informed defaults documented in Assumptions section.

## Evaluation notes (flywheel)

- Failure modes observed: None - specification completed successfully with all quality checks passed
- Graders run and results (PASS/FAIL): Quality checklist validation PASS (16/16 items) - Content Quality 4/4, Requirement Completeness 8/8, Feature Readiness 4/4
- Prompt variant (if applicable): Standard /sp.specify command with comprehensive engineering requirements
- Next experiment (smallest change to try): Test specification clarity by running `/sp.plan` and verifying plan can be generated without additional clarifications; validate that all edge cases translate to concrete implementation tasks
