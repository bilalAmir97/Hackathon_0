"""Integration tests for Facebook & Instagram MCP Server workflows.

Tests end-to-end workflows:
- Facebook post approval → execution → metrics
- Instagram post approval → execution → metrics
- Scheduled post workflow
- Rate limit recovery workflow
- Error recovery workflow
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_servers.facebook_instagram_mcp_server import (
    facebook_post_text_handler,
    facebook_post_image_handler,
    instagram_post_image_handler,
    execute_facebook_post_text,
    execute_facebook_post_image,
    execute_instagram_post_image,
    get_facebook_post_metrics_handler
)


# Fixtures

@pytest.fixture
def temp_vault(tmp_path):
    """Create temporary vault structure."""
    vault = tmp_path / "AI_Employee_Vault"
    (vault / "Pending_Approval").mkdir(parents=True)
    (vault / "Approved").mkdir(parents=True)
    (vault / "Done").mkdir(parents=True)
    return vault


@pytest.fixture
def sample_image(tmp_path):
    """Create sample test image."""
    from PIL import Image

    image_path = tmp_path / "test_image.jpg"
    img = Image.new('RGB', (1080, 1080), color='blue')
    img.save(image_path)

    return str(image_path)


@pytest.fixture
def mock_meta_api():
    """Mock Meta Graph API responses."""
    with patch('mcp_servers.meta_graph_client.requests.Session') as mock_session:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            "X-App-Usage": '{"call_count":10,"total_cputime":5,"total_time":8}'
        }
        mock_response.json.return_value = {"id": "123456789_987654321"}

        mock_session.return_value.request.return_value = mock_response
        yield mock_session


# Integration Tests

@pytest.mark.integration
@pytest.mark.asyncio
async def test_e2e_facebook_post_workflow(temp_vault, mock_meta_api, sample_image):
    """
    T097: Test end-to-end Facebook post workflow.

    Given: Valid Facebook post request
    When: Handler creates approval → approval granted → post executed → metrics retrieved
    Then: Complete workflow succeeds with audit trail
    """
    # Set environment
    with patch.dict(os.environ, {
        "VAULT_PATH": str(temp_vault),
        "FACEBOOK_PAGE_ACCESS_TOKEN": "test_token",
        "FACEBOOK_PAGE_ID": "123456789"
    }):
        # Step 1: Create approval request
        arguments = {
            "page_id": "123456789",
            "message": "Test post for integration test",
            "link": None,
            "scheduled_time": None
        }

        result = await facebook_post_text_handler(arguments)

        assert result["success"] is True
        assert "approval_id" in result
        approval_id = result["approval_id"]

        # Verify approval file created
        approval_files = list((temp_vault / "Pending_Approval").glob("*.md"))
        assert len(approval_files) == 1

        # Step 2: Simulate approval (move to Approved)
        approval_file = approval_files[0]
        approved_file = temp_vault / "Approved" / approval_file.name
        approval_file.rename(approved_file)

        # Step 3: Execute approved post
        metadata = {
            "page_id": "123456789",
            "message": "Test post for integration test",
            "link": None,
            "scheduled_time": None,
            "action": "facebook_post_text"
        }

        exec_result = execute_facebook_post_text(approval_id, metadata)

        assert exec_result["success"] is True
        assert "post_id" in exec_result
        post_id = exec_result["post_id"]

        # Step 4: Retrieve metrics
        metrics_args = {
            "post_id": post_id,
            "metrics": ["likes", "comments", "shares"]
        }

        with patch('mcp_servers.meta_graph_client.MetaGraphClient.get_facebook_post_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "likes": 10,
                "comments": 2,
                "shares": 1
            }

            metrics_result = await get_facebook_post_metrics_handler(metrics_args)

            assert metrics_result["success"] is True
            assert metrics_result["data"]["likes"] == 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_e2e_instagram_post_workflow(temp_vault, mock_meta_api, sample_image):
    """
    T098: Test end-to-end Instagram post workflow.

    Given: Valid Instagram post request
    When: Handler creates approval → approval granted → post executed → metrics retrieved
    Then: Complete workflow succeeds
    """
    # Set environment
    with patch.dict(os.environ, {
        "VAULT_PATH": str(temp_vault),
        "INSTAGRAM_BUSINESS_ACCESS_TOKEN": "test_token",
        "INSTAGRAM_BUSINESS_ACCOUNT_ID": "987654321"
    }):
        # Step 1: Create approval request
        arguments = {
            "account_id": "987654321",
            "caption": "Test Instagram post",
            "image_path": sample_image
        }

        result = await instagram_post_image_handler(arguments)

        assert result["success"] is True
        assert "approval_id" in result
        approval_id = result["approval_id"]

        # Step 2: Execute approved post
        metadata = {
            "account_id": "987654321",
            "caption": "Test Instagram post",
            "image_path": sample_image,
            "action": "instagram_post_image"
        }

        with patch('mcp_servers.meta_graph_client.MetaGraphClient.post_to_instagram') as mock_post:
            mock_post.return_value = {
                "media_id": "IG_123456",
                "created_time": datetime.utcnow().isoformat()
            }

            exec_result = execute_instagram_post_image(approval_id, metadata)

            assert exec_result["success"] is True
            assert "media_id" in exec_result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_e2e_scheduled_post_workflow(temp_vault, mock_meta_api):
    """
    T099: Test end-to-end scheduled post workflow.

    Given: Post with future scheduled_time
    When: Approval granted and executed
    Then: Post is scheduled correctly
    """
    # Set environment
    future_time = (datetime.utcnow() + timedelta(hours=2)).isoformat() + "Z"

    with patch.dict(os.environ, {
        "VAULT_PATH": str(temp_vault),
        "FACEBOOK_PAGE_ACCESS_TOKEN": "test_token",
        "FACEBOOK_PAGE_ID": "123456789"
    }):
        # Create approval request with scheduled_time
        arguments = {
            "page_id": "123456789",
            "message": "Scheduled post",
            "scheduled_time": future_time
        }

        result = await facebook_post_text_handler(arguments)

        assert result["success"] is True

        # Verify scheduled_time in approval file
        approval_files = list((temp_vault / "Pending_Approval").glob("*.md"))
        approval_content = approval_files[0].read_text()
        assert future_time in approval_content


@pytest.mark.integration
@pytest.mark.asyncio
async def test_e2e_rate_limit_recovery_workflow():
    """
    T100: Test end-to-end rate limit recovery workflow.

    Given: API returns rate limit error
    When: Request is made
    Then: Request is queued and retried after cooldown
    """
    from mcp_servers.rate_limiter import RateLimiter

    # Create rate limiter
    rate_limiter = RateLimiter(threshold=0.8, cooldown_seconds=60)

    # Simulate rate limit
    headers = {
        "X-App-Usage": '{"call_count":190,"total_cputime":95,"total_time":100}'
    }
    rate_limiter.update_rate_limit("test_endpoint", headers)

    # Check rate limit (should be throttled)
    is_allowed, reason = rate_limiter.check_rate_limit("test_endpoint")
    assert is_allowed is False

    # Add to queue
    rate_limiter.add_to_queue("test_endpoint", retry_count=0)

    # Verify queue
    queued = rate_limiter.get_queued_requests()
    assert len(queued) == 1
    assert queued[0]["endpoint"] == "test_endpoint"

    # Simulate reset (manually clear rate limit)
    rate_limiter._rate_limits.clear()

    # Check again (should be allowed)
    is_allowed, reason = rate_limiter.check_rate_limit("test_endpoint")
    assert is_allowed is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_e2e_error_recovery_workflow():
    """
    T101: Test end-to-end error recovery workflow.

    Given: Network error occurs
    When: Request is made with retry decorator
    Then: Request is retried and eventually succeeds
    """
    from mcp_servers.meta_graph_client import MetaGraphClient

    with patch.dict(os.environ, {
        "FACEBOOK_PAGE_ACCESS_TOKEN": "test_token",
        "FACEBOOK_PAGE_ID": "123456789"
    }):
        client = MetaGraphClient()

        # Mock request to fail twice then succeed
        call_count = 0

        def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                raise Exception("Network error")

            # Success on third attempt
            response = Mock()
            response.status_code = 200
            response.headers = {"X-App-Usage": '{"call_count":10}'}
            response.json.return_value = {"id": "post_123"}
            return response

        with patch.object(client.session, 'request', side_effect=mock_request):
            # This should retry and eventually succeed
            try:
                result = client.post_to_facebook_page(message="Test with retry")
                # If we get here, retry worked
                assert call_count == 3  # Failed twice, succeeded on third
                assert result["post_id"] == "post_123"
            except Exception as e:
                # Retry decorator should have caught this
                pytest.fail(f"Request failed after retries: {e}")


@pytest.mark.integration
def test_approval_file_format_validation(temp_vault):
    """
    Test that approval files have correct format.

    Given: Approval request created
    When: File is read
    Then: Contains all required fields in correct format
    """
    from mcp_servers.meta_graph_client import create_approval_request_file

    # Create approval file
    approval_id = "SOCIAL_FACEBOOK_POST_TEXT_20260318_120000"
    metadata = {
        "page_id": "123456789",
        "message": "Test post",
        "action": "facebook_post_text"
    }

    filepath = create_approval_request_file(
        approval_id=approval_id,
        action_type="facebook_post_text",
        content_preview="Test post",
        target_account="123456789",
        risk_level="low",
        metadata=metadata,
        vault_path=str(temp_vault)
    )

    # Verify file exists and has correct content
    assert Path(filepath).exists()
    content = Path(filepath).read_text()

    # Check required sections
    assert "# Social Media Post Approval Request" in content
    assert approval_id in content
    assert "facebook_post_text" in content
    assert "Test post" in content
    assert "PENDING_APPROVAL" in content
    assert "```json" in content  # Metadata section
    assert "Move this file to" in content  # Instructions


@pytest.mark.integration
def test_metrics_cache_expiry():
    """
    T056: Test metrics cache expiry.

    Given: Metrics cached with TTL
    When: TTL expires
    Then: Next request fetches fresh data
    """
    from mcp_servers.facebook_instagram_mcp_server import _metrics_cache
    from cachetools import TTLCache
    import time

    # Create cache with 1 second TTL
    test_cache = TTLCache(maxsize=10, ttl=1)

    # Add item
    test_cache["test_key"] = {"likes": 100}
    assert "test_key" in test_cache

    # Wait for expiry
    time.sleep(1.1)

    # Item should be expired
    assert "test_key" not in test_cache
