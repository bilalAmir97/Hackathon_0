# Implementation Tasks: Twitter MCP Server

**Feature**: 008-twitter-mcp
**Branch**: `008-twitter-mcp`
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

---

## Task Summary

- **Total Tasks**: 36
- **Parallelizable Tasks**: 18
- **User Stories**: 4 (P1-P4)
- **Estimated Effort**: 12-16 hours

---

## Implementation Strategy

**MVP Scope**: User Story 1 (Post Tweet) - Phases 1-3
- Provides immediate value with tweet posting capability
- Validates Twitter API integration and approval workflow
- Foundation for remaining user stories

**Incremental Delivery**:
1. MVP: Tweet posting (P1) - 4-6 hours
2. Thread creation (P2) - 2-3 hours
3. Mentions monitoring (P3) - 2-3 hours
4. Metrics tracking (P4) - 2-3 hours
5. Polish & integration - 2-3 hours

---

## Dependencies & Execution Order

### Story Completion Order
```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1: Post Tweet) ✓ MVP
                                          ↓
                                    Phase 4 (US2: Thread) → Phase 5 (US3: Mentions) → Phase 6 (US4: Metrics)
                                                                                      ↓
                                                                                Phase 7 (Polish)
```

### Story Dependencies
- **US1 (Post Tweet)**: No dependencies - can start after foundational phase
- **US2 (Thread)**: Depends on US1 (uses same posting infrastructure)
- **US3 (Mentions)**: Independent of US1/US2 (read-only)
- **US4 (Metrics)**: Independent of US1/US2 (read-only)

### Parallel Execution Opportunities

**Phase 2 (Foundational)**: 3 parallel tracks
- Track A: Twitter client (T004-T006)
- Track B: Rate limiter (T007-T008)
- Track C: Helper scripts (T009-T010)

**Phase 3 (US1)**: 2 parallel tracks after T011
- Track A: MCP server implementation (T012-T014)
- Track B: Approval executor updates (T015-T016)

**Phase 4 (US2)**: Independent of US3/US4
**Phase 5 (US3)**: Can run parallel with US2 or US4
**Phase 6 (US4)**: Can run parallel with US2 or US3

---

## Phase 1: Setup & Dependencies

**Goal**: Initialize project structure and install dependencies

**Tasks**:

- [X] T001 Install Tweepy library (v4.14+) via pip or uv in pyproject.toml
- [X] T002 Add Twitter environment variables to .env.example
- [X] T003 Update .gitignore to exclude Twitter state files and test images

**Acceptance Criteria**:
- Tweepy v4.14+ installed and importable
- .env.example contains all Twitter variables with placeholders
- .gitignore prevents credential and state file leaks

---

## Phase 2: Foundational Infrastructure

**Goal**: Build core Twitter API client and rate limiting infrastructure

**Independent Test Criteria**:
- Twitter client can authenticate and make basic API calls
- Rate limiter tracks and enforces limits correctly
- Helper scripts validate setup and generate tokens

**Tasks**:

- [X] T004 [P] Create TwitterClient class in mcp_servers/twitter_client.py with Tweepy dual client pattern (API v2 + v1.1)
- [X] T005 [P] Implement authentication methods (OAuth 1.0a) in mcp_servers/twitter_client.py
- [X] T006 [P] Add error handling, retry decorators, and circuit breaker to TwitterClient in mcp_servers/twitter_client.py
- [X] T007 [P] Create TwitterRateLimiter class in mcp_servers/twitter_rate_limiter.py with 80% threshold
- [X] T008 [P] Implement rate limit tracking from response headers in mcp_servers/twitter_rate_limiter.py
- [X] T009 [P] Create get_twitter_tokens.py helper script in scripts/ for token generation
- [X] T010 [P] Create verify_twitter_setup.py script in scripts/ to validate credentials and API access

**Acceptance Criteria**:
- TwitterClient successfully authenticates with Twitter API
- Rate limiter correctly tracks and enforces 80% threshold
- Helper scripts run without errors and provide clear output
- All foundational components have error handling

---

## Phase 3: User Story 1 - Post Tweet (MVP)

**Story**: P1 - Post Tweet
**Goal**: Enable posting text and image tweets via approval workflow

**Independent Test Criteria**:
- Can create approval request for tweet posting
- Approval executor successfully posts tweet after approval
- Tweet appears on Twitter with correct content
- Audit log captures all tweet posting actions
- Image uploads work for 1-4 images

**Tasks**:

- [X] T011 [US1] Create twitter_mcp_server.py skeleton with MCP protocol setup in mcp_servers/
- [X] T012 [P] [US1] Implement twitter_post_tweet MCP tool handler in mcp_servers/twitter_mcp_server.py
- [X] T013 [P] [US1] Add approval request creation logic for tweets in mcp_servers/twitter_mcp_server.py
- [X] T014 [P] [US1] Implement image upload via Twitter media endpoint in mcp_servers/twitter_client.py
- [X] T015 [US1] Add execute_twitter_post_tweet handler to scripts/approval_executor.py
- [X] T016 [US1] Integrate audit logging for tweet posts in scripts/approval_executor.py
- [X] T017 [US1] Add tweet text validation (280 char limit) in mcp_servers/twitter_mcp_server.py
- [X] T018 [US1] Add image validation (format: PNG/JPG/GIF, size: 5MB max, count: 4 max) using existing image_validator.py

**Acceptance Criteria**:
- ✅ Successful text tweet: Creates approval → Posts after approval → Returns tweet ID
- ✅ Tweet with image: Uploads image → Posts tweet with media → Displays correctly
- ✅ Tweet with multiple images: Uploads all images → Posts with all media
- ✅ Tweet requires approval: Creates request in Pending_Approval/ → Waits for approval
- ✅ Audit log records: action_type, tweet_id, timestamp, parameters
- ✅ Edge cases handled: 280 char limit, image size, rate limits

**Test Scenarios** (Manual):
1. Post text-only tweet via approval workflow
2. Post tweet with single image
3. Post tweet with 4 images
4. Attempt tweet >280 chars (should error)
5. Attempt image >5MB (should error)
6. Verify audit log entries

---

## Phase 4: User Story 2 - Create Tweet Thread

**Story**: P2 - Create Tweet Thread
**Goal**: Enable posting multi-tweet threads with automatic numbering and linking

**Independent Test Criteria**:
- Can create approval request for thread posting
- Thread posts all tweets in sequence with proper linking
- Automatic numbering added (1/n, 2/n, etc.)
- Rollback works if thread creation fails mid-way
- Audit log captures thread creation

**Tasks**:

- [X] T019 [P] [US2] Implement twitter_post_thread MCP tool handler in mcp_servers/twitter_mcp_server.py
- [X] T020 [P] [US2] Add thread creation logic with automatic numbering in mcp_servers/twitter_client.py
- [X] T021 [P] [US2] Implement atomic thread posting with rollback in mcp_servers/twitter_client.py
- [X] T022 [US2] Add execute_twitter_post_thread handler to scripts/approval_executor.py
- [X] T023 [US2] Integrate audit logging for thread creation in scripts/approval_executor.py
- [X] T024 [US2] Add thread validation (2-25 tweets, 260 char limit per tweet) in mcp_servers/twitter_mcp_server.py

**Acceptance Criteria**:
- ✅ Successful thread: Posts all tweets → Links via in_reply_to → Returns all IDs
- ✅ Automatic numbering: Each tweet has (n/total) appended
- ✅ Thread with images: Distributes images across tweets correctly
- ✅ Thread requires approval: Single approval for entire thread
- ✅ Rollback on failure: Deletes posted tweets if mid-thread error
- ✅ Edge cases handled: 25 tweet limit, partial failures

**Test Scenarios** (Manual):
1. Post 3-tweet thread via approval workflow
2. Post thread with images
3. Verify automatic numbering (1/3, 2/3, 3/3)
4. Verify tweets are linked (each replies to previous)
5. Test rollback by simulating mid-thread failure

---

## Phase 5: User Story 3 - Monitor Mentions

**Story**: P3 - Monitor Mentions
**Goal**: Retrieve tweets mentioning the authenticated account

**Independent Test Criteria**:
- Can retrieve mentions from last 7 days
- Mentions include author info and text
- Results are cached for 5 minutes
- Filtering by date range works
- Audit log captures mention retrieval

**Tasks**:

- [X] T025 [P] [US3] Implement twitter_get_mentions MCP tool handler in mcp_servers/twitter_mcp_server.py
- [X] T026 [P] [US3] Add mentions retrieval via Tweepy in mcp_servers/twitter_client.py
- [X] T027 [P] [US3] Implement 5-minute TTL caching infrastructure and cache mentions in mcp_servers/twitter_client.py
- [X] T028 [US3] Add mentions filtering by date range in mcp_servers/twitter_client.py
- [X] T029 [US3] Integrate audit logging for mention retrieval in mcp_servers/twitter_mcp_server.py

**Acceptance Criteria**:
- ✅ Retrieve mentions: Returns list of mentions from last 7 days
- ✅ Mention data: Includes tweet_id, author_id, author_username, text, created_at
- ✅ Caching works: Second request within 5 minutes uses cache
- ✅ Date filtering: Can filter mentions by date range
- ✅ Empty results: Returns empty list if no mentions found
- ✅ Audit log records: action_type, count, timestamp

**Test Scenarios** (Manual):
1. Retrieve mentions (ensure some exist by mentioning account)
2. Verify mention data completeness
3. Test caching (second request should be instant)
4. Test date range filtering
5. Verify audit log entries

---

## Phase 6: User Story 4 - Track Engagement Metrics

**Story**: P4 - Track Engagement Metrics
**Goal**: Retrieve engagement metrics for tweets

**Independent Test Criteria**:
- Can retrieve metrics for specific tweet ID
- Metrics include likes, retweets, replies, impressions
- Results are cached for 5 minutes
- Engagement rate calculated correctly
- Audit log captures metrics retrieval

**Tasks**:

- [X] T030 [P] [US4] Implement twitter_get_metrics MCP tool handler in mcp_servers/twitter_mcp_server.py
- [X] T031 [P] [US4] Add metrics retrieval via Tweepy in mcp_servers/twitter_client.py
- [X] T032 [P] [US4] Implement 5-minute TTL caching for metrics (reuse cache from T027) in mcp_servers/twitter_client.py
- [X] T033 [US4] Add engagement rate calculation in mcp_servers/twitter_client.py
- [X] T034 [US4] Integrate audit logging for metrics retrieval in mcp_servers/twitter_mcp_server.py
- [X] T034a [P] [US4] Add account metrics retrieval (followers, tweet count) in mcp_servers/twitter_client.py

**Acceptance Criteria**:
- ✅ Retrieve metrics: Returns metrics for given tweet ID
- ✅ Account metrics: Returns follower count and tweet count
- ✅ Metric data: Includes likes, retweets, replies, impressions
- ✅ Engagement rate: Calculated as (likes + retweets + replies) / impressions
- ✅ Caching works: Second request within 5 minutes uses cache
- ✅ Missing metrics: Returns zeros with note if tweet too recent
- ✅ Audit log records: action_type, tweet_id, timestamp

**Test Scenarios** (Manual):
1. Post a tweet and retrieve its metrics
2. Verify all metric fields present
3. Verify engagement rate calculation
4. Test caching (second request should be instant)
5. Verify audit log entries

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Complete integration, documentation, and production readiness

**Tasks**:

- [X] T035 Update .env.example with all Twitter configuration options and comments

**Acceptance Criteria**:
- All environment variables documented in .env.example
- Setup verification script passes all checks
- All user stories tested end-to-end
- Documentation complete and accurate

---

## Parallel Execution Examples

### Example 1: Foundational Phase (Phase 2)
```bash
# Terminal 1: Twitter Client
# Work on T004-T006

# Terminal 2: Rate Limiter
# Work on T007-T008

# Terminal 3: Helper Scripts
# Work on T009-T010
```

### Example 2: User Story 1 (Phase 3)
```bash
# Terminal 1: MCP Server
# Work on T012-T014

# Terminal 2: Approval Executor
# Work on T015-T016
```

### Example 3: Independent Stories (Phases 5-6)
```bash
# Terminal 1: Mentions (US3)
# Work on T025-T029

# Terminal 2: Metrics (US4)
# Work on T030-T034
```

---

## Testing Strategy

**Note**: Tests are optional for this feature. If implementing tests:

### Unit Tests (Optional)
- twitter_client.py: Mock Tweepy calls, test authentication, error handling
- twitter_rate_limiter.py: Test threshold enforcement, header parsing
- twitter_mcp_server.py: Test each MCP tool handler with mocked client

### Integration Tests (Optional)
- Test actual Twitter API calls with test account
- Test approval workflow integration end-to-end
- Test audit logging integration

### End-to-End Tests (Optional)
- Complete tweet posting workflow (approval → post → log)
- Complete thread creation workflow
- Mentions and metrics retrieval workflows

---

## Risk Mitigation

### Risk 1: Twitter API Rate Limits
**Mitigation**: Proactive throttling at 80%, clear error messages, queue management

### Risk 2: Thread Creation Failures
**Mitigation**: Atomic rollback, detailed error logging, retry logic

### Risk 3: Authentication Issues
**Mitigation**: Setup verification script, clear error messages, token refresh logic

---

## Success Metrics

- Tweet posting success rate: >95%
- Thread creation success rate: >90%
- Mentions retrieval latency: <1 second
- Metrics retrieval latency: <1 second
- Rate limit compliance: 100% (never exceed quota)
- Audit log completeness: 100%

---

## Next Steps

1. Start with Phase 1 (Setup) - install dependencies
2. Complete Phase 2 (Foundational) - build core infrastructure
3. Implement MVP (Phase 3 - User Story 1)
4. Test MVP thoroughly before proceeding
5. Incrementally add remaining user stories
6. Polish and integrate
7. Create PR with comprehensive testing evidence

---

## Notes

- Reuse existing image_validator.py from Facebook/Instagram MCP
- Follow patterns from facebook_instagram_mcp_server.py for consistency
- All write operations require approval workflow
- All actions must be logged via audit_logger.py
- Rate limiting is critical - never exceed Twitter API quotas
