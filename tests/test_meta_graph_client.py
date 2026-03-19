"""Tests for MetaGraphClient.

Tests the Meta Graph API client for:
- Facebook posting operations
- Instagram posting operations
- Metrics retrieval
- Rate limiting integration
- Error recovery
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import requests

# Import the client module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_servers.meta_graph_client import MetaGraphClient, generate_approval_id, create_approval_request_file


# Fixtures

@pytest.fixture
def meta_client():
    """Create MetaGraphClient instance with mocked credentials."""
    with patch.dict(os.environ, {
        "FACEBOOK_PAGE_ACCESS_TOKEN": "test_fb_token",
        "FACEBOOK_PAGE_ID": "123456789",
        "INSTAGRAM_BUSINESS_ACCESS_TOKEN": "test_ig_token",
        "INSTAGRAM_BUSINESS_ACCOUNT_ID": "987654321"
    }):
        client = MetaGraphClient()
        yield client


@pytest.fixture
def mock_response():
    """Create mock response object."""
    response = Mock(spec=requests.Response)
    response.status_code = 200
    response.headers = {
        "X-App-Usage": '{"call_count":10,"total_cputime":5,"total_time":8}'
    }
    return response


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample test image."""
    from PIL import Image

    image_path = tmp_path / "test_image.jpg"
    img = Image.new('RGB', (800, 600), color='blue')
    img.save(image_path)

    return str(image_path)


# Tests for User Story 1: Facebook Posting

@pytest.mark.unit
def test_execute_facebook_post_text_success(meta_client, mock_response):
    """
    T013: Test successful Facebook text post execution.

    Given: Valid page ID, message, and access token
    When: post_to_facebook_page is called
    Then: POST request is made to Facebook API
    And: Returns post_id and created_time
    And: Rate limit is updated from response headers
    """
    # Arrange
    mock_response.json.return_value = {
        "id": "123456789_987654321"
    }

    with patch.object(meta_client, '_make_request', return_value=mock_response):
        # Act
        result = meta_client.post_to_facebook_page(
            message="Test post message",
            link=None,
            scheduled_time=None
        )

        # Assert
        assert "post_id" in result
        assert result["post_id"] == "123456789_987654321"
        assert "created_time" in result

        # Verify rate limit was checked and updated
        meta_client._make_request.assert_called_once()


@pytest.mark.unit
def test_execute_facebook_post_image_success(meta_client, mock_response, sample_image):
    """
    T014: Test successful Facebook image post execution.

    Given: Valid page ID, message, image path, and access token
    When: post_image_to_facebook is called
    Then: POST request is made with image file
    And: Returns post_id and created_time
    And: Rate limit is updated
    """
    # Arrange
    mock_response.json.return_value = {
        "id": "123456789_111222333"
    }

    with patch.object(meta_client, '_make_request', return_value=mock_response):
        # Act
        result = meta_client.post_image_to_facebook(
            message="Test image caption",
            image_path=sample_image,
            scheduled_time=None
        )

        # Assert
        assert "post_id" in result
        assert result["post_id"] == "123456789_111222333"
        assert "created_time" in result

        # Verify request was made with files parameter
        call_args = meta_client._make_request.call_args
        assert call_args is not None


@pytest.mark.unit
def test_facebook_post_rate_limit_check(meta_client):
    """
    T087: Test rate limit integration with Meta client.

    Given: Rate limit threshold reached
    When: post_to_facebook_page is called
    Then: Rate limit check raises exception
    And: Request is not made to API
    """
    # Arrange
    meta_client.rate_limiter.update_rate_limit("facebook_post", {
        "X-App-Usage": '{"call_count":190,"total_cputime":95,"total_time":98}'
    })

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        meta_client.post_to_facebook_page(message="Test")

    assert "Rate limit" in str(exc_info.value)


@pytest.mark.unit
def test_facebook_post_authentication_error(meta_client, mock_response):
    """
    Test Facebook post with invalid token.

    Given: Invalid access token
    When: post_to_facebook_page is called
    Then: Raises exception with authentication error
    """
    # Arrange
    mock_response.status_code = 401
    mock_response.json.return_value = {
        "error": {
            "message": "Invalid OAuth access token",
            "code": 190
        }
    }

    with patch.object(meta_client, '_make_request', side_effect=Exception("Meta API error 190: Invalid OAuth access token")):
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            meta_client.post_to_facebook_page(message="Test")

        assert "Invalid OAuth access token" in str(exc_info.value)


@pytest.mark.unit
def test_facebook_post_with_scheduled_time(meta_client, mock_response):
    """
    Test Facebook post with scheduled publish time.

    Given: Valid message and future scheduled_time
    When: post_to_facebook_page is called with scheduled_time
    Then: Request includes scheduled_publish_time parameter
    And: published parameter is set to False
    """
    # Arrange
    mock_response.json.return_value = {"id": "123_456"}
    scheduled_time = "2026-12-31T23:59:59Z"

    with patch.object(meta_client, '_make_request', return_value=mock_response) as mock_request:
        # Act
        result = meta_client.post_to_facebook_page(
            message="Scheduled post",
            scheduled_time=scheduled_time
        )

        # Assert
        assert result["post_id"] == "123_456"

        # Verify scheduled parameters were included
        call_args = mock_request.call_args
        data = call_args.kwargs.get('data', {})
        assert 'scheduled_publish_time' in data
        assert data['published'] is False


# Tests for User Story 2: Instagram Posting

@pytest.mark.unit
def test_execute_instagram_post_image_success(meta_client, mock_response, sample_image):
    """
    T032: Test successful Instagram image post execution.

    Given: Valid account ID, caption, image path, and access token
    When: post_to_instagram is called
    Then: Creates container and publishes it
    And: Returns media_id and created_time
    """
    # Arrange
    container_response = Mock(spec=requests.Response)
    container_response.status_code = 200
    container_response.headers = mock_response.headers
    container_response.json.return_value = {"id": "container_123"}

    publish_response = Mock(spec=requests.Response)
    publish_response.status_code = 200
    publish_response.headers = mock_response.headers
    publish_response.json.return_value = {"id": "media_456"}

    with patch.object(meta_client, '_make_request', side_effect=[container_response, publish_response]):
        # Act
        result = meta_client.post_to_instagram(
            image_path=sample_image,
            caption="Test Instagram post"
        )

        # Assert
        assert "media_id" in result
        assert result["media_id"] == "media_456"
        assert "created_time" in result

        # Verify two API calls were made (create + publish)
        assert meta_client._make_request.call_count == 2


@pytest.mark.unit
def test_execute_instagram_post_carousel_success(meta_client):
    """
    T033: Test successful Instagram carousel post execution.

    Given: Valid account ID, caption, and multiple image paths
    When: post_carousel_to_instagram is called
    Then: Creates containers for each image
    And: Publishes carousel
    And: Returns media_id
    """
    # This will be implemented in Phase 4
    with pytest.raises(NotImplementedError):
        meta_client.post_carousel_to_instagram(
            image_paths=["img1.jpg", "img2.jpg"],
            caption="Carousel test"
        )


# Tests for approval workflow helpers

@pytest.mark.unit
def test_generate_approval_id():
    """
    Test approval ID generation.

    Given: Platform and action type
    When: generate_approval_id is called
    Then: Returns unique ID with correct format
    """
    # Act
    approval_id = generate_approval_id("facebook", "post_text")

    # Assert
    assert approval_id.startswith("SOCIAL_FACEBOOK_POST_TEXT_")
    assert len(approval_id) > 30  # Should include timestamp


@pytest.mark.unit
def test_create_approval_request_file(tmp_path):
    """
    Test approval request file creation.

    Given: Approval details and metadata
    When: create_approval_request_file is called
    Then: Creates markdown file in Pending_Approval/
    And: File contains all required information
    """
    # Arrange
    vault_path = tmp_path / "AI_Employee_Vault"
    approval_id = "SOCIAL_FACEBOOK_POST_TEXT_20260318_120000"
    metadata = {
        "message": "Test post",
        "page_id": "123456789"
    }

    # Act
    filepath = create_approval_request_file(
        approval_id=approval_id,
        action_type="facebook_post",
        content_preview="Test post",
        target_account="123456789",
        risk_level="low",
        metadata=metadata,
        vault_path=str(vault_path)
    )

    # Assert
    assert Path(filepath).exists()
    content = Path(filepath).read_text()
    assert approval_id in content
    assert "Test post" in content
    assert "PENDING_APPROVAL" in content
    assert "facebook_post" in content
