# Tasks: Facebook & Instagram MCP Server

**Input**: Design documents from `/specs/007-facebook-instagram-mcp/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included following TDD approach (SDD + TDD methodology for Gold Tier Module 3)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Add dependencies to requirements.txt (requests>=2.31.0, Pillow>=10.0.0, cachetools>=5.3.0)
- [ ] T002 Update .env.example with Facebook and Instagram token placeholders
- [ ] T003 Verify .env is in .gitignore to prevent token leakage

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create ImageValidator class in mcp_servers/image_validator.py with validation methods
- [ ] T005 [P] Create RateLimiter class in mcp_servers/rate_limiter.py with quota tracking
- [ ] T006 [P] Create MetaGraphClient base class in mcp_servers/meta_graph_client.py with authentication
- [ ] T007 [P] Create approval workflow helper functions in mcp_servers/meta_graph_client.py (generate_approval_id, create_approval_request_file)
- [ ] T008 [P] Create execution functions module structure in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T009 Initialize MCP server app in mcp_servers/facebook_instagram_mcp_server.py with list_tools and call_tool handlers

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Post to Facebook Page (Priority: P1) 🎯 MVP

**Goal**: Enable posting text and images to Facebook pages with approval workflow

**Independent Test**: Create approval request for Facebook post, approve it, verify post appears on Facebook page with correct content and audit log entry

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Write test_facebook_post_text_creates_approval in tests/test_facebook_instagram_mcp_server.py
- [ ] T011 [P] [US1] Write test_facebook_post_image_validates_image in tests/test_facebook_instagram_mcp_server.py
- [ ] T012 [P] [US1] Write test_facebook_post_image_creates_approval in tests/test_facebook_instagram_mcp_server.py
- [ ] T013 [P] [US1] Write test_execute_facebook_post_text_success in tests/test_meta_graph_client.py
- [ ] T014 [P] [US1] Write test_execute_facebook_post_image_success in tests/test_meta_graph_client.py
- [ ] T015 [P] [US1] Write test_facebook_image_validation_size_limit in tests/test_image_validator.py
- [ ] T016 [P] [US1] Write test_facebook_image_validation_format in tests/test_image_validator.py

### Implementation for User Story 1

- [ ] T017 [P] [US1] Implement validate_facebook_image method in mcp_servers/image_validator.py (validate format, min 200x200px, max 4MB; max dimensions 2048x2048 are optional recommendations)
- [ ] T018 [P] [US1] Implement get_image_info method in mcp_servers/image_validator.py
- [ ] T019 [US1] Implement post_to_facebook_page method in mcp_servers/meta_graph_client.py with @with_retry decorator
- [ ] T020 [US1] Implement post_image_to_facebook method in mcp_servers/meta_graph_client.py with @with_retry decorator
- [ ] T021 [US1] Add facebook_post_text tool definition to list_tools in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T022 [US1] Add facebook_post_image tool definition to list_tools in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T023 [US1] Implement facebook_post_text_handler in mcp_servers/facebook_instagram_mcp_server.py (includes FR9.1 formatting: preserve line breaks, auto-link URLs, support @mentions/hashtags)
- [ ] T024 [US1] Implement facebook_post_image_handler in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T025 [US1] Implement execute_facebook_post_text function in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T026 [US1] Implement execute_facebook_post_image function in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T027 [US1] Add audit logging to facebook_post_text_handler in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T028 [US1] Add audit logging to facebook_post_image_handler in mcp_servers/facebook_instagram_mcp_server.py

**Checkpoint**: At this point, User Story 1 should be fully functional - can post text and images to Facebook with approval workflow

---

## Phase 4: User Story 2 - Post to Instagram Business Account (Priority: P1)

**Goal**: Enable posting images and carousels to Instagram business accounts with approval workflow

**Independent Test**: Create approval request for Instagram post, approve it, verify post appears on Instagram feed with correct caption and audit log entry

### Tests for User Story 2

- [ ] T029 [P] [US2] Write test_instagram_post_image_creates_approval in tests/test_facebook_instagram_mcp_server.py
- [ ] T030 [P] [US2] Write test_instagram_post_carousel_validates_images in tests/test_facebook_instagram_mcp_server.py
- [ ] T031 [P] [US2] Write test_instagram_post_carousel_creates_approval in tests/test_facebook_instagram_mcp_server.py
- [ ] T032 [P] [US2] Write test_execute_instagram_post_image_success in tests/test_meta_graph_client.py
- [ ] T033 [P] [US2] Write test_execute_instagram_post_carousel_success in tests/test_meta_graph_client.py
- [ ] T034 [P] [US2] Write test_instagram_image_validation_aspect_ratio in tests/test_image_validator.py
- [ ] T035 [P] [US2] Write test_instagram_image_validation_size_limit in tests/test_image_validator.py

### Implementation for User Story 2

- [ ] T036 [P] [US2] Implement validate_instagram_image method in mcp_servers/image_validator.py
- [ ] T037 [P] [US2] Implement calculate_aspect_ratio helper in mcp_servers/image_validator.py
- [ ] T038 [US2] Implement create_instagram_container method in mcp_servers/meta_graph_client.py with @with_retry decorator
- [ ] T039 [US2] Implement publish_instagram_container method in mcp_servers/meta_graph_client.py with @with_retry decorator
- [ ] T040 [US2] Implement post_to_instagram method in mcp_servers/meta_graph_client.py (combines create + publish)
- [ ] T041 [US2] Implement post_carousel_to_instagram method in mcp_servers/meta_graph_client.py
- [ ] T042 [US2] Add instagram_post_image tool definition to list_tools in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T043 [US2] Add instagram_post_carousel tool definition to list_tools in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T044 [US2] Implement instagram_post_image_handler in mcp_servers/facebook_instagram_mcp_server.py (includes FR9.2 formatting: preserve line breaks, support @mentions/hashtags, emoji support)
- [ ] T045 [US2] Implement instagram_post_carousel_handler in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T046 [US2] Implement execute_instagram_post_image function in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T047 [US2] Implement execute_instagram_post_carousel function in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T048 [US2] Add audit logging to instagram_post_image_handler in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T049 [US2] Add audit logging to instagram_post_carousel_handler in mcp_servers/facebook_instagram_mcp_server.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - can post to Facebook and Instagram

---

## Phase 5: User Story 3 - Retrieve Engagement Metrics (Priority: P2)

**Goal**: Enable retrieval of engagement metrics for Facebook and Instagram posts with caching

**Independent Test**: Retrieve metrics for existing post, verify correct values returned, verify cache hit on second request within 5 minutes

### Tests for User Story 3

- [ ] T050 [P] [US3] Write test_get_facebook_post_metrics_cache_miss in tests/test_facebook_instagram_mcp_server.py
- [ ] T051 [P] [US3] Write test_get_facebook_post_metrics_cache_hit in tests/test_facebook_instagram_mcp_server.py
- [ ] T052 [P] [US3] Write test_get_instagram_post_metrics_cache_miss in tests/test_facebook_instagram_mcp_server.py
- [ ] T053 [P] [US3] Write test_get_instagram_post_metrics_cache_hit in tests/test_facebook_instagram_mcp_server.py
- [ ] T054 [P] [US3] Write test_get_facebook_page_insights in tests/test_meta_graph_client.py
- [ ] T055 [P] [US3] Write test_get_instagram_account_insights in tests/test_meta_graph_client.py
- [ ] T056 [P] [US3] Write test_metrics_cache_expiry in tests/test_facebook_instagram_mcp_server.py

### Implementation for User Story 3

- [ ] T057 [P] [US3] Initialize metrics cache with cachetools.TTLCache in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T058 [P] [US3] Implement get_facebook_post_metrics method in mcp_servers/meta_graph_client.py with @with_circuit_breaker decorator
- [ ] T059 [P] [US3] Implement get_instagram_post_metrics method in mcp_servers/meta_graph_client.py with @with_circuit_breaker decorator
- [ ] T060 [P] [US3] Implement get_facebook_page_insights method in mcp_servers/meta_graph_client.py
- [ ] T061 [P] [US3] Implement get_instagram_account_insights method in mcp_servers/meta_graph_client.py
- [ ] T062 [US3] Add get_facebook_post_metrics tool definition to list_tools in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T063 [US3] Add get_instagram_post_metrics tool definition to list_tools in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T064 [US3] Add get_facebook_page_insights tool definition to list_tools in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T065 [US3] Add get_instagram_account_insights tool definition to list_tools in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T066 [US3] Implement get_facebook_post_metrics_handler with cache check in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T067 [US3] Implement get_instagram_post_metrics_handler with cache check in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T068 [US3] Implement get_facebook_page_insights_handler in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T069 [US3] Implement get_instagram_account_insights_handler in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T070 [US3] Add audit logging to all metrics handlers in mcp_servers/facebook_instagram_mcp_server.py

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - posting and metrics retrieval functional

---

## Phase 6: User Story 4 - Schedule Posts with Approval Workflow (Priority: P2)

**Goal**: Enable scheduling posts for future publication with approval workflow

**Independent Test**: Schedule Facebook post for future time, approve it, verify post publishes at scheduled time

### Tests for User Story 4

- [ ] T071 [P] [US4] Write test_schedule_facebook_post_creates_approval in tests/test_facebook_instagram_mcp_server.py
- [ ] T072 [P] [US4] Write test_schedule_instagram_post_creates_approval in tests/test_facebook_instagram_mcp_server.py
- [ ] T073 [P] [US4] Write test_scheduled_post_publishes_at_correct_time in tests/test_integration_social_workflow.py
- [ ] T074 [P] [US4] Write test_scheduled_post_validation_past_time in tests/test_facebook_instagram_mcp_server.py

### Implementation for User Story 4

- [ ] T075 [US4] Add scheduled_time parameter support to facebook_post_text_handler in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T076 [US4] Add scheduled_time parameter support to facebook_post_image_handler in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T077 [US4] Add scheduled_time parameter support to instagram_post_image_handler in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T078 [US4] Add scheduled_time parameter support to instagram_post_carousel_handler in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T079 [US4] Add scheduled_time validation (must be future) to all post handlers in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T080 [US4] Update approval request format to include scheduled_time in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T081 [US4] Update approval executor to handle scheduled posts in scripts/approval_executor.py

**Checkpoint**: At this point, all posting features support scheduling - posts can be scheduled for future publication

---

## Phase 7: User Story 5 - Handle Rate Limits Gracefully (Priority: P3)

**Goal**: Implement proactive rate limiting to prevent API errors and queue requests when limits reached

**Independent Test**: Make multiple rapid API calls, verify throttling at 80% capacity, verify queued requests retry after cooldown

### Tests for User Story 5

- [ ] T082 [P] [US5] Write test_rate_limit_header_parsing in tests/test_rate_limiter.py
- [ ] T083 [P] [US5] Write test_proactive_throttling_at_80_percent in tests/test_rate_limiter.py
- [ ] T084 [P] [US5] Write test_rate_limit_queue_management in tests/test_rate_limiter.py
- [ ] T085 [P] [US5] Write test_rate_limit_exponential_backoff in tests/test_rate_limiter.py
- [ ] T086 [P] [US5] Write test_rate_limit_per_endpoint_tracking in tests/test_rate_limiter.py
- [ ] T087 [P] [US5] Write test_rate_limit_integration_with_meta_client in tests/test_meta_graph_client.py

### Implementation for User Story 5

- [ ] T088 [P] [US5] Implement parse_rate_limit_headers method in mcp_servers/rate_limiter.py
- [ ] T089 [P] [US5] Implement check_rate_limit method in mcp_servers/rate_limiter.py
- [ ] T090 [P] [US5] Implement update_rate_limit method in mcp_servers/rate_limiter.py
- [ ] T091 [P] [US5] Implement wait_for_rate_limit_reset method in mcp_servers/rate_limiter.py
- [ ] T092 [P] [US5] Implement get_rate_limit_status method in mcp_servers/rate_limiter.py
- [ ] T093 [US5] Integrate RateLimiter with MetaGraphClient in mcp_servers/meta_graph_client.py (check before each API call)
- [ ] T094 [US5] Add rate limit error handling to all MetaGraphClient methods in mcp_servers/meta_graph_client.py
- [ ] T095 [US5] Implement request queue for rate-limited requests in mcp_servers/rate_limiter.py
- [ ] T096 [US5] Add rate limit status to MCP server error responses in mcp_servers/facebook_instagram_mcp_server.py

**Checkpoint**: At this point, all user stories are complete - rate limiting protects all API operations

---

## Phase 8: Integration Tests (End-to-End Workflows)

**Purpose**: Verify complete workflows across multiple user stories

- [ ] T097 [P] Write test_e2e_facebook_post_workflow in tests/test_integration_social_workflow.py (approval → post → metrics)
- [ ] T098 [P] Write test_e2e_instagram_post_workflow in tests/test_integration_social_workflow.py (approval → post → metrics)
- [ ] T099 [P] Write test_e2e_scheduled_post_workflow in tests/test_integration_social_workflow.py (schedule → approve → publish)
- [ ] T100 [P] Write test_e2e_rate_limit_recovery_workflow in tests/test_integration_social_workflow.py (throttle → queue → retry)
- [ ] T101 [P] Write test_e2e_error_recovery_workflow in tests/test_integration_social_workflow.py (network error → retry → success)

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T102 [P] Add comprehensive error messages for all validation failures in mcp_servers/image_validator.py
- [ ] T103 [P] Add risk level calculation logic to approval request creation in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T104 [P] Add content preview generation (first 200 chars) to approval requests in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T105 [P] Add token validation on MCP server startup in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T106 [P] Add rate limit status monitoring endpoint in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T107 [P] Update .env.example with all configuration options and comments
- [ ] T108 [P] Create test fixtures for mocked Meta API responses in tests/conftest.py
- [ ] T109 [P] Add error handling for missing environment variables in mcp_servers/facebook_instagram_mcp_server.py
- [ ] T110 Run all tests to verify complete system functionality
- [ ] T111 Manual testing: Post to Facebook page and verify on facebook.com
- [ ] T112 Manual testing: Post to Instagram and verify on instagram.com
- [ ] T113 Manual testing: Retrieve metrics and verify accuracy against Meta Business Suite
- [ ] T114 Validate quickstart.md setup instructions are accurate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User Story 1 (Facebook): Can start after Foundational - No dependencies on other stories
  - User Story 2 (Instagram): Can start after Foundational - No dependencies on other stories
  - User Story 3 (Metrics): Can start after Foundational - No dependencies on other stories
  - User Story 4 (Scheduling): Can start after Foundational - Integrates with US1 and US2 but independently testable
  - User Story 5 (Rate Limiting): Can start after Foundational - Integrates with all stories but independently testable
- **Integration Tests (Phase 8)**: Depends on all user stories being complete
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent - Can complete without any other story
- **User Story 2 (P1)**: Independent - Can complete without any other story
- **User Story 3 (P2)**: Independent - Can complete without any other story (uses existing posts for testing)
- **User Story 4 (P2)**: Integrates with US1 and US2 but independently testable (adds scheduling to existing post handlers)
- **User Story 5 (P3)**: Integrates with all stories but independently testable (adds rate limiting layer)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/validators before services/clients
- Services/clients before MCP handlers
- MCP handlers before execution functions
- Core implementation before audit logging
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 2 (Foundational)**: All 6 tasks can run in parallel (T004-T009)

**Phase 3 (US1 Tests)**: All 7 test tasks can run in parallel (T010-T016)

**Phase 3 (US1 Implementation)**:
- T017-T018 can run in parallel (ImageValidator methods)
- T019-T020 can run in parallel (MetaGraphClient methods)
- T021-T022 can run in parallel (tool definitions)

**Phase 4 (US2 Tests)**: All 7 test tasks can run in parallel (T029-T035)

**Phase 4 (US2 Implementation)**:
- T036-T037 can run in parallel (ImageValidator methods)
- T038-T041 can run in parallel (MetaGraphClient methods)
- T042-T043 can run in parallel (tool definitions)

**Phase 5 (US3 Tests)**: All 7 test tasks can run in parallel (T050-T056)

**Phase 5 (US3 Implementation)**:
- T058-T061 can run in parallel (MetaGraphClient methods)
- T062-T065 can run in parallel (tool definitions)

**Phase 6 (US4 Tests)**: All 4 test tasks can run in parallel (T071-T074)

**Phase 7 (US5 Tests)**: All 6 test tasks can run in parallel (T082-T087)

**Phase 7 (US5 Implementation)**:
- T088-T092 can run in parallel (RateLimiter methods)

**Phase 8 (Integration Tests)**: All 5 test tasks can run in parallel (T097-T101)

**Phase 9 (Polish)**: Tasks T102-T109 can run in parallel

**Cross-Story Parallelism**: After Foundational phase completes, User Stories 1, 2, and 3 can be worked on in parallel by different developers

---

## Parallel Example: User Story 1 (Facebook Posting)

```bash
# Launch all tests for User Story 1 together:
Task: "Write test_facebook_post_text_creates_approval in tests/test_facebook_instagram_mcp_server.py"
Task: "Write test_facebook_post_image_validates_image in tests/test_facebook_instagram_mcp_server.py"
Task: "Write test_facebook_post_image_creates_approval in tests/test_facebook_instagram_mcp_server.py"
Task: "Write test_execute_facebook_post_text_success in tests/test_meta_graph_client.py"
Task: "Write test_execute_facebook_post_image_success in tests/test_meta_graph_client.py"
Task: "Write test_facebook_image_validation_size_limit in tests/test_image_validator.py"
Task: "Write test_facebook_image_validation_format in tests/test_image_validator.py"

# After tests fail, launch ImageValidator methods in parallel:
Task: "Implement validate_facebook_image method in mcp_servers/image_validator.py"
Task: "Implement get_image_info method in mcp_servers/image_validator.py"

# Then launch MetaGraphClient methods in parallel:
Task: "Implement post_to_facebook_page method in mcp_servers/meta_graph_client.py"
Task: "Implement post_image_to_facebook method in mcp_servers/meta_graph_client.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T009) - CRITICAL
3. Complete Phase 3: User Story 1 - Facebook Posting (T010-T028)
4. Complete Phase 4: User Story 2 - Instagram Posting (T029-T049)
5. **STOP and VALIDATE**: Test both stories independently
6. Deploy/demo if ready

**MVP Delivers**: Core posting functionality for both platforms with approval workflow

### Incremental Delivery

1. **Foundation** (Phases 1-2): Setup + Foundational → Infrastructure ready
2. **MVP** (Phases 3-4): US1 + US2 → Test independently → Deploy/Demo
3. **Metrics** (Phase 5): US3 → Test independently → Deploy/Demo
4. **Scheduling** (Phase 6): US4 → Test independently → Deploy/Demo
5. **Rate Limiting** (Phase 7): US5 → Test independently → Deploy/Demo
6. **Integration** (Phase 8): End-to-end tests → Validate complete system
7. **Polish** (Phase 9): Cross-cutting improvements → Production ready

Each increment adds value without breaking previous functionality.

### Parallel Team Strategy

With multiple developers:

1. **Together**: Complete Setup + Foundational (Phases 1-2)
2. **Once Foundational is done**:
   - Developer A: User Story 1 (Facebook Posting)
   - Developer B: User Story 2 (Instagram Posting)
   - Developer C: User Story 3 (Metrics Retrieval)
3. **Sequential**: User Stories 4 and 5 (integrate with existing stories)
4. **Together**: Integration tests and polish

---

## Task Summary

**Total Tasks**: 114
- Phase 1 (Setup): 3 tasks
- Phase 2 (Foundational): 6 tasks
- Phase 3 (US1 - Facebook): 19 tasks (7 tests + 12 implementation)
- Phase 4 (US2 - Instagram): 21 tasks (7 tests + 14 implementation)
- Phase 5 (US3 - Metrics): 20 tasks (7 tests + 13 implementation)
- Phase 6 (US4 - Scheduling): 11 tasks (4 tests + 7 implementation)
- Phase 7 (US5 - Rate Limiting): 15 tasks (6 tests + 9 implementation)
- Phase 8 (Integration): 5 tasks (end-to-end tests)
- Phase 9 (Polish): 14 tasks (cross-cutting improvements)

**Parallel Opportunities**: 67 tasks marked [P] can run in parallel within their phase

**MVP Scope**: Phases 1-4 (49 tasks) - Facebook and Instagram posting with approval workflow

**Independent Test Criteria**:
- US1: Post to Facebook, verify on facebook.com, check audit log
- US2: Post to Instagram, verify on instagram.com, check audit log
- US3: Retrieve metrics, verify cache hit on second request
- US4: Schedule post, verify publishes at correct time
- US5: Make rapid API calls, verify throttling and queuing

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All tasks follow strict checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

---

**Tasks Status**: ✅ COMPLETE - Ready for implementation
**Next Command**: `/sp.implement` to execute tasks with TDD approach
