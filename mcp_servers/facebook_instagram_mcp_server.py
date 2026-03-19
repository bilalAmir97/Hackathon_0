"""Facebook & Instagram MCP Server.

This MCP server exposes social media operations for Facebook pages and
Instagram business accounts using the Meta Graph API.

Features:
- Post text and images to Facebook pages
- Post images and carousels to Instagram business accounts
- Retrieve engagement metrics for posts
- Schedule posts with approval workflow
- Handle rate limits gracefully with proactive throttling
- Error recovery with retry patterns and circuit breaker
- Audit logging for all operations
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from mcp.server import Server
from mcp.types import Tool, TextContent
from cachetools import TTLCache

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.audit_logger import AuditLogger

# Import our modules
from .meta_graph_client import MetaGraphClient, generate_approval_id, create_approval_request_file
from .image_validator import ImageValidator
from .rate_limiter import RateLimiter

# Initialize MCP server
app = Server("facebook-instagram-mcp-server")

# Global instances (initialized on first use)
_meta_client: Optional[MetaGraphClient] = None
_image_validator: Optional[ImageValidator] = None
_audit_logger: Optional[AuditLogger] = None

# Metrics cache (5 minutes TTL, max 100 entries)
METRICS_CACHE_TTL = int(os.getenv("META_METRICS_CACHE_TTL", "300"))
METRICS_CACHE_SIZE = int(os.getenv("META_METRICS_CACHE_SIZE", "100"))
_metrics_cache = TTLCache(maxsize=METRICS_CACHE_SIZE, ttl=METRICS_CACHE_TTL)


def get_meta_client() -> MetaGraphClient:
    """Get or create MetaGraphClient instance."""
    global _meta_client
    if _meta_client is None:
        _meta_client = MetaGraphClient()
    return _meta_client


def get_image_validator() -> ImageValidator:
    """Get or create ImageValidator instance."""
    global _image_validator
    if _image_validator is None:
        facebook_max_mb = float(os.getenv("FACEBOOK_MAX_IMAGE_SIZE_MB", "4"))
        instagram_max_mb = float(os.getenv("INSTAGRAM_MAX_IMAGE_SIZE_MB", "8"))
        _image_validator = ImageValidator(
            facebook_max_size_mb=facebook_max_mb,
            instagram_max_size_mb=instagram_max_mb
        )
    return _image_validator


def get_audit_logger() -> AuditLogger:
    """Get or create AuditLogger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def validate_environment_variables() -> tuple[bool, list[str]]:
    """
    Validate required environment variables on startup.

    Returns:
        Tuple of (is_valid, list of missing variables)
    """
    missing = []

    # Check Facebook credentials
    if not os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN"):
        missing.append("FACEBOOK_PAGE_ACCESS_TOKEN")
    if not os.getenv("FACEBOOK_PAGE_ID"):
        missing.append("FACEBOOK_PAGE_ID")

    # Check Instagram credentials
    if not os.getenv("INSTAGRAM_BUSINESS_ACCESS_TOKEN"):
        missing.append("INSTAGRAM_BUSINESS_ACCESS_TOKEN")
    if not os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID"):
        missing.append("INSTAGRAM_BUSINESS_ACCOUNT_ID")

    return len(missing) == 0, missing


def validate_tokens_on_startup() -> dict:
    """
    Validate access tokens on MCP server startup.

    Returns:
        Dictionary with validation results
    """
    results = {
        "facebook": {"valid": False, "error": None},
        "instagram": {"valid": False, "error": None}
    }

    try:
        client = get_meta_client()

        # Validate Facebook token
        if client.facebook_page_token and client.facebook_page_id:
            try:
                # Make a simple API call to validate token
                url = f"{client.api_url}/{client.facebook_page_id}"
                params = {"access_token": client.facebook_page_token, "fields": "id,name"}
                response = client._make_request("GET", url, params=params)

                if response.status_code == 200:
                    results["facebook"]["valid"] = True
                else:
                    results["facebook"]["error"] = "Invalid token or page ID"
            except Exception as e:
                results["facebook"]["error"] = str(e)

        # Validate Instagram token
        if client.instagram_token and client.instagram_account_id:
            try:
                # Make a simple API call to validate token
                url = f"{client.api_url}/{client.instagram_account_id}"
                params = {"access_token": client.instagram_token, "fields": "id,username"}
                response = client._make_request("GET", url, params=params)

                if response.status_code == 200:
                    results["instagram"]["valid"] = True
                else:
                    results["instagram"]["error"] = "Invalid token or account ID"
            except Exception as e:
                results["instagram"]["error"] = str(e)

    except Exception as e:
        results["error"] = f"Token validation failed: {e}"

    return results


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available social media tools."""
    return [
        # Facebook Tools
        Tool(
            name="facebook_post_text",
            description="Post text to Facebook page with approval workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Facebook page ID (optional, uses default from .env)"
                    },
                    "message": {
                        "type": "string",
                        "description": "Post content (max 63,206 characters)"
                    },
                    "link": {
                        "type": "string",
                        "description": "Optional URL to attach"
                    },
                    "scheduled_time": {
                        "type": "string",
                        "description": "Optional ISO 8601 timestamp for scheduling"
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="facebook_post_image",
            description="Post image with caption to Facebook page with approval workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Facebook page ID (optional, uses default from .env)"
                    },
                    "message": {
                        "type": "string",
                        "description": "Post caption"
                    },
                    "image_path": {
                        "type": "string",
                        "description": "Local path to image file"
                    },
                    "scheduled_time": {
                        "type": "string",
                        "description": "Optional ISO 8601 timestamp for scheduling"
                    }
                },
                "required": ["message", "image_path"]
            }
        ),

        # Instagram Tools
        Tool(
            name="instagram_post_image",
            description="Post image with caption to Instagram business account with approval workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Instagram business account ID (optional, uses default from .env)"
                    },
                    "caption": {
                        "type": "string",
                        "description": "Post caption (max 2,200 characters)"
                    },
                    "image_path": {
                        "type": "string",
                        "description": "Local path to image file"
                    }
                },
                "required": ["caption", "image_path"]
            }
        ),
        Tool(
            name="instagram_post_carousel",
            description="Post carousel (multiple images) to Instagram business account with approval workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Instagram business account ID (optional, uses default from .env)"
                    },
                    "caption": {
                        "type": "string",
                        "description": "Post caption (max 2,200 characters)"
                    },
                    "image_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of local image paths (2-10 images)"
                    }
                },
                "required": ["caption", "image_paths"]
            }
        ),

        # Metrics Tools
        Tool(
            name="get_facebook_post_metrics",
            description="Get engagement metrics for Facebook post",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {
                        "type": "string",
                        "description": "Facebook post ID"
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of metrics (likes, comments, shares, reactions, reach, impressions)"
                    }
                },
                "required": ["post_id"]
            }
        ),
        Tool(
            name="get_instagram_post_metrics",
            description="Get engagement metrics for Instagram post",
            inputSchema={
                "type": "object",
                "properties": {
                    "media_id": {
                        "type": "string",
                        "description": "Instagram media ID"
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of metrics (likes, comments, saves, reach, impressions, engagement)"
                    }
                },
                "required": ["media_id"]
            }
        ),
        Tool(
            name="get_facebook_page_insights",
            description="Get insights for Facebook page",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Facebook page ID (optional, uses default from .env)"
                    },
                    "period": {
                        "type": "string",
                        "description": "Time period: day, week, or month (default: week)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_instagram_account_insights",
            description="Get insights for Instagram business account",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Instagram business account ID (optional, uses default from .env)"
                    },
                    "period": {
                        "type": "string",
                        "description": "Time period: day, week, or month (default: week)"
                    }
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        # Route to appropriate handler
        if name == "facebook_post_text":
            result = await facebook_post_text_handler(arguments)
        elif name == "facebook_post_image":
            result = await facebook_post_image_handler(arguments)
        elif name == "instagram_post_image":
            result = await instagram_post_image_handler(arguments)
        elif name == "instagram_post_carousel":
            result = await instagram_post_carousel_handler(arguments)
        elif name == "get_facebook_post_metrics":
            result = await get_facebook_post_metrics_handler(arguments)
        elif name == "get_instagram_post_metrics":
            result = await get_instagram_post_metrics_handler(arguments)
        elif name == "get_facebook_page_insights":
            result = await get_facebook_page_insights_handler(arguments)
        elif name == "get_instagram_account_insights":
            result = await get_instagram_account_insights_handler(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "tool": name
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


# Handler functions

async def facebook_post_text_handler(arguments: dict) -> dict:
    """
    Handle facebook_post_text tool call.

    Creates approval request for Facebook text post.
    Includes FR9.1 formatting: preserve line breaks, auto-link URLs, support @mentions/hashtags.

    Args:
        arguments: Tool arguments (page_id, message, link, scheduled_time)

    Returns:
        Dictionary with success status, approval_id, and approval_file_path
    """
    try:
        # Extract arguments
        page_id = arguments.get("page_id") or os.getenv("FACEBOOK_PAGE_ID")
        message = arguments.get("message")
        link = arguments.get("link")
        scheduled_time = arguments.get("scheduled_time")

        # Validate required fields
        if not message:
            return {
                "success": False,
                "error": "Message is required"
            }

        if not page_id:
            return {
                "success": False,
                "error": "Facebook page ID not configured. Set FACEBOOK_PAGE_ID in .env"
            }

        # Validate scheduled_time if provided
        if scheduled_time:
            try:
                scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                if scheduled_dt <= datetime.utcnow().replace(tzinfo=scheduled_dt.tzinfo):
                    return {
                        "success": False,
                        "error": "Scheduled time must be in the future"
                    }
            except (ValueError, AttributeError) as e:
                return {
                    "success": False,
                    "error": f"Invalid scheduled_time format: {e}"
                }

        # Generate approval ID
        approval_id = generate_approval_id("facebook", "post_text")

        # Create content preview (first 200 chars)
        content_preview = message[:200] + ("..." if len(message) > 200 else "")

        # Build metadata
        metadata = {
            "page_id": page_id,
            "message": message,
            "link": link,
            "scheduled_time": scheduled_time,
            "action": "facebook_post_text"
        }

        # Calculate risk level (simple heuristic)
        risk_level = "low"
        if len(message) > 1000 or scheduled_time:
            risk_level = "medium"

        # Create approval request file
        vault_path = os.getenv("VAULT_PATH", "./AI_Employee_Vault")
        approval_file = create_approval_request_file(
            approval_id=approval_id,
            action_type="facebook_post_text",
            content_preview=content_preview,
            target_account=page_id,
            risk_level=risk_level,
            metadata=metadata,
            vault_path=vault_path
        )

        # Log action
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="facebook_post_text_request",
            actor="mcp_server",
            target=f"facebook_page_{page_id}",
            parameters={"approval_id": approval_id, "message_length": len(message)},
            result="approval_created"
        )

        return {
            "success": True,
            "status": "pending_approval",
            "approval_id": approval_id,
            "approval_file": approval_file,
            "message": f"Approval request created. Move {Path(approval_file).name} to Approved/ to publish."
        }

    except Exception as e:
        # Log error
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="facebook_post_text_request",
            actor="mcp_server",
            target="facebook_page",
            parameters={"error": str(e)},
            result="error"
        )

        return {
            "success": False,
            "error": str(e)
        }


async def facebook_post_image_handler(arguments: dict) -> dict:
    """
    Handle facebook_post_image tool call.

    Validates image and creates approval request for Facebook image post.

    Args:
        arguments: Tool arguments (page_id, message, image_path, scheduled_time)

    Returns:
        Dictionary with success status, approval_id, and approval_file_path
    """
    try:
        # Extract arguments
        page_id = arguments.get("page_id") or os.getenv("FACEBOOK_PAGE_ID")
        message = arguments.get("message")
        image_path = arguments.get("image_path")
        scheduled_time = arguments.get("scheduled_time")

        # Validate required fields
        if not message:
            return {
                "success": False,
                "error": "Message is required"
            }

        if not image_path:
            return {
                "success": False,
                "error": "Image path is required"
            }

        if not page_id:
            return {
                "success": False,
                "error": "Facebook page ID not configured. Set FACEBOOK_PAGE_ID in .env"
            }

        # Validate image
        validator = get_image_validator()
        is_valid, error = validator.validate_facebook_image(image_path)

        if not is_valid:
            return {
                "success": False,
                "error": f"Image validation failed: {error}"
            }

        # Get image info for metadata
        image_info = validator.get_image_info(image_path)

        # Validate scheduled_time if provided
        if scheduled_time:
            try:
                scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                if scheduled_dt <= datetime.utcnow().replace(tzinfo=scheduled_dt.tzinfo):
                    return {
                        "success": False,
                        "error": "Scheduled time must be in the future"
                    }
            except (ValueError, AttributeError) as e:
                return {
                    "success": False,
                    "error": f"Invalid scheduled_time format: {e}"
                }

        # Generate approval ID
        approval_id = generate_approval_id("facebook", "post_image")

        # Create content preview
        content_preview = f"{message[:150]}...\n\n[Image: {Path(image_path).name}, {image_info['width']}x{image_info['height']}px, {image_info['size_mb']}MB]"

        # Build metadata
        metadata = {
            "page_id": page_id,
            "message": message,
            "image_path": image_path,
            "image_info": image_info,
            "scheduled_time": scheduled_time,
            "action": "facebook_post_image"
        }

        # Calculate risk level
        risk_level = "medium"  # Image posts are medium risk by default
        if scheduled_time:
            risk_level = "high"

        # Create approval request file
        vault_path = os.getenv("VAULT_PATH", "./AI_Employee_Vault")
        approval_file = create_approval_request_file(
            approval_id=approval_id,
            action_type="facebook_post_image",
            content_preview=content_preview,
            target_account=page_id,
            risk_level=risk_level,
            metadata=metadata,
            vault_path=vault_path
        )

        # Log action
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="facebook_post_image_request",
            actor="mcp_server",
            target=f"facebook_page_{page_id}",
            parameters={
                "approval_id": approval_id,
                "image_size_mb": image_info['size_mb'],
                "image_dimensions": f"{image_info['width']}x{image_info['height']}"
            },
            result="approval_created"
        )

        return {
            "success": True,
            "status": "pending_approval",
            "approval_id": approval_id,
            "approval_file": approval_file,
            "image_info": image_info,
            "message": f"Approval request created. Move {Path(approval_file).name} to Approved/ to publish."
        }

    except Exception as e:
        # Log error
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="facebook_post_image_request",
            actor="mcp_server",
            target="facebook_page",
            parameters={"error": str(e)},
            result="error"
        )

        return {
            "success": False,
            "error": str(e)
        }


async def instagram_post_image_handler(arguments: dict) -> dict:
    """
    Handle instagram_post_image tool call.

    Validates image and creates approval request for Instagram image post.
    Includes FR9.2 formatting: preserve line breaks, support @mentions/hashtags, emoji support.

    Args:
        arguments: Tool arguments (account_id, caption, image_path)

    Returns:
        Dictionary with success status, approval_id, and approval_file_path
    """
    try:
        # Extract arguments
        account_id = arguments.get("account_id") or os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        caption = arguments.get("caption")
        image_path = arguments.get("image_path")

        # Validate required fields
        if not caption:
            return {
                "success": False,
                "error": "Caption is required"
            }

        if not image_path:
            return {
                "success": False,
                "error": "Image path is required"
            }

        if not account_id:
            return {
                "success": False,
                "error": "Instagram account ID not configured. Set INSTAGRAM_BUSINESS_ACCOUNT_ID in .env"
            }

        # Validate caption length
        if len(caption) > 2200:
            return {
                "success": False,
                "error": f"Caption too long ({len(caption)} chars). Maximum 2,200 characters."
            }

        # Validate image
        validator = get_image_validator()
        is_valid, error = validator.validate_instagram_image(image_path)

        if not is_valid:
            return {
                "success": False,
                "error": f"Image validation failed: {error}"
            }

        # Get image info for metadata
        image_info = validator.get_image_info(image_path)

        # Generate approval ID
        approval_id = generate_approval_id("instagram", "post_image")

        # Create content preview
        content_preview = f"{caption[:150]}...\n\n[Image: {Path(image_path).name}, {image_info['width']}x{image_info['height']}px, {image_info['size_mb']}MB, aspect ratio {image_info['aspect_ratio']}]"

        # Build metadata
        metadata = {
            "account_id": account_id,
            "caption": caption,
            "image_path": image_path,
            "image_info": image_info,
            "action": "instagram_post_image"
        }

        # Calculate risk level
        risk_level = "medium"  # Instagram posts are medium risk by default

        # Create approval request file
        vault_path = os.getenv("VAULT_PATH", "./AI_Employee_Vault")
        approval_file = create_approval_request_file(
            approval_id=approval_id,
            action_type="instagram_post_image",
            content_preview=content_preview,
            target_account=account_id,
            risk_level=risk_level,
            metadata=metadata,
            vault_path=vault_path
        )

        # Log action
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="instagram_post_image_request",
            actor="mcp_server",
            target=f"instagram_account_{account_id}",
            parameters={
                "approval_id": approval_id,
                "image_size_mb": image_info['size_mb'],
                "image_dimensions": f"{image_info['width']}x{image_info['height']}",
                "aspect_ratio": image_info['aspect_ratio']
            },
            result="approval_created"
        )

        return {
            "success": True,
            "status": "pending_approval",
            "approval_id": approval_id,
            "approval_file": approval_file,
            "image_info": image_info,
            "message": f"Approval request created. Move {Path(approval_file).name} to Approved/ to publish."
        }

    except Exception as e:
        # Log error
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="instagram_post_image_request",
            actor="mcp_server",
            target="instagram_account",
            parameters={"error": str(e)},
            result="error"
        )

        return {
            "success": False,
            "error": str(e)
        }


async def instagram_post_carousel_handler(arguments: dict) -> dict:
    """
    Handle instagram_post_carousel tool call.

    Validates images and creates approval request for Instagram carousel post.

    Args:
        arguments: Tool arguments (account_id, caption, image_paths)

    Returns:
        Dictionary with success status, approval_id, and approval_file_path
    """
    try:
        # Extract arguments
        account_id = arguments.get("account_id") or os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        caption = arguments.get("caption")
        image_paths = arguments.get("image_paths", [])

        # Validate required fields
        if not caption:
            return {
                "success": False,
                "error": "Caption is required"
            }

        if not image_paths:
            return {
                "success": False,
                "error": "Image paths are required"
            }

        if not account_id:
            return {
                "success": False,
                "error": "Instagram account ID not configured. Set INSTAGRAM_BUSINESS_ACCOUNT_ID in .env"
            }

        # Validate caption length
        if len(caption) > 2200:
            return {
                "success": False,
                "error": f"Caption too long ({len(caption)} chars). Maximum 2,200 characters."
            }

        # Validate number of images
        if not isinstance(image_paths, list):
            return {
                "success": False,
                "error": "image_paths must be an array"
            }

        if len(image_paths) < 2 or len(image_paths) > 10:
            return {
                "success": False,
                "error": f"Carousel must have 2-10 images. Provided: {len(image_paths)}"
            }

        # Validate all images
        validator = get_image_validator()
        validated_images = []

        for idx, image_path in enumerate(image_paths):
            is_valid, error = validator.validate_instagram_image(image_path)

            if not is_valid:
                return {
                    "success": False,
                    "error": f"Image {idx + 1} validation failed: {error}"
                }

            # Get image info
            image_info = validator.get_image_info(image_path)
            validated_images.append(image_info)

        # Generate approval ID
        approval_id = generate_approval_id("instagram", "post_carousel")

        # Create content preview
        image_summary = ", ".join([f"{img['width']}x{img['height']}" for img in validated_images])
        content_preview = f"{caption[:150]}...\n\n[Carousel: {len(image_paths)} images - {image_summary}]"

        # Build metadata
        metadata = {
            "account_id": account_id,
            "caption": caption,
            "image_paths": image_paths,
            "images_info": validated_images,
            "action": "instagram_post_carousel"
        }

        # Calculate risk level
        risk_level = "high"  # Carousel posts are high risk (multiple images)

        # Create approval request file
        vault_path = os.getenv("VAULT_PATH", "./AI_Employee_Vault")
        approval_file = create_approval_request_file(
            approval_id=approval_id,
            action_type="instagram_post_carousel",
            content_preview=content_preview,
            target_account=account_id,
            risk_level=risk_level,
            metadata=metadata,
            vault_path=vault_path
        )

        # Log action
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="instagram_post_carousel_request",
            actor="mcp_server",
            target=f"instagram_account_{account_id}",
            parameters={
                "approval_id": approval_id,
                "image_count": len(image_paths)
            },
            result="approval_created"
        )

        return {
            "success": True,
            "status": "pending_approval",
            "approval_id": approval_id,
            "approval_file": approval_file,
            "images_info": validated_images,
            "message": f"Approval request created. Move {Path(approval_file).name} to Approved/ to publish."
        }

    except Exception as e:
        # Log error
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="instagram_post_carousel_request",
            actor="mcp_server",
            target="instagram_account",
            parameters={"error": str(e)},
            result="error"
        )

        return {
            "success": False,
            "error": str(e)
        }



async def get_facebook_post_metrics_handler(arguments: dict) -> dict:
    """
    Handle get_facebook_post_metrics tool call.

    Retrieves engagement metrics for Facebook post with caching.

    Args:
        arguments: Tool arguments (post_id, metrics)

    Returns:
        Dictionary with success status, metrics data, and cache status
    """
    try:
        # Extract arguments
        post_id = arguments.get("post_id")
        metrics = arguments.get("metrics")

        # Validate required fields
        if not post_id:
            return {
                "success": False,
                "error": "Post ID is required"
            }

        # Check cache first
        cache_key = f"facebook_post_{post_id}"
        if cache_key in _metrics_cache:
            cached_data = _metrics_cache[cache_key]

            # Log cache hit
            audit_logger = get_audit_logger()
            audit_logger.log_action(

                action_type="get_facebook_post_metrics",
                actor="mcp_server",
                target=f"facebook_post_{post_id}",
                parameters={"cache_hit": True},
                result="success"
            )

            return {
                "success": True,
                "data": cached_data,
                "cached": True,
                "post_id": post_id
            }

        # Cache miss - fetch from API
        client = get_meta_client()
        metrics_data = client.get_facebook_post_metrics(
            post_id=post_id,
            metrics=metrics
        )

        # Store in cache
        _metrics_cache[cache_key] = metrics_data

        # Log cache miss
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="get_facebook_post_metrics",
            actor="mcp_server",
            target=f"facebook_post_{post_id}",
            parameters={"cache_hit": False, "metrics": metrics},
            result="success"
        )

        return {
            "success": True,
            "data": metrics_data,
            "cached": False,
            "post_id": post_id
        }

    except Exception as e:
        # Log error
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="get_facebook_post_metrics",
            actor="mcp_server",
            target=f"facebook_post_{arguments.get('post_id')}",
            parameters={"error": str(e)},
            result="error"
        )

        return {
            "success": False,
            "error": str(e)
        }


async def get_instagram_post_metrics_handler(arguments: dict) -> dict:
    """
    Handle get_instagram_post_metrics tool call.

    Retrieves engagement metrics for Instagram post with caching.

    Args:
        arguments: Tool arguments (media_id, metrics)

    Returns:
        Dictionary with success status, metrics data, and cache status
    """
    try:
        # Extract arguments
        media_id = arguments.get("media_id")
        metrics = arguments.get("metrics")

        # Validate required fields
        if not media_id:
            return {
                "success": False,
                "error": "Media ID is required"
            }

        # Check cache first
        cache_key = f"instagram_post_{media_id}"
        if cache_key in _metrics_cache:
            cached_data = _metrics_cache[cache_key]

            # Log cache hit
            audit_logger = get_audit_logger()
            audit_logger.log_action(

                action_type="get_instagram_post_metrics",
                actor="mcp_server",
                target=f"instagram_post_{media_id}",
                parameters={"cache_hit": True},
                result="success"
            )

            return {
                "success": True,
                "data": cached_data,
                "cached": True,
                "media_id": media_id
            }

        # Cache miss - fetch from API
        client = get_meta_client()
        metrics_data = client.get_instagram_post_metrics(
            media_id=media_id,
            metrics=metrics
        )

        # Store in cache
        _metrics_cache[cache_key] = metrics_data

        # Log cache miss
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="get_instagram_post_metrics",
            actor="mcp_server",
            target=f"instagram_post_{media_id}",
            parameters={"cache_hit": False, "metrics": metrics},
            result="success"
        )

        return {
            "success": True,
            "data": metrics_data,
            "cached": False,
            "media_id": media_id
        }

    except Exception as e:
        # Log error
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="get_instagram_post_metrics",
            actor="mcp_server",
            target=f"instagram_post_{arguments.get('media_id')}",
            parameters={"error": str(e)},
            result="error"
        )

        return {
            "success": False,
            "error": str(e)
        }


async def get_facebook_page_insights_handler(arguments: dict) -> dict:
    """
    Handle get_facebook_page_insights tool call.

    Retrieves insights for Facebook page.

    Args:
        arguments: Tool arguments (page_id, period)

    Returns:
        Dictionary with success status and insights data
    """
    try:
        # Extract arguments
        page_id = arguments.get("page_id")
        period = arguments.get("period", "week")

        # Get Meta client
        client = get_meta_client()

        # Fetch insights
        insights_data = client.get_facebook_page_insights(
            page_id=page_id,
            period=period
        )

        # Log action
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="get_facebook_page_insights",
            actor="mcp_server",
            target=f"facebook_page_{page_id or 'default'}",
            parameters={"period": period},
            result="success"
        )

        return {
            "success": True,
            "data": insights_data,
            "period": period,
            "page_id": page_id or os.getenv("FACEBOOK_PAGE_ID")
        }

    except Exception as e:
        # Log error
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="get_facebook_page_insights",
            actor="mcp_server",
            target="facebook_page",
            parameters={"error": str(e)},
            result="error"
        )

        return {
            "success": False,
            "error": str(e)
        }


async def get_instagram_account_insights_handler(arguments: dict) -> dict:
    """
    Handle get_instagram_account_insights tool call.

    Retrieves insights for Instagram business account.

    Args:
        arguments: Tool arguments (account_id, period)

    Returns:
        Dictionary with success status and insights data
    """
    try:
        # Extract arguments
        account_id = arguments.get("account_id")
        period = arguments.get("period", "week")

        # Get Meta client
        client = get_meta_client()

        # Fetch insights
        insights_data = client.get_instagram_account_insights(
            account_id=account_id,
            period=period
        )

        # Log action
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="get_instagram_account_insights",
            actor="mcp_server",
            target=f"instagram_account_{account_id or 'default'}",
            parameters={"period": period},
            result="success"
        )

        return {
            "success": True,
            "data": insights_data,
            "period": period,
            "account_id": account_id or os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        }

    except Exception as e:
        # Log error
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="get_instagram_account_insights",
            actor="mcp_server",
            target="instagram_account",
            parameters={"error": str(e)},
            result="error"
        )

        return {
            "success": False,
            "error": str(e)
        }



# Execution functions (called by approval executor after approval)

def execute_facebook_post_text(approval_id: str, metadata: dict) -> dict:
    """
    Execute approved Facebook text post.

    Called by approval executor after approval is granted.

    Args:
        approval_id: Unique approval ID
        metadata: Post metadata from approval request

    Returns:
        Dictionary with success status, post_id, and permalink
    """
    try:
        # Validate metadata type
        if not isinstance(metadata, dict):
            raise TypeError(f"[STEP 1] metadata must be a dict, got {type(metadata).__name__}: {metadata}")

        # Extract metadata
        try:
            page_id = metadata.get("page_id")
            message = metadata.get("message")
            link = metadata.get("link")
            scheduled_time = metadata.get("scheduled_time")
        except AttributeError as e:
            raise TypeError(f"[STEP 2] Error extracting metadata: {e}. metadata type: {type(metadata)}, value: {metadata}")

        # Get Meta client
        client = get_meta_client()

        # Post to Facebook
        try:
            result = client.post_to_facebook_page(
                message=message,
                link=link,
                scheduled_time=scheduled_time
            )
        except Exception as e:
            raise Exception(f"[STEP 3] Error posting to Facebook: {e}")

        # Ensure result is a dict
        if not isinstance(result, dict):
            raise TypeError(f"[STEP 4] Expected dict from post_to_facebook_page, got {type(result)}: {result}")

        # Log successful execution
        try:
            audit_logger = get_audit_logger()
            audit_logger.log_action(
                action_type="facebook_post_text_executed",
                actor="approval_executor",
                target=f"facebook_page_{page_id or 'unknown'}",
                parameters={
                    "approval_id": approval_id,
                    "post_id": result.get("post_id"),
                    "scheduled": scheduled_time is not None
                },
                result="success"
            )
        except Exception as e:
            raise Exception(f"[STEP 5] Error in audit logging: {e}")

        return {
            "success": True,
            "post_id": result.get("post_id"),
            "created_time": result.get("created_time"),
            "approval_id": approval_id,
            "permalink": f"https://facebook.com/{result.get('post_id')}"
        }

    except Exception as e:
        # Log error
        audit_logger = get_audit_logger()
        page_id_for_log = metadata.get('page_id') if isinstance(metadata, dict) else 'unknown'
        audit_logger.log_action(
            action_type="facebook_post_text_executed",
            actor="approval_executor",
            target=f"facebook_page_{page_id_for_log}",
            parameters={"approval_id": approval_id, "error": str(e)},
            result="error"
        )

        return {
            "success": False,
            "error": str(e),
            "approval_id": approval_id
        }


def execute_facebook_post_image(approval_id: str, metadata: dict) -> dict:
    """
    Execute approved Facebook image post.

    Called by approval executor after approval is granted.

    Args:
        approval_id: Unique approval ID
        metadata: Post metadata from approval request

    Returns:
        Dictionary with success status, post_id, and permalink
    """
    try:
        # Extract metadata
        page_id = metadata.get("page_id")
        message = metadata.get("message")
        image_path = metadata.get("image_path")
        scheduled_time = metadata.get("scheduled_time")

        # Verify image still exists
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Get Meta client
        client = get_meta_client()

        # Post to Facebook
        result = client.post_image_to_facebook(
            message=message,
            image_path=image_path,
            scheduled_time=scheduled_time
        )

        # Log successful execution
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="facebook_post_image_executed",
            actor="approval_executor",
            target=f"facebook_page_{page_id}",
            parameters={
                "approval_id": approval_id,
                "post_id": result.get("post_id"),
                "image_path": image_path,
                "scheduled": scheduled_time is not None
            },
            result="success"
        )

        return {
            "success": True,
            "post_id": result.get("post_id"),
            "created_time": result.get("created_time"),
            "approval_id": approval_id,
            "permalink": f"https://facebook.com/{result.get('post_id')}"
        }

    except Exception as e:
        # Log error
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="facebook_post_image_executed",
            actor="approval_executor",
            target=f"facebook_page_{metadata.get('page_id')}",
            parameters={"approval_id": approval_id, "error": str(e)},
            result="error"
        )

        return {
            "success": False,
            "error": str(e),
            "approval_id": approval_id
        }


def execute_instagram_post_image(approval_id: str, metadata: dict) -> dict:
    """
    Execute approved Instagram image post.

    Called by approval executor after approval is granted.

    Args:
        approval_id: Unique approval ID
        metadata: Post metadata from approval request

    Returns:
        Dictionary with success status, media_id, and permalink
    """
    try:
        # Extract metadata
        account_id = metadata.get("account_id")
        caption = metadata.get("caption")
        image_path = metadata.get("image_path")

        # Verify image exists (skip check for URLs)
        is_url = image_path.startswith(('http://', 'https://'))
        if not is_url and not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Get Meta client
        client = get_meta_client()

        # Post to Instagram
        result = client.post_to_instagram(
            image_path=image_path,
            caption=caption
        )

        # Log successful execution
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="instagram_post_image_executed",
            actor="approval_executor",
            target=f"instagram_account_{account_id}",
            parameters={
                "approval_id": approval_id,
                "media_id": result.get("media_id"),
                "image_path": image_path
            },
            result="success"
        )

        return {
            "success": True,
            "media_id": result.get("media_id"),
            "created_time": result.get("created_time"),
            "approval_id": approval_id,
            "permalink": f"https://instagram.com/p/{result.get('media_id')}"
        }

    except Exception as e:
        # Log error
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="instagram_post_image_executed",
            actor="approval_executor",
            target=f"instagram_account_{metadata.get('account_id')}",
            parameters={"approval_id": approval_id, "error": str(e)},
            result="error"
        )

        return {
            "success": False,
            "error": str(e),
            "approval_id": approval_id
        }


def execute_instagram_post_carousel(approval_id: str, metadata: dict) -> dict:
    """
    Execute approved Instagram carousel post.

    Called by approval executor after approval is granted.

    Args:
        approval_id: Unique approval ID
        metadata: Post metadata from approval request

    Returns:
        Dictionary with success status, media_id, and permalink
    """
    try:
        # Extract metadata
        account_id = metadata.get("account_id")
        caption = metadata.get("caption")
        image_paths = metadata.get("image_paths", [])

        # Verify all images still exist
        for image_path in image_paths:
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")

        # Get Meta client
        client = get_meta_client()

        # Post carousel to Instagram
        result = client.post_carousel_to_instagram(
            image_paths=image_paths,
            caption=caption
        )

        # Log successful execution
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="instagram_post_carousel_executed",
            actor="approval_executor",
            target=f"instagram_account_{account_id}",
            parameters={
                "approval_id": approval_id,
                "media_id": result.get("media_id"),
                "image_count": len(image_paths)
            },
            result="success"
        )

        return {
            "success": True,
            "media_id": result.get("media_id"),
            "created_time": result.get("created_time"),
            "approval_id": approval_id,
            "permalink": f"https://instagram.com/p/{result.get('media_id')}"
        }

    except Exception as e:
        # Log error
        audit_logger = get_audit_logger()
        audit_logger.log_action(

            action_type="instagram_post_carousel_executed",
            actor="approval_executor",
            target=f"instagram_account_{metadata.get('account_id')}",
            parameters={"approval_id": approval_id, "error": str(e)},
            result="error"
        )

        return {
            "success": False,
            "error": str(e),
            "approval_id": approval_id
        }



if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    asyncio.run(main())
