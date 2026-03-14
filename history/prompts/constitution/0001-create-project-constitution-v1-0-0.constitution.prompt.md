---
id: 0001
title: Create Project Constitution v1.0.0
stage: constitution
date: 2026-02-25
surface: agent
model: claude-sonnet-4-5
feature: none
branch: main
user: User
command: /sp.constitution
labels: ["constitution", "governance", "principles", "v1.0.0", "hackathon-0"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - .specify/templates/plan-template.md
  - .specify/templates/spec-template.md
  - .specify/templates/tasks-template.md
tests:
  - none
---

## Prompt

Project: Hackathon 0 – Personal AI Employee (Digital FTE)

Goal:
Design and implement a tiered (Bronze → Silver → Gold → Platinum), local-first, agent-driven Personal AI Employee that autonomously manages communications and business workflows using Claude Code (reasoning), Obsidian (state/memory), Watchers (sensors), and MCP servers (actions), with Human-in-the-Loop safeguards for sensitive operations.

Core Principles:
- Local-first architecture (Vault = single source of truth)
- Safety before autonomy (Approval workflow precedes external actions)
- File-based deterministic state transitions (move = state change)
- Idempotent watchers (no duplicate task creation)
- Explicit reasoning (Plan.md before action)
- Human accountability (AI never overrides approval boundaries)
- Auditability (every action logged)

Architecture Standards:
- Perception → Reasoning → Action pipeline strictly enforced
- Watchers only write to /Needs_Action (never execute actions)
- Claude writes plans to /Plans before invoking MCP
- Sensitive actions require /Pending_Approval file creation
- Only Orchestrator may execute MCP actions
- Completion defined by file movement to /Done

Key Standards:
- All automation must be reproducible from vault state
- Secrets stored only in environment variables (.env, never vault)
- Every external action logged in /Logs/YYYY-MM-DD.json
- Approval required for: Payments > defined threshold, Emails to new contacts, Any irreversible action
- Dry-run mode must be supported during development

Edge Cases:
- Token expiration (pause + human alert)
- API rate limits (exponential backoff)
- Duplicate message detection
- Orchestrator crash recovery
- Partial MCP failure (log + rollback if possible)
- Vault lock or corruption (graceful degradation)
- Network outage (queue tasks locally)

Constraints:
- All AI functionality implemented as Agent Skills
- Tier isolation: Bronze, Silver, Gold code organized separately
- No hardcoded credentials
- Watchers must support restart without data loss
- Max retry attempts defined for transient failures
- System must tolerate 24/7 operation

Security Requirements:
- .env in .gitignore
- No secrets inside Markdown files
- Approval workflow mandatory for financial actions
- Monthly credential rotation recommended
- Minimum 90-day audit log retention

Success Criteria:
- Watchers reliably create action files without duplication
- Claude generates Plan.md before executing actions
- Approval workflow blocks sensitive operations
- MCP actions execute only after approval
- System recovers gracefully from transient errors
- Vault reflects accurate, real-time system state
- End-to-end workflow reproducible from logs

Definition of Done:
The Personal AI Employee operates autonomously within defined boundaries, executes approved actions safely, maintains complete audit trails, and adheres to tier-specific deliverables as defined in Hackathon 0 documentation.

## Response snapshot

Created comprehensive project constitution v1.0.0 with 7 core principles and 5 supporting sections:

**Core Principles Established:**
1. Local-First Architecture - Vault as single source of truth
2. Safety Before Autonomy - Approval workflow precedes all external actions
3. File-Based Deterministic State Transitions - State changes via file movements
4. Idempotent Watchers - Duplicate detection and prevention
5. Explicit Reasoning - Plan.md creation before MCP actions
6. Human Accountability - No AI override of approval boundaries
7. Auditability - Complete logging to /Logs/YYYY-MM-DD.json

**Supporting Sections:**
- Architecture Standards (Perception → Reasoning → Action pipeline)
- Key Standards (Reproducibility, Secrets Management, Logging, Approval Requirements)
- Edge Cases & Error Handling (Token expiration, rate limits, crashes, network outages)
- Constraints (Technical and Operational)
- Security Requirements (Credential protection, approval enforcement, audit trails)
- Success Criteria (9 measurable outcomes)
- Governance (Amendment process, versioning policy, compliance review)

**Template Updates:**
- Updated plan-template.md with constitution check section (10 checkboxes)
- Updated spec-template.md with Security & Approval Requirements section
- Updated tasks-template.md with Constitution-Driven Tasks in foundational phase

**Sync Impact Report:**
- Version: NEW → 1.0.0 (Initial constitution)
- Ratification: 2026-02-25
- All templates flagged for review and updated
- No placeholders remaining in constitution

## Outcome

- ✅ Impact: Project constitution established as authoritative governance document; all 7 principles documented with rationale; 3 templates updated for consistency
- 🧪 Tests: N/A (documentation artifact)
- 📁 Files: 4 files created/modified (.specify/memory/constitution.md, 3 template updates)
- 🔁 Next prompts: Review constitution compliance in existing code; Create ADRs for significant architectural decisions; Update CLAUDE.md runtime guidance if needed
- 🧠 Reflection: Constitution provides clear governance for autonomous AI system with strong safety guarantees. File-based state transitions and approval workflows are well-defined. Templates now enforce constitution compliance during planning and task generation.

## Evaluation notes (flywheel)

- Failure modes observed: None - constitution creation completed successfully with all placeholders filled
- Graders run and results (PASS/FAIL): Manual validation PASS - no unresolved placeholders, version semantics correct, principles testable and declarative
- Prompt variant (if applicable): Standard /sp.constitution command with comprehensive user input
- Next experiment (smallest change to try): Test constitution compliance checking during /sp.plan execution; verify template updates enforce principles correctly
