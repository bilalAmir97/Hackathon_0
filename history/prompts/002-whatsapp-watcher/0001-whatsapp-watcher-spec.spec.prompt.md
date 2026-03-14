---
id: 0001
title: whatsapp-watcher-spec
stage: spec
date: 2026-02-25
surface: agent
model: claude-sonnet-4-5-20250929
feature: 002-whatsapp-watcher
branch: 002-whatsapp-watcher
user: user
command: /sp.specify
labels: ["whatsapp", "watcher", "sensor", "specification", "silver-tier"]
links:
  spec: specs/002-whatsapp-watcher/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-whatsapp-watcher/spec.md
  - specs/002-whatsapp-watcher/checklists/requirements.md
tests:
  - N/A (specification phase)
---

## Prompt

Role: Senior automation systems engineer designing production-grade WhatsApp Watcher for local-first AI Employee (Silver Tier – Multi-Channel Phase).

Goal: Design persistent, idempotent WhatsApp Watcher that monitors WhatsApp Web using Playwright, detects unread messages, filters by business keywords, prevents duplicate processing, creates structured .md files in /Needs_Action, and integrates with existing Email-based pipeline. Sensor-only (no reasoning, no MCP calls).

Constraints: Local-first architecture, Playwright persistent session, 30s polling interval, restart-safe, state persistence, dry-run mode, max 3 retries with exponential backoff, monitor-only (no sending), graceful shutdown, compatible with Orchestrator folder pipeline.

Edge Cases: Session expiration, network interruption, DOM selector changes, duplicate detection after restart, partial page load, rate limiting, corrupted session directory, large unread backlog.

Success Criteria: New message → file in /Needs_Action, no duplicates across restarts, keyword-only filtering, automatic recovery from transient failures, 24-hour continuous operation, JSON Lines logging, seamless approval workflow integration.

Output Format: System architecture, behavior spec, folder/state model, data schema, keyword filtering, session management, failure handling, pseudocode, test cases, non-goals.

## Response snapshot

Created comprehensive WhatsApp Watcher specification following Spec-Driven Development methodology:

**Branch Created**: 002-whatsapp-watcher

**Specification**: specs/002-whatsapp-watcher/spec.md
- 4 prioritized user stories (P1-P4) with independent test criteria
- 12 functional requirements (FR-001 to FR-012)
- 6 security & approval requirements (SR-001 to SR-006)
- 7 resilience requirements (RR-001 to RR-007)
- 10 measurable success criteria + 4 quality metrics
- 8 edge cases with handling strategies
- 4 key entities (WhatsApp Message, Action File, Watcher State, Priority Keyword)
- 10 assumptions, 10 out-of-scope items, 5 dependencies, 5 risks

**Quality Validation**: specs/002-whatsapp-watcher/checklists/requirements.md
- All quality gates passed on first validation
- Zero [NEEDS CLARIFICATION] markers
- Technology-agnostic success criteria
- Testable and unambiguous requirements
- Ready for planning phase

**Key Design Decisions**:
1. Sensor-only architecture (no reasoning, no action execution)
2. Idempotent operation with persistent state tracking
3. Exponential backoff retry logic (1s, 2s, 4s)
4. Session persistence to minimize re-authentication
5. Dry-run mode for safe testing
6. Integration with existing approval workflow

## Outcome

- ✅ Impact: Complete specification for WhatsApp Watcher (Silver Tier Phase 2 component), enabling multi-channel monitoring alongside Gmail
- 🧪 Tests: 16 acceptance scenarios defined across 4 user stories, 8 edge cases documented
- 📁 Files: spec.md (228 lines), requirements.md checklist (complete validation)
- 🔁 Next prompts: `/sp.plan` to generate implementation plan with architecture and task breakdown
- 🧠 Reflection: Specification prioritizes reliability and idempotency over features, appropriate for sensor layer. Strong focus on failure recovery and restart-safety ensures production readiness.

## Evaluation notes (flywheel)

- Failure modes observed: None - specification completed successfully on first attempt with zero clarifications needed
- Graders run and results (PASS/FAIL): Content Quality: PASS, Requirement Completeness: PASS, Feature Readiness: PASS
- Prompt variant (if applicable): Standard /sp.specify with detailed engineering requirements
- Next experiment (smallest change to try): Proceed to planning phase to validate specification completeness through implementation design
