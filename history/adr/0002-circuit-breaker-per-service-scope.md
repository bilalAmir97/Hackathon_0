# ADR-0002: Circuit Breaker Per-Service Scope

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Accepted
- **Date:** 2026-03-16
- **Feature:** 005-error-recovery
- **Context:** The error recovery system needs circuit breaker protection to prevent cascading failures when external services fail. The key architectural question is: what should be the scope of each circuit breaker? Should we have one global circuit breaker for all external calls, one circuit breaker per service (gmail_api, whatsapp_web, linkedin_api), or one circuit breaker per operation (fetch_emails, send_email, post_message, etc.)? This decision impacts failure isolation, state management complexity, and recovery granularity. The system currently integrates with 3 external services (Gmail API, WhatsApp Web, LinkedIn API) and will add more in the future (Facebook, Twitter, Odoo).

<!-- Significance checklist (ALL must be true to justify this ADR)
     1) Impact: Long-term consequence for architecture/platform/security? YES - affects failure isolation and recovery behavior for all integrations
     2) Alternatives: Multiple viable options considered with tradeoffs? YES - global vs per-service vs per-operation
     3) Scope: Cross-cutting concern (not an isolated detail)? YES - impacts all external API integrations
-->

## Decision

Implement **one circuit breaker per external service** with the following scope:

- **Service-Level Circuit Breakers:**
  - `gmail_api`: Protects all Gmail API operations (fetch, send, search)
  - `whatsapp_web`: Protects all WhatsApp Web operations (read, send)
  - `linkedin_api`: Protects all LinkedIn API operations (post, get_stats)
  - Future services: `facebook_api`, `twitter_api`, `odoo_api`

- **Circuit Breaker Configuration:**
  - Failure threshold: 5 consecutive failures
  - Cooldown period: 60 seconds
  - Half-open test: Single request to verify recovery

- **State Management:**
  - Each circuit breaker maintains independent state (failure count, last failure time, current state)
  - All circuit states persisted in single `recovery_state.json` file
  - Circuit breakers identified by service name string

This provides a balance between failure isolation (service-level) and manageable complexity (not per-operation).

## Consequences

### Positive

- **Good failure isolation**: If Gmail API fails, only Gmail operations are blocked; WhatsApp and LinkedIn continue working
- **Prevents cascading failures**: Failing service doesn't bring down entire system
- **Manageable state size**: ~10 circuit breakers (one per service) vs 50+ (one per operation)
- **Clear failure boundaries**: Easy to understand which service is failing from circuit breaker state
- **Service-level recovery**: When service recovers, all operations resume together (no partial recovery confusion)
- **Simpler monitoring**: Health checks can report "Gmail API circuit open" rather than tracking dozens of operation-level circuits
- **Appropriate granularity**: Most service failures affect all operations (e.g., API down, rate limit, auth failure)

### Negative

- **Coarse-grained isolation**: If one Gmail operation fails repeatedly (e.g., send_email), all Gmail operations are blocked (including fetch_emails)
- **Potential false positives**: A single failing operation can open circuit for entire service
- **No operation-level recovery**: Can't selectively disable problematic operations while keeping others working
- **Service definition required**: Must clearly define service boundaries (e.g., is "gmail_send" separate from "gmail_fetch"?)
- **Shared failure budget**: All operations share the same failure threshold (5 failures across any operations)

## Alternatives Considered

### Alternative 1: Global Circuit Breaker

**Approach**: Single circuit breaker protecting all external API calls

**Why rejected**:
- **No failure isolation**: If Gmail API fails, circuit opens and blocks WhatsApp, LinkedIn, and all other services
- **Cascading failures**: One failing service brings down entire system
- **Poor recovery**: Must wait for all services to recover before circuit closes
- **Unclear failure source**: Can't tell which service is actually failing
- **Inappropriate for distributed systems**: Violates principle of isolating failures

### Alternative 2: Per-Operation Circuit Breakers

**Approach**: One circuit breaker per operation (fetch_emails, send_email, post_linkedin, etc.)

**Why rejected**:
- **Excessive complexity**: 50+ circuit breakers to manage (10 services × 5 operations each)
- **State explosion**: Large state file, slower persistence, more memory usage
- **Monitoring overhead**: Health checks must track dozens of circuit states
- **Confusing recovery**: Service partially recovered (some operations work, others don't)
- **Overkill for common failures**: Most service failures affect all operations (API down, auth failure, rate limit)
- **Harder to reason about**: "Gmail is failing" vs "fetch_emails is failing but send_email works"

### Alternative 3: Hierarchical Circuit Breakers

**Approach**: Service-level circuit breakers with optional operation-level overrides

**Why rejected**:
- **Added complexity**: Two-tier circuit breaker system with fallback logic
- **Unclear semantics**: When does operation-level override service-level?
- **Configuration burden**: Must configure both service and operation thresholds
- **Premature optimization**: No evidence that operation-level granularity is needed
- **Can be added later**: If needed, can introduce operation-level circuits without breaking existing service-level circuits

## References

- Feature Spec: [specs/005-error-recovery/spec.md](../../specs/005-error-recovery/spec.md)
- Implementation Plan: [specs/005-error-recovery/plan.md](../../specs/005-error-recovery/plan.md)
- Research: [specs/005-error-recovery/research.md](../../specs/005-error-recovery/research.md)
- Data Model: [specs/005-error-recovery/data-model.md](../../specs/005-error-recovery/data-model.md)
- Related ADRs: [ADR-0001: Centralized Error Recovery Module](0001-centralized-error-recovery-module.md)
- Evaluator Evidence: [history/prompts/005-error-recovery/0002-error-recovery-implementation-plan.plan.prompt.md](../prompts/005-error-recovery/0002-error-recovery-implementation-plan.plan.prompt.md)
