"""
Twitter MCP Server

Model Context Protocol server for Twitter integration.
Provides tools for posting tweets, creating threads, monitoring mentions, and tracking metrics.

All write operations integrate with the approval workflow system.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from mcp_servers.twitter_client import TwitterClient
from mcp_servers.twitter_rate_limiter import TwitterRateLimiter, RateLimitException
from mcp_servers.image_validator import ImageValidator
from scripts.audit_logger import AuditLogger


class TwitterMCPServer:
    """
    MCP server for Twitter integration.

    Provides tools:
    - twitter_post_tweet: Post a tweet with optional images
    - twitter_post_thread: Create a tweet thread
    - twitter_get_mentions: Retrieve mentions
    - twitter_get_metrics: Get engagement metrics
    """

    def __init__(self):
        """Initialize Twitter MCP server."""
        self.client = TwitterClient()
        self.rate_limiter = TwitterRateLimiter()
        self.image_validator = ImageValidator()
        self.audit_logger = AuditLogger()

        # Vault paths
        self.vault_path = Path(os.getenv('VAULT_PATH', './AI_Employee_Vault'))
        self.pending_approval_path = self.vault_path / 'Pending_Approval'

        # Ensure directories exist
        self.pending_approval_path.mkdir(parents=True, exist_ok=True)

    def _create_approval_id(self, action_type: str) -> str:
        """
        Generate unique approval ID.

        Args:
            action_type: Type of action (e.g., 'POST_TWEET', 'POST_THREAD')

        Returns:
            Approval ID in format: SOCIAL_TWITTER_{ACTION}_{TIMESTAMP}
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"SOCIAL_TWITTER_{action_type}_{timestamp}"

    def _create_approval_request(
        self,
        approval_id: str,
        action_type: str,
        metadata: Dict[str, Any],
        reasoning: str
    ) -> str:
        """
        Create approval request file in Pending_Approval directory.

        Args:
            approval_id: Unique approval identifier
            action_type: Type of action (twitter_post_tweet, twitter_post_thread)
            metadata: Action-specific metadata
            reasoning: Human-readable explanation

        Returns:
            Path to created approval file
        """
        # Create approval request content
        content = f"""---
approval_id: {approval_id}
action_type: {action_type}
email_action_ref: social_media_post
action_params:
  platform: twitter
  post_type: {'tweet' if 'tweet' in action_type else 'thread'}
risk_assessment: low
reasoning: {reasoning}
created_at: {datetime.utcnow().isoformat()}Z
metadata:
  {self._format_metadata_yaml(metadata)}
---

# Twitter {'Tweet' if 'tweet' in action_type else 'Thread'} - Approval Request

**Approval ID:** {approval_id}
**Action Type:** {action_type}

## Content

{self._format_content_preview(metadata)}

---

**Status:** PENDING
"""

        # Write to file
        filename = f"{approval_id}.md"
        filepath = self.pending_approval_path / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(filepath)

    def _format_metadata_yaml(self, metadata: Dict[str, Any]) -> str:
        """Format metadata as YAML for approval file."""
        lines = []
        for key, value in metadata.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"    - {json.dumps(item)}")
            elif value is None:
                lines.append(f"{key}: null")
            else:
                lines.append(f"{key}: {json.dumps(value)}")
        return '\n  '.join(lines)

    def _format_content_preview(self, metadata: Dict[str, Any]) -> str:
        """Format content preview for approval file."""
        if 'text' in metadata:
            return metadata['text']
        elif 'tweets' in metadata:
            tweets = metadata['tweets']
            preview = '\n\n'.join([f"{i+1}. {tweet}" for i, tweet in enumerate(tweets)])
            return preview
        return "No content preview available"

    async def twitter_post_tweet(
        self,
        text: str,
        image_paths: Optional[List[str]] = None,
        scheduled_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a tweet to Twitter (creates approval request).

        Args:
            text: Tweet text (max 280 characters)
            image_paths: Optional list of image file paths (max 4)
            scheduled_time: Optional ISO 8601 timestamp for scheduling

        Returns:
            Dict with status, approval_id, approval_file, message
        """
        try:
            # Validate text length
            if len(text) > 280:
                return {
                    'status': 'error',
                    'error': f'Tweet text exceeds 280 characters: {len(text)} characters',
                    'message': 'Tweet text too long'
                }

            # Validate images if provided
            if image_paths:
                if len(image_paths) > 4:
                    return {
                        'status': 'error',
                        'error': 'Maximum 4 images allowed per tweet',
                        'message': 'Too many images'
                    }

                for image_path in image_paths:
                    validation = self.image_validator.validate_image(
                        image_path,
                        max_size_mb=5,  # Twitter limit
                        allowed_formats=['PNG', 'JPEG', 'GIF']
                    )
                    if not validation['valid']:
                        return {
                            'status': 'error',
                            'error': validation['error'],
                            'message': f'Image validation failed: {Path(image_path).name}'
                        }

            # Create approval request
            approval_id = self._create_approval_id('POST_TWEET')

            metadata = {
                'text': text,
                'image_paths': image_paths or [],
                'scheduled_time': scheduled_time
            }

            reasoning = f"Posting tweet: {text[:50]}{'...' if len(text) > 50 else ''}"

            approval_file = self._create_approval_request(
                approval_id=approval_id,
                action_type='twitter_post_tweet',
                metadata=metadata,
                reasoning=reasoning
            )

            # Log approval request creation
            self.audit_logger.log_action(
                action_type='twitter_post_tweet_request',
                actor='ai_employee',
                target='twitter',
                parameters={'text_length': len(text), 'images': len(image_paths) if image_paths else 0},
                result={'approval_id': approval_id, 'approval_file': approval_file},
                approval=approval_id
            )

            return {
                'status': 'approval_created',
                'approval_id': approval_id,
                'approval_file': approval_file,
                'message': f'Approval request created: {approval_id}'
            }

        except Exception as e:
            error_msg = str(e)
            self.audit_logger.log_action(
                action_type='twitter_post_tweet_request',
                actor='ai_employee',
                target='twitter',
                parameters={'text': text[:100]},
                error=error_msg
            )

            return {
                'status': 'error',
                'error': error_msg,
                'message': 'Failed to create approval request'
            }

    async def twitter_post_thread(
        self,
        tweets: List[str],
        image_paths: Optional[List[str]] = None,
        scheduled_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a tweet thread (creates approval request).

        Args:
            tweets: List of tweet texts (2-25 tweets, max 260 chars each for numbering)
            image_paths: Optional list of image file paths (max 4 total)
            scheduled_time: Optional ISO 8601 timestamp for scheduling

        Returns:
            Dict with status, approval_id, approval_file, total_tweets, message
        """
        try:
            # Validate thread length
            if len(tweets) < 2:
                return {
                    'status': 'error',
                    'error': 'Thread must have at least 2 tweets',
                    'message': 'Thread too short'
                }

            if len(tweets) > 25:
                return {
                    'status': 'error',
                    'error': 'Thread cannot exceed 25 tweets',
                    'message': 'Thread too long'
                }

            # Validate each tweet length (leave room for numbering)
            for i, tweet in enumerate(tweets):
                # Numbering adds " (n/total)" which is about 8-10 characters
                if len(tweet) > 260:
                    return {
                        'status': 'error',
                        'error': f'Tweet {i+1} exceeds 260 characters (need room for numbering): {len(tweet)} characters',
                        'message': f'Tweet {i+1} too long'
                    }

            # Validate images if provided
            if image_paths:
                if len(image_paths) > 4:
                    return {
                        'status': 'error',
                        'error': 'Maximum 4 images allowed per thread',
                        'message': 'Too many images'
                    }

                for image_path in image_paths:
                    validation = self.image_validator.validate_image(
                        image_path,
                        max_size_mb=5,
                        allowed_formats=['PNG', 'JPEG', 'GIF']
                    )
                    if not validation['valid']:
                        return {
                            'status': 'error',
                            'error': validation['error'],
                            'message': f'Image validation failed: {Path(image_path).name}'
                        }

            # Create approval request
            approval_id = self._create_approval_id('POST_THREAD')

            metadata = {
                'tweets': tweets,
                'image_paths': image_paths or [],
                'scheduled_time': scheduled_time
            }

            reasoning = f"Posting thread with {len(tweets)} tweets"

            approval_file = self._create_approval_request(
                approval_id=approval_id,
                action_type='twitter_post_thread',
                metadata=metadata,
                reasoning=reasoning
            )

            # Log approval request creation
            self.audit_logger.log_action(
                action_type='twitter_post_thread_request',
                actor='ai_employee',
                target='twitter',
                parameters={'tweet_count': len(tweets), 'images': len(image_paths) if image_paths else 0},
                result={'approval_id': approval_id, 'approval_file': approval_file},
                approval=approval_id
            )

            return {
                'status': 'approval_created',
                'approval_id': approval_id,
                'approval_file': approval_file,
                'total_tweets': len(tweets),
                'message': f'Thread approval request created: {approval_id}'
            }

        except Exception as e:
            error_msg = str(e)
            self.audit_logger.log_action(
                action_type='twitter_post_thread_request',
                actor='ai_employee',
                target='twitter',
                parameters={'tweet_count': len(tweets) if tweets else 0},
                error=error_msg
            )

            return {
                'status': 'error',
                'error': error_msg,
                'message': 'Failed to create thread approval request'
            }

    async def twitter_get_mentions(
        self,
        since: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve tweets mentioning the authenticated user.

        Args:
            since: ISO 8601 timestamp to retrieve mentions since (max 7 days ago)
            max_results: Maximum number of mentions to retrieve (5-100)

        Returns:
            Dict with status, mentions, count, cached, message
        """
        try:
            # Check rate limit
            self.rate_limiter.check_limit('mentions')

            # Get mentions
            mentions = self.client.get_mentions(since=since, max_results=max_results)

            # Log retrieval
            self.audit_logger.log_action(
                action_type='twitter_get_mentions',
                actor='ai_employee',
                target='twitter',
                parameters={'since': since, 'max_results': max_results},
                result={'count': len(mentions)}
            )

            return {
                'status': 'success',
                'mentions': mentions,
                'count': len(mentions),
                'cached': False,  # TODO: Implement cache detection
                'message': f'Retrieved {len(mentions)} mentions'
            }

        except RateLimitException as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Rate limit reached'
            }
        except Exception as e:
            error_msg = str(e)
            self.audit_logger.log_action(
                action_type='twitter_get_mentions',
                actor='ai_employee',
                target='twitter',
                parameters={'since': since, 'max_results': max_results},
                error=error_msg
            )

            return {
                'status': 'error',
                'error': error_msg,
                'message': 'Failed to retrieve mentions'
            }

    async def twitter_get_metrics(self, tweet_id: str) -> Dict[str, Any]:
        """
        Retrieve engagement metrics for a tweet.

        Args:
            tweet_id: Twitter tweet ID

        Returns:
            Dict with status, metrics, cached, message
        """
        try:
            # Check rate limit
            self.rate_limiter.check_limit('metrics')

            # Get metrics
            metrics = self.client.get_tweet_metrics(tweet_id)

            # Log retrieval
            self.audit_logger.log_action(
                action_type='twitter_get_metrics',
                actor='ai_employee',
                target=f'tweet_{tweet_id}',
                parameters={'tweet_id': tweet_id},
                result=metrics
            )

            return {
                'status': 'success',
                'metrics': metrics,
                'cached': False,  # TODO: Implement cache detection
                'message': f'Retrieved metrics for tweet {tweet_id}'
            }

        except RateLimitException as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Rate limit reached'
            }
        except Exception as e:
            error_msg = str(e)
            self.audit_logger.log_action(
                action_type='twitter_get_metrics',
                actor='ai_employee',
                target=f'tweet_{tweet_id}',
                parameters={'tweet_id': tweet_id},
                error=error_msg
            )

            return {
                'status': 'error',
                'error': error_msg,
                'message': 'Failed to retrieve metrics'
            }


def execute_twitter_post_tweet(approval_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute approved tweet posting action.

    Called by approval_executor.py after human approval.

    Args:
        approval_id: Unique approval identifier
        metadata: Tweet metadata (text, image_paths, scheduled_time)

    Returns:
        Dict with success, tweet_id, url, error
    """
    try:
        from mcp_servers.twitter_client import TwitterClient
        from scripts.audit_logger import AuditLogger

        client = TwitterClient()
        audit_logger = AuditLogger()

        # Extract parameters
        text = metadata.get('text')
        image_paths = metadata.get('image_paths', [])
        scheduled_time = metadata.get('scheduled_time')

        if not text:
            return {
                'success': False,
                'error': 'Tweet text is required'
            }

        # Upload images if provided
        media_ids = []
        if image_paths:
            for image_path in image_paths:
                media_id = client.upload_media(image_path)
                media_ids.append(media_id)

        # Post tweet
        result = client.post_tweet(
            text=text,
            media_ids=media_ids if media_ids else None
        )

        tweet_id = result.get('tweet_id')

        # Log execution
        audit_logger.log_action(
            action_type='twitter_post_tweet_executed',
            actor='approval_executor',
            target=f'tweet_{tweet_id}',
            parameters={'text_length': len(text), 'images': len(media_ids)},
            result={'tweet_id': tweet_id},
            approval=approval_id
        )

        return {
            'success': True,
            'tweet_id': tweet_id,
            'url': f'https://twitter.com/i/web/status/{tweet_id}',
            'message': f'Tweet posted successfully: {tweet_id}'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def execute_twitter_post_thread(approval_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute approved thread posting action.

    Called by approval_executor.py after human approval.

    Args:
        approval_id: Unique approval identifier
        metadata: Thread metadata (tweets, image_paths, scheduled_time)

    Returns:
        Dict with success, tweet_ids, urls, error
    """
    try:
        from mcp_servers.twitter_client import TwitterClient
        from scripts.audit_logger import AuditLogger

        client = TwitterClient()
        audit_logger = AuditLogger()

        # Extract parameters
        tweets = metadata.get('tweets', [])
        image_paths = metadata.get('image_paths', [])
        scheduled_time = metadata.get('scheduled_time')

        if not tweets or len(tweets) < 2:
            return {
                'success': False,
                'error': 'Thread must have at least 2 tweets'
            }

        # Upload images if provided
        media_ids = []
        if image_paths:
            for image_path in image_paths:
                media_id = client.upload_media(image_path)
                media_ids.append(media_id)

        # Create thread
        result = client.create_thread(
            tweets=tweets,
            media_ids=media_ids if media_ids else None
        )

        tweet_ids = result.get('tweet_ids', [])

        # Log execution
        audit_logger.log_action(
            action_type='twitter_post_thread_executed',
            actor='approval_executor',
            target=f'thread_{tweet_ids[0] if tweet_ids else "unknown"}',
            parameters={'tweet_count': len(tweets), 'images': len(media_ids)},
            result={'tweet_ids': tweet_ids},
            approval=approval_id
        )

        return {
            'success': True,
            'tweet_ids': tweet_ids,
            'urls': [f'https://twitter.com/i/web/status/{tid}' for tid in tweet_ids],
            'message': f'Thread posted successfully: {len(tweet_ids)} tweets'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# MCP server entry point
if __name__ == "__main__":
    server = TwitterMCPServer()
    print("Twitter MCP Server initialized")
    print("Available tools:")
    print("  - twitter_post_tweet")
    print("  - twitter_post_thread")
    print("  - twitter_get_mentions")
    print("  - twitter_get_metrics")
