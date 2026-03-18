# ADR-0001: Centralized Error Recovery Module

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Accepted
- **Date:** 2026-03-16
- **Feature:** 005-error-recovery
- **Context:** The AI Employee system currently has retry logic scattered across multiple watchers (gmail_watcher.py, whatsapp_watcher.py) with inconsistent implementations. Each component implements its own retry patterns, leading to code duplication, inconsistent behavior, and maintenance challenges. As the system grows to include more external API integrations (LinkedIn, Facebook, Twitter, Odoo), this scattered approach becomes unsustainable. We need a unified error recovery strategy that provides retry patterns, circuit breaker protection, graceful degradation, and auto-restart capabilities across all components.

<!-- Significance checklist (ALL must be true to justify this ADR)
     1) Impact: Long-term consequence for architecture/platform/security? YES - affects all current and future integrations
     2) Alternatives: Multiple viable options considered with tradeoffs? YES - scattered vs centralized vs separate service
     3) Scope: Cross-cutting concern (not an isolated detail)? YES - impacts all watchers, services, and external API calls
-->

## Decision

Create a centralized error recovery module at `scripts/error_recovery/` with the following components:

- **Core Classes:**
  - `RetryPolicy`: Exponential backoff configuration and retry decision logic
  - `CircuitBreaker`: Three-state machine (CLOSED/OPEN/HALF_OPEN) for failure protection
  - `ServiceHealth`: Health tracking with critical/non-critical classification
  - `RecoveryState`: Persistent state management with atomic writes

- **Integration Layer:**
  - `@with_retry` decorator: Automatic retry with exponential backoff
  - `@with_circuit_breaker` decorator: Circuit breaker protection for external APIs
  - Explicit API for complex cases requiring fine-grained control

- **Infrastructure:**
  - State persistence in `AI_Employee_Vault/.state/recovery_state.json`
  - Audit logging integration for all recovery actions
  - Alert creation in `Needs_Action/` when automatic recovery fails

All existing watchers and services will migrate to use this centralized module, replacing their scattered retry implementations.

## Consequences

### Positive

- **Eliminates code duplication**: Single implementation of retry logic, circuit breaker, and health tracking used by all components
- **Ensures consistent behavior**: All components use the same retry delays, failure thresholds, and recovery strategies
- **Easier to test**: Centralized module can be thoroughly unit tested once, rather than testing scattered implementations
- **Easier to maintain**: Updates to error recovery logic only need to be made in one place
- **Single source of truth**: Configuration and behavior defined in one module, not scattered across codebase
- **Extensible**: New recovery patterns (e.g., bulkhead, rate limiting) can be added without touching existing code
- **Better observability**: All recovery actions logged consistently through centralized audit integration
- **Faster onboarding**: New integrations can adopt error recovery by adding decorators, no need to implement from scratch

### Negative

- **Migration effort required**: All existing watchers (gmail_watcher.py, whatsapp_watcher.py, linkedin_api_poster.py) must be updated to use new module
- **New dependency**: All components now depend on error_recovery module, increasing coupling
- **Potential breaking changes**: Migration must be done carefully to preserve existing behavior
- **Learning curve**: Team must learn new decorator API and understand when to use explicit API vs decorators
- **Rollback complexity**: If issues arise, rolling back requires reverting multiple files simultaneously
- **Testing overhead**: Must write comprehensive tests for centralized module to ensure reliability for all consumers

## Alternatives Considered

### Alternative 1: Keep Scattered Implementations

**Approach**: Continue with each component implementing its own retry logic

**Why rejected**:
- Code duplication across 6+ components (gmail_watcher, whatsapp_watcher, linkedin_poster, future integrations)
- Inconsistent behavior (gmail uses 3 retries, whatsapp uses different delays)
- Maintenance burden (bug fixes must be applied to multiple locations)
- Testing overhead (each implementation must be tested separately)
- No circuit breaker or graceful degradation (would need to implement in each component)

### Alternative 2: Separate Microservice

**Approach**: Create a standalone error recovery service that components call via HTTP/RPC

**Why rejected**:
- Added complexity (service deployment, monitoring, health checks)
- Latency overhead (network call for every retry decision)
- Single point of failure (if recovery service down, all components affected)
- Overkill for current scale (6 services, local-first architecture)
- Violates constitution principle of local-first architecture

### Alternative 3: Third-Party Library (tenacity, backoff)

**Approach**: Use existing Python retry libraries like `tenacity` or `backoff`

**Why rejected**:
- Doesn't include circuit breaker pattern (would need separate library)
- Doesn't integrate with our audit logging system (004-audit-logging)
- Doesn't support our state persistence requirements (AI_Employee_Vault/.state/)
- Doesn't provide service health classification (critical vs non-critical)
- Doesn't create alerts in our vault structure (Needs_Action/)
- Custom integration effort similar to building our own, but with less control

## References

- Feature Spec: [specs/005-error-recovery/spec.md](../../specs/005-error-recovery/spec.md)
- Implementation Plan: [specs/005-error-recovery/plan.md](../../specs/005-error-recovery/plan.md)
- Research: [specs/005-error-recovery/research.md](../../specs/005-error-recovery/research.md)
- Data Model: [specs/005-error-recovery/data-model.md](../../specs/005-error-recovery/data-model.md)
- Related ADRs: None (first ADR for this feature)
- Evaluator Evidence: [history/prompts/005-error-recovery/0002-error-recovery-implementation-plan.plan.prompt.md](../prompts/005-error-recovery/0002-error-recovery-implementation-plan.plan.prompt.md)
