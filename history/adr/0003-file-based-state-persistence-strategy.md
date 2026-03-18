# ADR-0003: File-Based State Persistence Strategy

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Accepted
- **Date:** 2026-03-16
- **Feature:** 005-error-recovery
- **Context:** The error recovery system must persist circuit breaker states, service health status, and restart attempt counters to survive system restarts. Without persistence, a system restart would reset all circuits to closed state, lose failure counts, and forget restart attempts, potentially leading to restart loops or lost failure isolation. The system follows a local-first architecture (constitution principle) where all state must be persisted as files in the AI_Employee_Vault. The state must be: (1) human-readable for debugging, (2) atomic to prevent corruption, (3) fast to load/save (<50ms), (4) small enough for frequent updates (<100KB), and (5) consistent with existing patterns (gmail_watcher_state.json, whatsapp_watcher_state.json).

<!-- Significance checklist (ALL must be true to justify this ADR)
     1) Impact: Long-term consequence for architecture/platform/security? YES - affects system reliability and recovery behavior across restarts
     2) Alternatives: Multiple viable options considered with tradeoffs? YES - JSON file vs SQLite vs multiple files vs in-memory
     3) Scope: Cross-cutting concern (not an isolated detail)? YES - impacts all error recovery components and system restart behavior
-->

## Decision

Implement **single JSON file state persistence** with the following approach:

- **File Location:**
  - `AI_Employee_Vault/.state/recovery_state.json`
  - Follows existing pattern (gmail_watcher_state.json, whatsapp_watcher_state.json)

- **Atomic Write Pattern:**
  1. Serialize state to JSON
  2. Write to temporary file: `recovery_state.json.tmp`
  3. Flush and sync to disk (`fsync`)
  4. Atomic rename to `recovery_state.json` (POSIX atomic operation)

- **State Schema (JSON):**
  ```json
  {
    "version": "1.0.0",
    "last_updated": "ISO 8601 timestamp",
    "circuit_breakers": {
      "service_name": {
        "state": "CLOSED|OPEN|HALF_OPEN",
        "failure_count": 0,
        "last_failure_time": "ISO 8601 or null"
      }
    },
    "service_health": {
      "service_name": {
        "state": "healthy|degraded|failed",
        "consecutive_failures": 0,
        "restart_count": 0,
        "last_restart_time": "ISO 8601 or null"
      }
    }
  }
  ```

- **Corruption Handling:**
  - On JSON parse error: Create timestamped backup, initialize fresh state
  - Log corruption event to audit trail
  - Alert created in Needs_Action/

- **Schema Versioning:**
  - Version field enables future migrations
  - Load logic checks version and applies migrations if needed

This provides simplicity, human-readability, and consistency with existing codebase patterns.

## Consequences

### Positive

- **Human-readable**: JSON format can be inspected and debugged with standard tools (cat, jq, text editor)
- **Simple implementation**: No external dependencies, uses Python standard library (json module)
- **Consistent with existing patterns**: Follows same approach as gmail_watcher_state.json and whatsapp_watcher_state.json
- **Atomic writes prevent corruption**: Temp file + rename ensures state is never partially written
- **Version control friendly**: Text format can be diffed and tracked in git (for debugging, not production state)
- **Fast for small state**: <10KB state file loads/saves in <10ms
- **No external dependencies**: No database server, no additional processes
- **Easy backup and restore**: Simple file copy for backup, no database dump/restore needed
- **Schema versioning**: Version field enables future migrations without breaking changes

### Negative

- **No query capabilities**: Must load entire state to find specific circuit breaker or service health
- **No concurrent access control**: Multiple processes writing simultaneously could cause corruption (mitigated by single writer pattern)
- **File locking issues**: On some filesystems, atomic rename may not be truly atomic
- **Size limitations**: JSON parsing becomes slow for very large files (>1MB), but current state is <10KB
- **No transactions**: Can't atomically update multiple state files (but we only have one file)
- **No indexing**: Linear search through circuit breakers and service health (acceptable for <10 services)
- **Manual schema migration**: Must write migration code for version upgrades (vs automatic with ORM)

## Alternatives Considered

### Alternative 1: SQLite Database

**Approach**: Use SQLite database with tables for circuit_breakers, service_health, restart_attempts

**Why rejected**:
- **Added dependency**: Requires sqlite3 library (though included in Python standard library)
- **Overkill for scale**: Current state is <10KB with ~10 services, SQLite overhead not justified
- **Not human-readable**: Binary format, requires sqlite3 CLI or GUI to inspect
- **More complex**: Schema definition, migrations, connection management, query writing
- **Inconsistent with existing patterns**: All other state files use JSON (gmail_watcher_state.json, whatsapp_watcher_state.json)
- **Violates YAGNI**: No evidence that query capabilities or indexing are needed
- **Can migrate later**: If state grows to 100+ services, can migrate to SQLite without breaking API

### Alternative 2: Multiple JSON Files

**Approach**: Separate files for circuit breakers (`circuit_breakers.json`) and service health (`service_health.json`)

**Why rejected**:
- **Consistency challenges**: No atomic way to update multiple files simultaneously
- **More complex loading**: Must load and merge multiple files on startup
- **Partial state risk**: If one file corrupts, system has incomplete state
- **More file I/O**: Multiple reads/writes instead of single operation
- **Unclear benefit**: State is small enough that splitting provides no performance gain
- **Harder to backup**: Must backup multiple files instead of one

### Alternative 3: In-Memory Only (No Persistence)

**Approach**: Keep all state in memory, reset on restart

**Why rejected**:
- **Violates constitution**: Local-first architecture requires state persistence
- **Lost failure isolation**: System restart resets all circuits to closed, losing failure history
- **Restart loops**: Restart counter resets, allowing infinite restart attempts
- **No recovery context**: Can't resume from last known state after crash
- **Debugging impossible**: No state to inspect after system restart
- **Unacceptable for 24/7 operation**: System must survive restarts without losing critical state

### Alternative 4: Pickle Format

**Approach**: Use Python pickle for serialization instead of JSON

**Why rejected**:
- **Not human-readable**: Binary format, can't inspect with standard tools
- **Security concerns**: Pickle can execute arbitrary code during deserialization
- **Not cross-language**: Pickle is Python-specific, limits future integrations
- **Versioning challenges**: Pickle format changes between Python versions
- **Inconsistent with existing patterns**: All other state files use JSON

## References

- Feature Spec: [specs/005-error-recovery/spec.md](../../specs/005-error-recovery/spec.md)
- Implementation Plan: [specs/005-error-recovery/plan.md](../../specs/005-error-recovery/plan.md)
- Research: [specs/005-error-recovery/research.md](../../specs/005-error-recovery/research.md)
- Data Model: [specs/005-error-recovery/data-model.md](../../specs/005-error-recovery/data-model.md)
- Constitution: [.specify/memory/constitution.md](../../.specify/memory/constitution.md) (Principle I: Local-First Architecture)
- Related ADRs: [ADR-0001: Centralized Error Recovery Module](0001-centralized-error-recovery-module.md)
- Evaluator Evidence: [history/prompts/005-error-recovery/0002-error-recovery-implementation-plan.plan.prompt.md](../prompts/005-error-recovery/0002-error-recovery-implementation-plan.plan.prompt.md)

