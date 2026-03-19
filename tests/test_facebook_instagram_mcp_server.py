"""Tests for Facebook & Instagram MCP Server.

Tests the MCP server handlers for:
- Facebook posting (text and images)
- Instagram posting (images and carousels)
- Metrics retrieval
- Approval workflow integration
- Rate limiting
- Error handling
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the MCP server module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_servers.facebook_instagram_mcp_server import (
    facebook_post_text_handler,
    facebook_post_image_handler,
    instagram_post_image_handler,
    instagram_post_carousel_handler,
    get_facebook_post_metrics_handler,
    get_instagram_post_metrics_handler,
    get_meta_client,
    get_image_validator,
    get_audit_logger
)


# Fixtures

@pytest.fixture
def mock_meta_client():
    """Mock MetaGraphClient for testing."""
    client = Mock()
    with patch('mcp_servers.facebook_instagram_mcp_server.get_meta_client', return_value=client):
        yield client


@pytest.fixture
def mock_image_validator():
    """Mock ImageValidator for testing."""
    validator = Mock()
    with patch('mcp_servers.facebook_instagram_mcp_server.get_image_validator', return_value=validator):
        yield validator


@pytest.fixture
def mock_audit_logger():
    """Mock AuditLogger for testing."""
    logger = Mock()
    with patch('mcp_servers.facebook_instagram_mcp_server.get_audit_logger', return_value=logger):
        yield logger


@pytest.fixture
def temp_approval_dir(tmp_path):
    """Create temporary approval directory."""
    approval_dir = tmp_path / "AI_Employee_Vault" / "Pending_Approval"
    approval_dir.mkdir(parents=True)
    return approval_dir


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample test image."""
    from PIL import Image

    image_path = tmp_path / "test_image.jpg"
    img = Image.new('RGB', (800, 600), color='red')
    img.save(image_path)

    return str(image_path)


# Tests for User Story 1: Facebook Posting

@pytest.mark.unit
@pytest.mark.asyncio
async def test_facebook_post_text_creates_approval(temp_approval_dir, mock_audit_logger):
    """
    T010: Test that facebook_post_text creates approval request.

    Given: Valid Facebook page ID and message
    When: facebook_post_text_handler is called
    Then: Approval request file is created in Pending_Approval/
    And: Returns approval_id and status
    """
    # Arrange
    arguments = {
        "page_id": "123456789",
        "message": "Test post message",
        "link": None,
        "scheduled_time": None
    }

    # Set VAULT_PATH to parent of Pending_Approval (AI_Employee_Vault)
    with patch.dict(os.environ, {"VAULT_PATH": str(temp_approval_dir.parent)}):
        # Act
        result = await facebook_post_text_handler(arguments)

        # Assert
        assert result["success"] is True
        assert "approval_id" in result
        assert result["status"] == "pending_approval"

        # Check approval file was created
        approval_files = list(temp_approval_dir.glob("SOCIAL_FACEBOOK_*.md"))
        assert len(approval_files) == 1

        # Verify file content
        approval_content = approval_files[0].read_text()
        assert "Test post message" in approval_content
        assert "PENDING_APPROVAL" in approval_content


@pytest.mark.unit
@pytest.mark.asyncio
async def test_facebook_post_image_validates_image(sample_image, mock_image_validator):
    """
    T011: Test that facebook_post_image validates image before creating approval.

    Given: Image path and message
    When: facebook_post_image_handler is called
    Then: Image is validated using ImageValidator
    And: Validation errors are returned if image is invalid
    """
    # Arrange
    mock_image_validator.validate_facebook_image.return_value = (False, "Image too large")

    arguments = {
        "page_id": "123456789",
        "message": "Test caption",
        "image_path": sample_image,
        "scheduled_time": None
    }

    # Act
    result = await facebook_post_image_handler(arguments)

    # Assert
    assert result["success"] is False
    assert "Image too large" in result["error"]
    mock_image_validator.validate_facebook_image.assert_called_once_with(sample_image)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_facebook_post_image_creates_approval(sample_image, temp_approval_dir,
                                                     mock_image_validator, mock_audit_logger):
    """
    T012: Test that facebook_post_image creates approval request for valid image.

    Given: Valid image and message
    When: facebook_post_image_handler is called
    Then: Approval request file is created
    And: Image path is included in metadata
    """
    # Arrange
    mock_image_validator.validate_facebook_image.return_value = (True, None)
    mock_image_validator.get_image_info.return_value = {
        'path': sample_image,
        'format': 'JPEG',
        'size_mb': 0.5,
        'width': 800,
        'height': 600,
        'aspect_ratio': 1.33
    }

    arguments = {
        "page_id": "123456789",
        "message": "Test caption",
        "image_path": sample_image,
        "scheduled_time": None
    }

    with patch.dict(os.environ, {"VAULT_PATH": str(temp_approval_dir.parent)}):
        # Act
        result = await facebook_post_image_handler(arguments)

        # Assert
        assert result["success"] is True
        assert "approval_id" in result
        assert result["status"] == "pending_approval"

        # Check approval file was created
        approval_files = list(temp_approval_dir.glob("SOCIAL_FACEBOOK_*.md"))
        assert len(approval_files) == 1

        # Verify image path in metadata
        approval_content = approval_files[0].read_text()
        assert sample_image in approval_content
        assert "Test caption" in approval_content


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_facebook_post_metrics_cache_miss(mock_meta_client, mock_audit_logger):
    """
    T050: Test metrics retrieval with cache miss.

    Given: Post ID not in cache
    When: get_facebook_post_metrics_handler is called
    Then: Metrics are fetched from API
    And: Metrics are cached for future requests
    """
    # Arrange
    mock_meta_client.get_facebook_post_metrics.return_value = {
        "likes": 100,
        "comments": 20,
        "shares": 5
    }

    arguments = {
        "post_id": "post_123",
        "metrics": ["likes", "comments", "shares"]
    }

    # Act
    result = await get_facebook_post_metrics_handler(arguments)

    # Assert
    assert result["success"] is True
    assert result["data"]["likes"] == 100
    assert result["data"]["comments"] == 20
    assert result["data"]["shares"] == 5
    assert result["cached"] is False

    mock_meta_client.get_facebook_post_metrics.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_facebook_post_metrics_cache_hit(mock_meta_client, mock_audit_logger):
    """
    T051: Test metrics retrieval with cache hit.

    Given: Post ID already in cache
    When: get_facebook_post_metrics_handler is called
    Then: Metrics are returned from cache
    And: API is not called
    """
    # Arrange
    from mcp_servers.facebook_instagram_mcp_server import _metrics_cache

    cache_key = "facebook_post_123"
    cached_data = {
        "likes": 100,
        "comments": 20,
        "shares": 5
    }
    _metrics_cache[cache_key] = cached_data

    arguments = {
        "post_id": "post_123",
        "metrics": ["likes", "comments", "shares"]
    }

    # Act
    result = await get_facebook_post_metrics_handler(arguments)

    # Assert
    assert result["success"] is True
    assert result["data"] == cached_data
    assert result["cached"] is True

    # API should not be called
    mock_meta_client.get_facebook_post_metrics.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_schedule_facebook_post_creates_approval(temp_approval_dir, mock_audit_logger):
    """
    T071: Test that scheduled Facebook post creates approval request.

    Given: Valid message and future scheduled_time
    When: facebook_post_text_handler is called with scheduled_time
    Then: Approval request includes scheduled_time in metadata
    And: Status is pending_approval
    """
    # Arrange
    future_time = "2026-12-31T23:59:59Z"
    arguments = {
        "page_id": "123456789",
        "message": "Scheduled post",
        "scheduled_time": future_time
    }

    with patch.dict(os.environ, {"VAULT_PATH": str(temp_approval_dir.parent)}):
        # Act
        result = await facebook_post_text_handler(arguments)

        # Assert
        assert result["success"] is True
        assert "approval_id" in result

        # Verify scheduled_time in approval file
        approval_files = list(temp_approval_dir.glob("SOCIAL_FACEBOOK_*.md"))
        assert len(approval_files) == 1
        approval_content = approval_files[0].read_text()
        assert future_time in approval_content


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scheduled_post_validation_past_time():
    """
    T074: Test that scheduled posts with past time are rejected.

    Given: Message with scheduled_time in the past
    When: facebook_post_text_handler is called
    Then: Returns error about invalid scheduled_time
    """
    # Arrange
    past_time = "2020-01-01T00:00:00Z"
    arguments = {
        "page_id": "123456789",
        "message": "Test post",
        "scheduled_time": past_time
    }

    # Act
    result = await facebook_post_text_handler(arguments)

    # Assert
    assert result["success"] is False
    assert "future" in result["error"].lower() or "past" in result["error"].lower() or "invalid" in result["error"].lower()
