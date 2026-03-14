---
id: 0002
title: whatsapp-watcher-plan
stage: plan
date: 2026-02-25
surface: agent
model: claude-sonnet-4-5-20250929
feature: 002-whatsapp-watcher
branch: 002-whatsapp-watcher
user: user
command: /sp.plan
labels: ["whatsapp", "watcher", "implementation-plan", "architecture", "silver-tier"]
links:
  spec: specs/002-whatsapp-watcher/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-whatsapp-watcher/plan.md
  - specs/002-whatsapp-watcher/research.md
  - specs/002-whatsapp-watcher/data-model.md
  - specs/002-whatsapp-watcher/quickstart.md
  - specs/002-whatsapp-watcher/contracts/whatsapp-action-file.schema.json
tests:
  - N/A (planning phase)
---

## Prompt

Goals: Implement restart-safe, idempotent WhatsApp Watcher (Playwright-based) that detects unread keyword-matched messages and writes structured files to /Needs_Action without executing actions.

Architecture & Technical Design: Python + Playwright persistent browser context, processed message ID store (local JSON/state file), configurable polling (default 30s) with exponential backoff retry, structured logging to /Logs/YYYY-MM-DD.json, sensor-only integration with existing Orchestrator pipeline.

Constraints: Local-first (Vault = source of truth), no message sending capability, dry-run mode supported, session reuse (no repeated QR login), restart-safe and duplicate-proof.

Edge Cases: Session expiry, DOM changes, network failure, large unread backlog, corrupted session storage, duplicate detection after crash.

Success Criteria & Testing Strategy: New relevant message → single file in /Needs_Action, no duplicates across restarts, graceful recovery from transient failures, 24-hour stability test without crash, end-to-end integration with Approval Workflow validated.

## Response snapshot

Created comprehensive implementation plan for WhatsApp Watcher following Spec-Driven Development methodology:

**Planning Artifacts Created**:

1. **plan.md** (449 lines): Complete implementation plan with:
   - Technical context (Python 3.13, Playwright 1.40+, existing dependencies)
   - Constitution compliance check (all 10 principles verified)
   - Project structure (documentation + source code layout)
   - Phase 0 research (5 technology decisions documented)
   - Phase 1 design (data model, contracts, integration points)
   - Architecture diagrams (component diagram, state machine)
   - Error handling strategy (6 failure modes)
   - Implementation validation (existing code review)
   - Testing strategy (unit, integration, manual)
   - Deployment guide (PM2 setup)
   - Risks & mitigations (5 identified)
   - Success metrics (5 measurable outcomes)

2. **research.md** (7 research topics): Technology decisions with rationale:
   - Playwright for browser automation (vs Selenium, Puppeteer)
   - Composite message ID for deduplication
   - data-testid selector strategy with fallbacks
   - Persistent browser context for session management
   - Exponential backoff retry logic (1s, 2s, 4s)
   - JSON Lines logging format (consistency with Gmail watcher)
   - JSON state file in vault (local-first architecture)

3. **data-model.md** (4 entities): Complete entity definitions:
   - WhatsAppMessage (detected unread message)
   - ActionFile (structured markdown in /Needs_Action)
   - WatcherState (persistent state tracking)
   - PriorityKeyword (configurable filtering)
   - Entity relationships and state transitions
   - Validation rules and performance considerations

4. **quickstart.md**: Step-by-step setup guide (15-20 minutes):
   - Dependency installation (Playwright browsers)
   - First-run QR code authentication
   - Priority message detection testing
   - Idempotency verification
   - PM2 production deployment
   - Troubleshooting guide

5. **contracts/whatsapp-action-file.schema.json**: JSON schema for action files with required fields validation

**Key Findings**:
- Existing implementation (`watchers/whatsapp_watcher.py`) already complete and matches specification
- No code gaps identified - validation and testing needed rather than new development
- Architecture fully compliant with constitution (all 10 principles)
- Reuses proven patterns from Gmail watcher (state management, logging, error handling)

**Architecture Decisions**:
- Sensor-only design (no reasoning or action execution)
- Playwright persistent_context for session management
- Composite message ID (sender + timestamp + preview) for deduplication
- Exponential backoff (1s, 2s, 4s) for transient failures
- JSON Lines logging consistent with existing infrastructure

## Outcome

- ✅ Impact: Complete implementation plan for WhatsApp Watcher with architecture, technology decisions, data model, and deployment guide
- 🧪 Tests: Testing strategy defined (unit, integration, manual) with 24-hour stability test requirement
- 📁 Files: plan.md (449 lines), research.md (7 topics), data-model.md (4 entities), quickstart.md (setup guide), JSON schema
- 🔁 Next prompts: `/sp.tasks` to generate task breakdown, then validate existing implementation against specification
- 🧠 Reflection: Planning revealed existing implementation is complete and specification-compliant. Focus shifts from development to validation and testing. Estimated 4-6 hours for validation vs. weeks for new development.

## Evaluation notes (flywheel)

- Failure modes observed: None - planning completed successfully with all required artifacts
- Graders run and results (PASS/FAIL): Constitution Check: PASS (10/10 principles), Architecture Design: PASS, Documentation: PASS
- Prompt variant (if applicable): Standard /sp.plan with detailed technical requirements
- Next experiment (smallest change to try): Validate existing code against plan, identify any gaps through testing rather than code review
