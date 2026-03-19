"""Meta Graph API Client for Facebook & Instagram MCP Server.

Provides base client for interacting with Meta Graph API:
- Authentication and token management
- Facebook page posting (text and images)
- Instagram business account posting (images and carousels)
- Engagement metrics retrieval
- Rate limiting integration
- Error recovery with retry patterns
- Approval workflow integration
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

# Add scripts directory to path for error recovery imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from error_recovery.decorators import with_retry, with_circuit_breaker

# Import rate limiter
from .rate_limiter import RateLimiter

# Load environment variables
load_dotenv()


class MetaGraphClient:
    """
    Client for interacting with Meta Graph API (Facebook & Instagram).

    Handles authentication, rate limiting, and provides methods for:
    - Posting to Facebook pages (text and images)
    - Posting to Instagram business accounts (images and carousels)
    - Retrieving engagement metrics
    - Page and account insights

    All write operations require approval workflow integration.
    """

    def __init__(self):
        """Initialize Meta Graph API client with configuration from environment variables."""
        # API Configuration
        self.api_version = os.getenv("META_GRAPH_API_VERSION", "v19.0")
        self.base_url = os.getenv("META_GRAPH_API_BASE_URL", "https://graph.facebook.com")
        self.api_url = f"{self.base_url}/{self.api_version}"

        # Facebook Configuration
        self.facebook_page_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
        self.facebook_page_id = os.getenv("FACEBOOK_PAGE_ID")

        # Instagram Configuration
        self.instagram_token = os.getenv("INSTAGRAM_BUSINESS_ACCESS_TOKEN")
        self.instagram_account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

        # Rate Limiter
        rate_limit_threshold = float(os.getenv("META_RATE_LIMIT_THRESHOLD", "0.8"))
        rate_limit_cooldown = int(os.getenv("META_RATE_LIMIT_COOLDOWN", "3600"))
        self.rate_limiter = RateLimiter(
            threshold=rate_limit_threshold,
            cooldown_seconds=rate_limit_cooldown
        )

        # Session for connection pooling
        self.session = requests.Session()

    def _check_rate_limit(self, endpoint: str):
        """
        Check rate limit before making API request.

        Args:
            endpoint: API endpoint name

        Raises:
            Exception: If rate limit exceeded
        """
        is_allowed, reason = self.rate_limiter.check_rate_limit(endpoint)
        if not is_allowed:
            raise Exception(f"Rate limit check failed: {reason}")

    def _update_rate_limit(self, endpoint: str, response: requests.Response):
        """
        Update rate limit state from API response.

        Args:
            endpoint: API endpoint name
            response: Response from Meta API
        """
        self.rate_limiter.update_rate_limit(endpoint, dict(response.headers))

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(service_name="meta_graph_api")
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request to Meta Graph API with error handling.

        Args:
            method: HTTP method (GET, POST, DELETE)
            url: Full URL to request
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            Exception: If request fails
        """
        response = self.session.request(method, url, **kwargs)

        # Check for API errors
        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                error_code = error_data.get('error', {}).get('code', 'Unknown')
                raise Exception(f"Meta API error {error_code}: {error_msg}")
            except (json.JSONDecodeError, KeyError):
                response.raise_for_status()

        return response

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(service_name="facebook_post")
    def post_to_facebook_page(self, message: str, link: Optional[str] = None,
                               scheduled_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Post text to Facebook page.

        Args:
            message: Post content (max 63,206 characters)
            link: Optional URL to attach
            scheduled_time: Optional ISO 8601 timestamp for scheduling

        Returns:
            Dictionary with post_id and created_time

        Raises:
            Exception: If posting fails or tokens not configured
        """
        try:
            if not self.facebook_page_token or not self.facebook_page_id:
                raise Exception("Facebook credentials not configured. Set FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID")

            # Check rate limit
            try:
                self._check_rate_limit("facebook_post")
            except Exception as e:
                raise Exception(f"[FB-STEP-1] Rate limit check failed: {e}")

            # Build request
            url = f"{self.api_url}/{self.facebook_page_id}/feed"
            data = {
                "message": message,
                "access_token": self.facebook_page_token
            }

            if link:
                data["link"] = link

            if scheduled_time:
                # Convert ISO 8601 to Unix timestamp
                dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                data["scheduled_publish_time"] = int(dt.timestamp())
                data["published"] = False

            # Make request
            try:
                response = self._make_request("POST", url, data=data)
            except Exception as e:
                raise Exception(f"[FB-STEP-2] API request failed: {e}")

            # Update rate limit
            try:
                self._update_rate_limit("facebook_post", response)
            except Exception as e:
                # Log warning but don't fail the post
                print(f"⚠️ Warning: Rate limit update failed: {e}")
                pass

            result = response.json()

            # Handle unexpected response format
            if isinstance(result, list):
                # If result is a list, try to get the first item
                if len(result) > 0 and isinstance(result[0], dict):
                    result = result[0]
                else:
                    raise Exception(f"Unexpected Facebook API response format (list): {result}")
            elif not isinstance(result, dict):
                raise Exception(f"Unexpected Facebook API response type: {type(result)}")

            return {
                "post_id": result.get("id"),
                "created_time": datetime.utcnow().isoformat()
            }
        except Exception as e:
            # Re-raise with context
            raise Exception(f"post_to_facebook_page error: {e}")

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(service_name="facebook_post")
    def post_image_to_facebook(self, message: str, image_path: str,
                                scheduled_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Post image with caption to Facebook page.

        Args:
            message: Post caption
            image_path: Local path to image file
            scheduled_time: Optional ISO 8601 timestamp for scheduling

        Returns:
            Dictionary with post_id and created_time

        Raises:
            Exception: If posting fails or image not found
        """
        if not self.facebook_page_token or not self.facebook_page_id:
            raise Exception("Facebook credentials not configured")

        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Check rate limit
        self._check_rate_limit("facebook_post")

        # Build request
        url = f"{self.api_url}/{self.facebook_page_id}/photos"
        data = {
            "message": message,
            "access_token": self.facebook_page_token
        }

        if scheduled_time:
            dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            data["scheduled_publish_time"] = int(dt.timestamp())
            data["published"] = False

        # Upload image
        with open(image_path, 'rb') as image_file:
            files = {'source': image_file}
            response = self._make_request("POST", url, data=data, files=files)

        # Update rate limit
        self._update_rate_limit("facebook_post", response)

        result = response.json()
        return {
            "post_id": result.get("id"),
            "created_time": datetime.utcnow().isoformat()
        }

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(service_name="instagram_post")
    def create_instagram_container(self, image_path: str, caption: str) -> str:
        """
        Create Instagram media container (step 1 of 2-step publishing).

        Args:
            image_path: Local path to image file
            caption: Post caption (max 2,200 characters)

        Returns:
            Container ID

        Raises:
            Exception: If container creation fails
        """
        if not self.instagram_token or not self.instagram_account_id:
            raise Exception("Instagram credentials not configured")

        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Check rate limit
        self._check_rate_limit("instagram_post")

        # Upload image to a publicly accessible URL (Meta requires URL, not file upload)
        # For now, we'll use the local file path and let Meta handle it
        # In production, you'd upload to CDN first
        url = f"{self.api_url}/{self.instagram_account_id}/media"
        data = {
            "image_url": image_path,  # This needs to be a public URL in production
            "caption": caption,
            "access_token": self.instagram_token
        }

        response = self._make_request("POST", url, data=data)

        # Update rate limit
        self._update_rate_limit("instagram_post", response)

        result = response.json()
        return result.get("id")

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(service_name="instagram_post")
    def publish_instagram_container(self, container_id: str) -> Dict[str, Any]:
        """
        Publish Instagram media container (step 2 of 2-step publishing).

        Args:
            container_id: Container ID from create_instagram_container

        Returns:
            Dictionary with media_id and created_time

        Raises:
            Exception: If publishing fails
        """
        if not self.instagram_token or not self.instagram_account_id:
            raise Exception("Instagram credentials not configured")

        # Check rate limit
        self._check_rate_limit("instagram_post")

        url = f"{self.api_url}/{self.instagram_account_id}/media_publish"
        data = {
            "creation_id": container_id,
            "access_token": self.instagram_token
        }

        response = self._make_request("POST", url, data=data)

        # Update rate limit
        self._update_rate_limit("instagram_post", response)

        result = response.json()
        return {
            "media_id": result.get("id"),
            "created_time": datetime.utcnow().isoformat()
        }

    def post_to_instagram(self, image_path: str, caption: str,
                          scheduled_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Post image to Instagram (combines create + publish).

        Args:
            image_path: Local path to image file
            caption: Post caption
            scheduled_time: Optional ISO 8601 timestamp (not supported by Instagram API)

        Returns:
            Dictionary with media_id and created_time

        Raises:
            Exception: If posting fails
        """
        if scheduled_time:
            raise Exception("Instagram does not support scheduled posts via API")

        # Step 1: Create container
        container_id = self.create_instagram_container(image_path, caption)

        # Step 2: Publish container
        return self.publish_instagram_container(container_id)

    def post_carousel_to_instagram(self, image_paths: List[str], caption: str) -> Dict[str, Any]:
        """
        Post carousel (multiple images) to Instagram.

        Args:
            image_paths: List of local image paths (2-10 images)
            caption: Post caption

        Returns:
            Dictionary with media_id and created_time

        Raises:
            Exception: If posting fails or invalid number of images
        """
        if not 2 <= len(image_paths) <= 10:
            raise ValueError("Carousel must have 2-10 images")

        # Implementation would create multiple containers and combine them
        # This is a simplified version - full implementation in later tasks
        raise NotImplementedError("Carousel posting will be implemented in Phase 4")

    @with_circuit_breaker(service_name="meta_metrics")
    def get_facebook_post_metrics(self, post_id: str, metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get engagement metrics for Facebook post.

        Args:
            post_id: Facebook post ID
            metrics: List of metrics to retrieve (default: all)

        Returns:
            Dictionary with metric values

        Raises:
            Exception: If retrieval fails
        """
        if not self.facebook_page_token:
            raise Exception("Facebook credentials not configured")

        # Default metrics
        if not metrics:
            metrics = ['likes', 'comments', 'shares', 'reactions', 'reach', 'impressions']

        url = f"{self.api_url}/{post_id}"
        params = {
            "fields": ",".join(metrics),
            "access_token": self.facebook_page_token
        }

        response = self._make_request("GET", url, params=params)
        return response.json()

    @with_circuit_breaker(service_name="meta_metrics")
    def get_instagram_post_metrics(self, media_id: str, metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get engagement metrics for Instagram post.

        Args:
            media_id: Instagram media ID
            metrics: List of metrics to retrieve (default: all)

        Returns:
            Dictionary with metric values

        Raises:
            Exception: If retrieval fails
        """
        if not self.instagram_token:
            raise Exception("Instagram credentials not configured")

        # Default metrics
        if not metrics:
            metrics = ['likes', 'comments', 'saves', 'reach', 'impressions', 'engagement']

        url = f"{self.api_url}/{media_id}/insights"
        params = {
            "metric": ",".join(metrics),
            "access_token": self.instagram_token
        }

        response = self._make_request("GET", url, params=params)
        return response.json()

    def get_facebook_page_insights(self, page_id: Optional[str] = None,
                                    period: str = "week") -> Dict[str, Any]:
        """
        Get insights for Facebook page.

        Args:
            page_id: Facebook page ID (uses default if not provided)
            period: Time period (day, week, month)

        Returns:
            Dictionary with insight data

        Raises:
            Exception: If retrieval fails
        """
        page_id = page_id or self.facebook_page_id
        if not self.facebook_page_token or not page_id:
            raise Exception("Facebook credentials not configured")

        url = f"{self.api_url}/{page_id}/insights"
        params = {
            "period": period,
            "access_token": self.facebook_page_token
        }

        response = self._make_request("GET", url, params=params)
        return response.json()

    def get_instagram_account_insights(self, account_id: Optional[str] = None,
                                        period: str = "week") -> Dict[str, Any]:
        """
        Get insights for Instagram business account.

        Args:
            account_id: Instagram account ID (uses default if not provided)
            period: Time period (day, week, month)

        Returns:
            Dictionary with insight data

        Raises:
            Exception: If retrieval fails
        """
        account_id = account_id or self.instagram_account_id
        if not self.instagram_token or not account_id:
            raise Exception("Instagram credentials not configured")

        url = f"{self.api_url}/{account_id}/insights"
        params = {
            "period": period,
            "access_token": self.instagram_token
        }

        response = self._make_request("GET", url, params=params)
        return response.json()


# Approval Workflow Helper Functions (T007)

def generate_approval_id(platform: str, action: str) -> str:
    """
    Generate unique approval ID for social media post.

    Format: SOCIAL_{PLATFORM}_{ACTION}_{TIMESTAMP}
    Example: SOCIAL_FACEBOOK_POST_20260318_143022

    Args:
        platform: Platform name (facebook, instagram)
        action: Action type (post_text, post_image, post_carousel)

    Returns:
        Unique approval ID
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"SOCIAL_{platform.upper()}_{action.upper()}_{timestamp}"


def create_approval_request_file(approval_id: str, action_type: str,
                                   content_preview: str, target_account: str,
                                   risk_level: str, metadata: Dict[str, Any],
                                   vault_path: str = "./AI_Employee_Vault") -> str:
    """
    Create approval request file in Pending_Approval/ directory.

    Args:
        approval_id: Unique approval ID
        action_type: Type of action (facebook_post, instagram_post)
        content_preview: Preview of content (first 200 chars)
        target_account: Target page/account ID
        risk_level: Risk level (low, medium, high)
        metadata: Additional metadata (image_path, scheduled_time, etc.)
        vault_path: Path to AI Employee Vault

    Returns:
        Path to created approval file

    Raises:
        Exception: If file creation fails
    """
    pending_dir = Path(vault_path) / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{approval_id}.md"
    filepath = pending_dir / filename

    # Build approval request content
    content = f"""# Social Media Post Approval Request

**Approval ID:** {approval_id}
**Action Type:** {action_type}
**Target Account:** {target_account}
**Risk Level:** {risk_level}
**Created:** {datetime.utcnow().isoformat()}

---

## Content Preview

{content_preview}

---

## Metadata

```json
{json.dumps(metadata, indent=2)}
```

---

## Instructions

To approve this post:
1. Review the content preview and metadata above
2. Move this file to `AI_Employee_Vault/Approved/`
3. The approval executor will publish the post

To deny this post:
1. Delete this file or move to `AI_Employee_Vault/Denied/`
2. The post will not be published

---

**Status:** PENDING_APPROVAL
"""

    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return str(filepath)
