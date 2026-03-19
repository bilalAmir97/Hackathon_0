---
id: 002
title: facebook-instagram-mcp-implementation-plan
stage: plan
date: 2026-03-18
surface: agent
model: claude-sonnet-4-5
feature: 007-facebook-instagram-mcp
branch: 007-facebook-instagram-mcp
user: bilal-amir
command: /sp.plan
labels: ["social-media", "mcp-server", "meta-graph-api", "implementation-plan", "architecture"]
links:
  spec: specs/007-facebook-instagram-mcp/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/007-facebook-instagram-mcp/plan.md
  - specs/007-facebook-instagram-mcp/research.md
  - specs/007-facebook-instagram-mcp/data-model.md
  - specs/007-facebook-instagram-mcp/quickstart.md
  - specs/007-facebook-instagram-mcp/contracts/facebook_tools.json
  - specs/007-facebook-instagram-mcp/contracts/instagram_tools.json
  - specs/007-facebook-instagram-mcp/contracts/approval_workflow.json
  - CLAUDE.md (updated with new technologies)
tests:
  - none (planning phase)
---

## Prompt

analyze my existing codebase architecture then proceed with the plan file according to it

## Response snapshot

Created comprehensive implementation plan for Facebook & Instagram MCP Server following established codebase architecture patterns.

**Architecture Analysis**:
- Analyzed existing MCP servers (email_mcp_server.py, odoo_mcp_server.py)
- Reviewed error recovery system (decorators, retry policy, circuit breaker)
- Examined audit logging integration patterns
- Verified approval workflow file format and execution patterns

**Planning Artifacts Created**:

1. **plan.md** - Complete implementation plan with:
   - Technical context (Python 3.10+, requests, Pillow, cachetools)
   - Constitution compliance check (all 10 principles satisfied)
   - 4 module breakdown (MetaGraphClient, RateLimiter, ImageValidator, MCP Server)
   - 3 integration points (approval workflow, audit logging, error recovery)
   - 4 architectural decisions (sync vs async, in-memory state, approval workflow, caching)
   - 5 risk analyses with mitigations
   - Testing strategy (unit, integration, contract tests)

2. **research.md** - Technology decisions with:
   - 5 research tasks resolved (Meta API patterns, rate limiting, image upload, caching, approval workflow)
   - 4 technology choices made (requests, Pillow, custom rate limiter, cachetools)
   - Meta Graph API endpoint structure documented
   - Rate limit header parsing strategy defined
   - Image validation rules specified

3. **data-model.md** - Entity definitions with:
   - 5 entities (Post, Account, Metrics, ApprovalRequest, RateLimitState)
   - Entity relationships diagram
   - Data flow for write and read operations
   - Storage strategy (persistent vs transient)
   - Validation rules and state transitions

4. **contracts/** - MCP tool schemas:
   - facebook_tools.json (4 tools: post_text, post_image, get_metrics, get_insights)
   - instagram_tools.json (4 tools: post_image, post_carousel, get_metrics, get_insights)
   - approval_workflow.json (approval request schema, risk calculation, state transitions)

5. **quickstart.md** - Setup guide with:
   - Step-by-step token acquisition (Facebook page, Instagram business)
   - Environment variable configuration
   - Dependency installation
   - Connection verification scripts
   - Claude Code MCP configuration
   - Troubleshooting guide

**Key Architectural Decisions**:
- Synchronous implementation (consistency with existing MCP servers)
- In-memory rate limit tracking (hourly reset, acceptable to lose on restart)
- Approval workflow for all write operations (constitution compliance)
- 5-minute TTL cache for metrics (balance freshness vs API calls)
- Custom rate limiter (Meta headers require custom parsing)

**Constitution Compliance**: All 10 principles satisfied, no violations.

## Outcome

- ✅ Impact: Comprehensive implementation plan created following established codebase patterns. All Phase 0 and Phase 1 artifacts completed. Ready for task generation (/sp.tasks).
- 🧪 Tests: None (planning phase - test strategy defined in plan.md)
- 📁 Files: 8 files created (plan.md, research.md, data-model.md, quickstart.md, 3 contract files, CLAUDE.md updated)
- 🔁 Next prompts: /sp.tasks (generate implementation tasks), /sp.implement (execute tasks with TDD)
- 🧠 Reflection: Plan follows established patterns from email and Odoo MCP servers. Key decisions: synchronous implementation for consistency, custom rate limiter for Meta header parsing, approval workflow for all writes. Architecture aligns with constitution principles (local-first, safety before autonomy, auditability).

## Evaluation notes (flywheel)

- Failure modes observed: None - planning completed successfully
- Graders run and results (PASS/FAIL): Constitution check - ALL PASS (10/10 principles satisfied)
- Prompt variant (if applicable): Standard /sp.plan workflow with codebase architecture analysis
- Next experiment (smallest change to try): Proceed with /sp.tasks to generate implementation tasks with TDD test cases
