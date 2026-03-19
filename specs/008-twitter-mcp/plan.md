# Implementation Plan: Twitter MCP Server

**Branch**: `008-twitter-mcp` | **Date**: 2026-03-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-twitter-mcp/spec.md`

## Summary

Create an MCP server that integrates with Twitter API v2 to enable tweet posting, thread creation, mentions monitoring, and engagement tracking. The server will expose MCP tools for posting tweets, creating threads, retrieving mentions, and tracking metrics. All write operations will integrate with the existing approval workflow system. The implementation will follow established patterns from facebook_instagram_mcp_server.py and email_mcp_server.py, including audit logging, error recovery decorators, and file-based approval workflow.

**Technical Approach**: Python MCP server using Tweepy library for Twitter API v2, with rate limiting via proactive throttling, image upload via Twitter media endpoint, metrics caching (5 minutes), and approval workflow integration for all write operations.

## Technical Context

**Language/Version**: Python 3.10+ (matching existing codebase)

**Primary Dependencies**:
- `mcp` (MCP protocol server)
- `tweepy` (Twitter API v2 client library)
- `Pillow` (image validation and processing)
- `python-dotenv` (environment variable management)

**Storage**:
- File-based approval workflow (AI_Employee_Vault/Pending_Approval/)
- Metrics cache (in-memory with 5-minute TTL)
- Rate limit state (in-memory, tracked per endpoint)
- Audit logs (AI_Employee_Vault/Logs/ via AuditLogger)

**Testing**: pytest (matching existing test suite)
- Unit tests for each MCP tool
- Integration tests for Twitter API calls
- Contract tests for approval workflow integration
- End-to-end tests for complete posting workflows

**Target Platform**: Linux server (WSL2 environment)

**Project Type**: Single project (MCP server module)

**Performance Goals**:
- Tweet posting: <2 seconds (excluding approval wait time)
- Thread creation: <10 seconds for 5-tweet thread
- Mentions retrieval: <1 second (with caching)
- Image upload: <5 seconds for images up to 5MB
- Rate limit detection: <100ms overhead per request

**Constraints**:
- Twitter API v2 rate limits: 50 tweets per 24 hours (free tier)
- Tweet character limit: 280 characters
- Image size limit: 5MB per image, max 4 images per tweet
- Thread limit: 25 tweets per thread
- Mentions retrieval: Last 7 days only
- Approval workflow adds 1-60 minutes latency (acceptable)

**Scale/Scope**:
- 1 platform (Twitter)
- 4 MCP tools (2 write, 2 read)
- ~400 lines of core logic (excluding tests)
- Support for 1 Twitter account initially

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with project constitution (`.specify/memory/constitution.md`):

- [x] **Local-First Architecture**: Approval requests stored in vault files (Pending_Approval/), audit logs in Logs/, no critical state in external DBs
- [x] **Safety Before Autonomy**: All write operations (tweet, thread) require approval workflow before execution
- [x] **File-Based State Transitions**: Approval workflow uses file movements (Pending_Approval/ → Approved/ → Done/)
- [x] **Idempotent Watchers**: N/A (this is an MCP server, not a watcher - idempotency handled by approval workflow)
- [x] **Explicit Reasoning**: MCP tools invoked by Claude Code after reasoning, approval requests document intent
- [x] **Human Accountability**: Approval boundaries enforced programmatically, no override capability in code
- [x] **Auditability**: All operations logged via AuditLogger with action_type, actor, target, parameters, result
- [x] **Secrets Management**: API keys and tokens in .env file only, never in code or vault files
- [x] **Tier Isolation**: Gold Tier feature (Module 3, Task 3.2), code in mcp_servers/ directory
- [x] **Error Handling**: Retry decorators for network errors, circuit breaker for API failures, graceful degradation for rate limits

**Violations Requiring Justification**: None - all constitution principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/008-twitter-mcp/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (in progress)
├── research.md          # Phase 0 output (to be created)
├── data-model.md        # Phase 1 output (to be created)
├── quickstart.md        # Phase 1 output (to be created)
├── contracts/           # Phase 1 output (to be created)
│   ├── twitter_tools.json        # Twitter MCP tool schemas
│   └── approval_workflow.json    # Approval request schema
├── checklists/
│   └── requirements.md  # Specification quality checklist (completed)
└── tasks.md             # Phase 2 output (created by /sp.tasks)
```

### Source Code (repository root)

```text
mcp_servers/
├── twitter_mcp_server.py             # Main MCP server (new)
├── twitter_client.py                 # Twitter API v2 client (new)
├── twitter_rate_limiter.py           # Twitter-specific rate limiting (new)
├── image_validator.py                # Existing (reuse from Facebook/Instagram)
├── facebook_instagram_mcp_server.py  # Existing (reference)
├── meta_graph_client.py              # Existing (reference)
└── email_mcp_server.py               # Existing (reference)

scripts/
├── audit_logger.py                   # Existing (used by MCP server)
├── approval_executor.py              # Existing (executes approved actions)
├── get_twitter_tokens.py             # Twitter token helper (new)
├── verify_twitter_setup.py           # Twitter setup verification (new)
└── error_recovery/                   # Existing (decorators for retry/circuit breaker)
    ├── decorators.py
    ├── retry_policy.py
    └── circuit_breaker.py

tests/
├── test_twitter_mcp_server.py        # MCP server tests (new)
├── test_twitter_client.py            # API client tests (new)
├── test_twitter_rate_limiter.py      # Rate limiting tests (new)
├── test_integration_twitter_workflow.py  # End-to-end tests (new)
└── conftest.py                       # Existing (shared fixtures)

AI_Employee_Vault/
├── Pending_Approval/                 # Approval requests created here
├── Approved/                         # Approved actions moved here
├── Done/                             # Completed actions moved here
└── Logs/                             # Audit logs written here

.env                                  # Environment variables (not in git)
├── TWITTER_API_KEY
├── TWITTER_API_SECRET
├── TWITTER_ACCESS_TOKEN
└── TWITTER_ACCESS_TOKEN_SECRET
```

**Structure Decision**: Single project structure following existing MCP server pattern. New MCP server in `mcp_servers/` directory alongside Facebook/Instagram and email servers. Supporting modules (Twitter client, rate limiter) in same directory. Reuse existing image_validator.py. Tests in `tests/` directory following existing naming convention. Approval workflow uses existing vault structure.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - table not needed.

---

## Phase 0: Research & Technology Decisions

### Research Tasks

#### R1: Twitter API v2 Integration with Tweepy

**Question**: What are the best practices for integrating Twitter API v2 using Tweepy library?

**Research Approach**:
- Review Tweepy v4.14+ documentation for API v2 support
- Analyze authentication patterns (OAuth 1.0a vs OAuth 2.0)
- Study rate limit handling in Tweepy
- Review media upload patterns for images

**Findings**: See research.md

#### R2: Twitter Rate Limiting Strategy

**Question**: How should we handle Twitter's strict rate limits (50 tweets/24h for free tier)?

**Research Approach**:
- Review Twitter API v2 rate limit documentation
- Analyze rate limit headers and response codes
- Study proactive throttling strategies
- Review queue-based approaches for rate limit management

**Findings**: See research.md

#### R3: Thread Creation Patterns

**Question**: What is the optimal approach for creating tweet threads with proper linking?

**Research Approach**:
- Review Twitter API v2 thread creation documentation
- Study reply chain mechanics
- Analyze thread numbering conventions
- Review error handling for partial thread failures

**Findings**: See research.md

#### R4: Approval Workflow Integration

**Question**: How should Twitter actions integrate with existing approval workflow?

**Research Approach**:
- Review existing approval_executor.py implementation
- Analyze Facebook/Instagram MCP approval patterns
- Study approval request schema requirements
- Review error handling for approval failures

**Findings**: See research.md

**Output**: research.md with consolidated findings

---

## Phase 1: Design & Contracts

### Data Model

**Output**: data-model.md with entities:
- Tweet (tweet_id, text, author_id, created_at, media_ids, metrics)
- Thread (thread_id, tweet_ids, created_at, total_tweets)
- Mention (mention_id, tweet_id, author_id, text, created_at)
- Metrics (likes, retweets, replies, impressions, engagement_rate)
- ApprovalRequest (approval_id, action_type, metadata, status)

### API Contracts

**Output**: contracts/ directory with:

1. **twitter_tools.json**: MCP tool schemas
   - twitter_post_tweet (text, image_paths, poll_options)
   - twitter_post_thread (tweets, image_paths)
   - twitter_get_mentions (since, max_results)
   - twitter_get_metrics (tweet_id)

2. **approval_workflow.json**: Approval request schema
   - SOCIAL_TWITTER_POST_TWEET
   - SOCIAL_TWITTER_POST_THREAD

### Quickstart Guide

**Output**: quickstart.md with:
- Twitter Developer Portal setup
- API key generation
- Environment variable configuration
- First tweet posting test
- Troubleshooting common issues

### Agent Context Update

**Action**: Run `.specify/scripts/bash/update-agent-context.sh claude`
- Add Twitter API v2 to active technologies
- Add Tweepy library reference
- Preserve existing manual additions

---

## Phase 2: Implementation Tasks

**Note**: Tasks are generated by `/sp.tasks` command (not part of `/sp.plan`).

See tasks.md for detailed implementation tasks with acceptance criteria.

---

## Architectural Decisions

### AD1: Use Tweepy Library

**Decision**: Use Tweepy v4.14+ for Twitter API v2 integration

**Rationale**:
- Official Python library for Twitter API
- Native support for API v2 endpoints
- Built-in rate limit handling
- Active maintenance and community support
- Simplifies authentication and request signing

**Alternatives Considered**:
- Direct requests library usage (more complex, error-prone)
- Twitter-API-v2 library (less mature, smaller community)

**Trade-offs**:
- Adds dependency on Tweepy library
- Must stay updated with Tweepy releases
- Abstracts some low-level API details

### AD2: Reuse image_validator.py

**Decision**: Reuse existing image_validator.py from Facebook/Instagram MCP

**Rationale**:
- Twitter image requirements similar to Facebook (5MB vs 4MB)
- Validation logic already tested and working
- Reduces code duplication
- Maintains consistency across social media integrations

**Alternatives Considered**:
- Create Twitter-specific validator (unnecessary duplication)
- No validation (risky, poor user experience)

**Trade-offs**:
- Slight difference in size limits (5MB vs 4MB) - handle via parameter

### AD3: Atomic Thread Creation

**Decision**: Implement thread creation as atomic operation (all tweets or none)

**Rationale**:
- Prevents partial threads that confuse users
- Simplifies error handling and rollback
- Maintains data consistency
- Aligns with approval workflow (single approval for entire thread)

**Alternatives Considered**:
- Best-effort thread creation (post what succeeds) - poor UX
- Manual rollback of partial threads - complex, error-prone

**Trade-offs**:
- Requires transaction-like logic for API calls
- May waste API quota on rollback scenarios
- More complex implementation

### AD4: 5-Minute Metrics Cache

**Decision**: Cache tweet metrics for 5 minutes

**Rationale**:
- Reduces API calls for frequently accessed metrics
- Twitter metrics don't change rapidly
- Balances freshness with API quota conservation
- Matches Facebook/Instagram caching strategy

**Alternatives Considered**:
- No caching (wastes API quota)
- Longer cache (10+ minutes) - stale data
- Shorter cache (1 minute) - minimal benefit

**Trade-offs**:
- Metrics may be up to 5 minutes stale
- Requires cache invalidation logic
- Memory overhead for cache storage

---

## Risk Mitigation

### Risk 1: Twitter API Rate Limits

**Mitigation**:
- Proactive throttling at 80% capacity
- Queue-based request management
- Clear error messages when limit reached
- Metrics dashboard showing quota usage

### Risk 2: Thread Creation Failures

**Mitigation**:
- Atomic transaction pattern (all or none)
- Detailed error logging for each tweet
- Rollback mechanism for partial threads
- Retry logic for transient failures

### Risk 3: Authentication Token Expiration

**Mitigation**:
- Token refresh logic in twitter_client.py
- Clear error messages for auth failures
- Setup verification script
- Documentation for token regeneration

### Risk 4: Image Upload Failures

**Mitigation**:
- Pre-upload validation (size, format)
- Separate retry logic for media uploads
- Fallback to text-only tweet on image failure
- Clear error messages with suggestions

---

## Testing Strategy

### Unit Tests
- twitter_mcp_server.py: Test each MCP tool handler
- twitter_client.py: Test API client methods with mocks
- twitter_rate_limiter.py: Test rate limit tracking and throttling

### Integration Tests
- Test actual Twitter API calls (with test account)
- Test approval workflow integration
- Test audit logging integration
- Test error recovery decorators

### End-to-End Tests
- Complete tweet posting workflow (approval → post → log)
- Complete thread creation workflow
- Mentions monitoring workflow
- Metrics retrieval workflow

### Contract Tests
- Validate MCP tool schemas
- Validate approval request schemas
- Validate audit log format

---

## Deployment Checklist

- [ ] Twitter Developer account created
- [ ] API keys generated and stored in .env
- [ ] Tweepy library installed (v4.14+)
- [ ] Environment variables configured
- [ ] Setup verification script passes
- [ ] All tests passing (unit + integration)
- [ ] Approval executor updated for Twitter actions
- [ ] Audit logger integration verified
- [ ] Rate limiting tested with real API
- [ ] Documentation complete (quickstart, troubleshooting)

---

## Success Metrics

- Tweet posting success rate: >95%
- Thread creation success rate: >90%
- Mentions retrieval latency: <1 second
- Metrics retrieval latency: <1 second
- Rate limit compliance: 100% (never exceed quota)
- Error recovery rate: >90% (transient failures)
- Audit log completeness: 100%

---

## Next Steps

1. Run `/sp.tasks` to generate implementation tasks
2. Implement twitter_client.py with Tweepy integration
3. Implement twitter_mcp_server.py with MCP tools
4. Implement twitter_rate_limiter.py
5. Write comprehensive tests
6. Create setup and verification scripts
7. Update approval_executor.py for Twitter actions
8. Test end-to-end workflows
9. Document setup and usage
10. Commit and create PR
