<!--
Sync Impact Report:
- Version: NEW → 1.0.0 (Initial constitution)
- Ratification: 2026-02-25
- Modified Principles: N/A (initial creation)
- Added Sections: All (7 core principles + 5 supporting sections)
- Removed Sections: None
- Templates Status:
  ✅ constitution.md created
  ⚠ plan-template.md - requires review for alignment
  ⚠ spec-template.md - requires review for alignment
  ⚠ tasks-template.md - requires review for alignment
- Follow-up TODOs: Review dependent templates for consistency with new principles
-->

# Hackathon 0 – Personal AI Employee Constitution

**Project Goal**: Design and implement a tiered (Bronze → Silver → Gold → Platinum), local-first, agent-driven Personal AI Employee that autonomously manages communications and business workflows using Claude Code (reasoning), Obsidian (state/memory), Watchers (sensors), and MCP servers (actions), with Human-in-the-Loop safeguards for sensitive operations.

## Core Principles

### I. Local-First Architecture

The Vault is the single source of truth. All system state, decisions, and audit trails MUST be persisted as files within the AI_Employee_Vault directory structure. No critical state may exist solely in memory or external databases. This ensures reproducibility, auditability, and system recovery from any point in time.

**Rationale**: File-based state enables version control, human inspection, and deterministic replay of system behavior without dependency on external services.

### II. Safety Before Autonomy

Approval workflow MUST precede all external actions. The system operates on a "perceive → reason → request approval → act" pipeline. No email sending, payment processing, or irreversible operation may execute without explicit human approval documented in the vault.

**Rationale**: Autonomous systems require safety guardrails. Human-in-the-loop approval prevents costly errors and maintains accountability for all consequential actions.

### III. File-Based Deterministic State Transitions

State changes are represented by file movements between vault directories. Moving a file from `/Needs_Action` to `/Pending_Approval` to `/Approved` to `/Done` creates an immutable audit trail. State MUST NOT be tracked in databases or memory-only structures.

**Rationale**: File movements are atomic, visible, and reversible. This design enables crash recovery and provides clear visual representation of workflow progress.

### IV. Idempotent Watchers

Watchers MUST detect and prevent duplicate task creation. Each watcher maintains state to track processed items (email IDs, message hashes, file checksums). Re-running a watcher on the same input MUST NOT create duplicate action files.

**Rationale**: System restarts and network failures are inevitable. Idempotency ensures reliable 24/7 operation without manual cleanup of duplicate tasks.

### V. Explicit Reasoning

Claude Code MUST write a Plan.md file to `/Plans` before invoking any MCP action. The plan documents the reasoning, alternatives considered, and expected outcomes. No action may be taken without a corresponding plan artifact.

**Rationale**: Explicit reasoning enables human review, debugging, and learning. Plans serve as documentation and provide context for future similar decisions.

### VI. Human Accountability

AI MUST NEVER override approval boundaries. The system may suggest, draft, and prepare actions, but final execution authority rests with humans. Approval thresholds are defined in Company_Handbook.md and MUST be enforced programmatically.

**Rationale**: Autonomous systems serve humans, not replace human judgment. Clear accountability boundaries prevent scope creep and maintain trust.

### VII. Auditability

Every external action MUST be logged to `/Logs/YYYY-MM-DD.json` with timestamp, action type, inputs, outputs, and approval reference. Logs MUST be retained for minimum 90 days. No action may execute without corresponding log entry.

**Rationale**: Audit trails enable compliance verification, debugging, and learning from system behavior over time.

## Architecture Standards

### Perception → Reasoning → Action Pipeline

The system architecture MUST strictly enforce this three-stage pipeline:

1. **Perception (Watchers)**: Monitor external sources (Gmail, WhatsApp, filesystem) and write observations to `/Needs_Action`. Watchers MUST NOT execute actions or make decisions.

2. **Reasoning (Claude Code)**: Analyze action items, generate plans in `/Plans`, create approval requests in `/Pending_Approval` for sensitive operations.

3. **Action (Orchestrator + MCP)**: Execute approved actions via MCP servers, log results to `/Logs`, move completed tasks to `/Done`.

**Enforcement Rules**:
- Watchers only write to `/Needs_Action` (never execute actions)
- Claude writes plans to `/Plans` before invoking MCP
- Sensitive actions require `/Pending_Approval` file creation
- Only Orchestrator may execute MCP actions
- Completion defined by file movement to `/Done`

## Key Standards

### Reproducibility

All automation MUST be reproducible from vault state. Given a vault snapshot and environment variables, the system MUST be able to resume operation without manual intervention.

### Secrets Management

- Secrets stored ONLY in environment variables (`.env` file)
- `.env` MUST be in `.gitignore`
- No credentials in vault Markdown files
- No credentials in git history
- Token rotation recommended every 90 days

### Logging Requirements

Every external action logged to `/Logs/YYYY-MM-DD.json` with:
- ISO 8601 timestamp
- Action type (email_sent, payment_processed, etc.)
- Input parameters
- Output/result
- Approval file reference
- Success/failure status

### Approval Requirements

Human approval REQUIRED for:
- Payments above threshold defined in Company_Handbook.md
- Emails to new contacts (not in approved list)
- Any irreversible action (deletions, cancellations)
- Actions with financial or legal consequences

### Development Standards

- Dry-run mode MUST be supported during development
- All AI functionality implemented as Agent Skills (`.claude/skills/`)
- Tier isolation: Bronze, Silver, Gold, Platinum code organized separately
- Watchers MUST support restart without data loss
- Maximum retry attempts defined for transient failures

## Edge Cases & Error Handling

The system MUST gracefully handle:

- **Token Expiration**: Pause operations, alert human, wait for token refresh
- **API Rate Limits**: Exponential backoff with maximum retry limit
- **Duplicate Message Detection**: Hash-based deduplication in watcher state
- **Orchestrator Crash Recovery**: Resume from last completed task in vault
- **Partial MCP Failure**: Log error, rollback if possible, create alert in `/Needs_Action`
- **Vault Lock/Corruption**: Graceful degradation, alert human, prevent data loss
- **Network Outage**: Queue tasks locally, retry when connection restored

## Constraints

### Technical Constraints

- All AI functionality implemented as Agent Skills
- Tier isolation maintained (Bronze, Silver, Gold, Platinum)
- No hardcoded credentials anywhere in codebase
- Watchers support restart without data loss
- System tolerates 24/7 operation
- Maximum 3 retry attempts for transient failures

### Operational Constraints

- Human approval required for sensitive operations
- Approval workflow cannot be bypassed programmatically
- Logs retained minimum 90 days
- Vault is authoritative source of truth
- State transitions via file movements only

## Security Requirements

### Mandatory Security Controls

1. **Credential Protection**:
   - `.env` in `.gitignore`
   - No secrets in Markdown files
   - No secrets in git commits
   - Environment variables only

2. **Approval Enforcement**:
   - Approval workflow mandatory for financial actions
   - Programmatic enforcement (not just policy)
   - Approval files immutable once created

3. **Audit Trail**:
   - All actions logged with approval reference
   - Logs tamper-evident (append-only)
   - Minimum 90-day retention

4. **Access Control**:
   - Monthly credential rotation recommended
   - Principle of least privilege for API tokens
   - Separate credentials per tier if possible

## Success Criteria

The constitution is successfully implemented when:

- ✅ Watchers reliably create action files without duplication
- ✅ Claude generates Plan.md before executing actions
- ✅ Approval workflow blocks sensitive operations
- ✅ MCP actions execute only after approval
- ✅ System recovers gracefully from transient errors
- ✅ Vault reflects accurate, real-time system state
- ✅ End-to-end workflow reproducible from logs
- ✅ No credentials in git history or vault files
- ✅ 24/7 operation without manual intervention (within approved boundaries)

## Definition of Done

The Personal AI Employee operates autonomously within defined boundaries, executes approved actions safely, maintains complete audit trails, and adheres to tier-specific deliverables as defined in Hackathon 0 documentation.

**Tier-Specific Deliverables**:
- **Bronze**: File system watcher + manual approval workflow
- **Silver**: Gmail/WhatsApp watchers + email MCP + approval automation
- **Gold**: Business system integration (Odoo, LinkedIn) + scheduling
- **Platinum**: Multi-agent coordination + advanced reasoning loops

## Governance

### Amendment Process

1. Proposed changes documented in ADR (Architecture Decision Record)
2. Impact analysis on existing artifacts (specs, plans, tasks)
3. Approval required before implementation
4. Version bump according to semantic versioning
5. Migration plan for breaking changes
6. Update dependent templates and documentation

### Versioning Policy

- **MAJOR**: Backward incompatible governance/principle removals or redefinitions
- **MINOR**: New principle/section added or materially expanded guidance
- **PATCH**: Clarifications, wording, typo fixes, non-semantic refinements

### Compliance Review

All PRs, code reviews, and task implementations MUST verify compliance with this constitution. Complexity MUST be justified against principles. Deviations require explicit ADR documentation and approval.

### Runtime Guidance

For agent-specific development guidance, refer to `CLAUDE.md` in project root. This constitution defines WHAT must be done; runtime guidance defines HOW Claude Code should operate.

---

**Version**: 1.0.0 | **Ratified**: 2026-02-25 | **Last Amended**: 2026-02-25
