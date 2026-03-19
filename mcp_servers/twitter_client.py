"""
Twitter API v2 Client

Provides a wrapper around Tweepy for Twitter API v2 integration with:
- Dual client pattern (API v2 + v1.1 for media)
- OAuth 1.0a authentication
- Error handling and retry logic
- Circuit breaker for sustained failures
- Rate limiting integration
"""

import os
import tweepy
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
import time

# Import error recovery decorators
import sys
sys.path.append(str(Path(__file__).parent.parent))
from scripts.error_recovery.decorators import with_retry, with_circuit_breaker


class TwitterClient:
    """
    Twitter API v2 client with dual client pattern.

    Uses tweepy.Client for API v2 operations and tweepy.API for v1.1 media uploads.
    Includes authentication, error handling, and rate limiting.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None
    ):
        """
        Initialize Twitter client with OAuth 1.0a credentials.

        Args:
            api_key: Twitter API key (consumer key)
            api_secret: Twitter API secret (consumer secret)
            access_token: Twitter access token
            access_token_secret: Twitter access token secret
        """
        # Load credentials from environment if not provided
        self.api_key = api_key or os.getenv('TWITTER_API_KEY')
        self.api_secret = api_secret or os.getenv('TWITTER_API_SECRET')
        self.access_token = access_token or os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = access_token_secret or os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

        # Validate credentials
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            raise ValueError(
                "Missing Twitter credentials. Ensure TWITTER_API_KEY, TWITTER_API_SECRET, "
                "TWITTER_ACCESS_TOKEN, and TWITTER_ACCESS_TOKEN_SECRET are set."
            )

        # Initialize clients
        self.client_v2: Optional[tweepy.Client] = None
        self.api_v1: Optional[tweepy.API] = None

        # Cache for metrics and mentions (5-minute TTL)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = int(os.getenv('TWITTER_METRICS_CACHE_TTL', '300'))  # 5 minutes

        # Authenticate
        self._authenticate()

    def _authenticate(self):
        """
        Authenticate with Twitter API using OAuth 1.0a.
        Creates both API v2 client and v1.1 API for media uploads.
        """
        try:
            # Create API v2 client
            self.client_v2 = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True  # Automatic rate limit handling
            )

            # Create API v1.1 client for media uploads
            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret
            )
            self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)

            # Verify credentials
            self.client_v2.get_me()

        except tweepy.TweepyException as e:
            raise Exception(f"Twitter authentication failed: {e}")

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(failure_threshold=5, cooldown_seconds=60)
    def post_tweet(
        self,
        text: str,
        media_ids: Optional[List[str]] = None,
        in_reply_to_tweet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a tweet to Twitter.

        Args:
            text: Tweet text (max 280 characters)
            media_ids: List of media IDs to attach (max 4)
            in_reply_to_tweet_id: Tweet ID to reply to (for threads)

        Returns:
            Dict with tweet_id and created_at

        Raises:
            Exception: If tweet posting fails
        """
        try:
            # Validate text length
            if len(text) > 280:
                raise ValueError(f"Tweet text exceeds 280 characters: {len(text)}")

            # Post tweet
            response = self.client_v2.create_tweet(
                text=text,
                media_ids=media_ids if media_ids else None,
                in_reply_to_tweet_id=in_reply_to_tweet_id
            )

            return {
                "tweet_id": response.data['id'],
                "created_at": datetime.utcnow().isoformat()
            }

        except tweepy.TweepyException as e:
            raise Exception(f"Failed to post tweet: {e}")

    @with_retry(max_attempts=3, base_delay=1.0)
    def upload_media(self, image_path: str) -> str:
        """
        Upload media to Twitter via API v1.1.

        Args:
            image_path: Path to image file

        Returns:
            Media ID string

        Raises:
            Exception: If media upload fails
        """
        try:
            # Validate file exists
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")

            # Upload via API v1.1
            media = self.api_v1.media_upload(filename=image_path)

            return str(media.media_id)

        except tweepy.TweepyException as e:
            raise Exception(f"Failed to upload media: {e}")

    @with_retry(max_attempts=3, base_delay=1.0)
    @with_circuit_breaker(failure_threshold=5, cooldown_seconds=60)
    def create_thread(
        self,
        tweets: List[str],
        media_ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Create a tweet thread with automatic numbering and linking.

        Args:
            tweets: List of tweet texts (2-25 tweets)
            media_ids: Optional list of media IDs to attach to first tweet

        Returns:
            List of tweet IDs in thread order

        Raises:
            Exception: If thread creation fails (triggers rollback)
        """
        if len(tweets) < 2:
            raise ValueError("Thread must have at least 2 tweets")
        if len(tweets) > 25:
            raise ValueError("Thread cannot exceed 25 tweets")

        posted_ids = []
        total = len(tweets)

        try:
            for i, text in enumerate(tweets):
                # Add automatic numbering
                numbered_text = f"{text} ({i+1}/{total})"

                # Validate length (leave room for numbering)
                if len(numbered_text) > 280:
                    raise ValueError(f"Tweet {i+1} exceeds 280 characters with numbering: {len(numbered_text)}")

                # Post tweet
                if i == 0:
                    # First tweet (with optional media)
                    response = self.post_tweet(
                        text=numbered_text,
                        media_ids=media_ids
                    )
                else:
                    # Reply to previous tweet
                    response = self.post_tweet(
                        text=numbered_text,
                        in_reply_to_tweet_id=posted_ids[-1]
                    )

                posted_ids.append(response['tweet_id'])

            return posted_ids

        except Exception as e:
            # Rollback: delete all posted tweets
            for tweet_id in posted_ids:
                try:
                    self.client_v2.delete_tweet(tweet_id)
                except:
                    pass  # Log but don't fail rollback

            raise Exception(f"Thread creation failed, rolled back {len(posted_ids)} tweets: {e}")

    @with_retry(max_attempts=3, base_delay=1.0)
    def get_mentions(
        self,
        since: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve mentions of the authenticated user.

        Args:
            since: ISO 8601 timestamp to retrieve mentions since (max 7 days ago)
            max_results: Maximum number of mentions to retrieve (5-100)

        Returns:
            List of mention dictionaries with tweet_id, author_id, text, created_at
        """
        # Check cache
        cache_key = f"mentions_{since}_{max_results}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.fromisoformat(cached['cached_at']) + timedelta(seconds=self._cache_ttl) > datetime.utcnow():
                return cached['data']

        try:
            # Get authenticated user ID
            me = self.client_v2.get_me()
            user_id = me.data.id

            # Get mentions
            mentions = self.client_v2.get_users_mentions(
                id=user_id,
                start_time=since,
                max_results=min(max_results, 100),
                tweet_fields=['created_at', 'author_id', 'conversation_id'],
                expansions=['author_id'],
                user_fields=['username']
            )

            # Format results
            results = []
            if mentions.data:
                # Create user lookup
                users = {user.id: user.username for user in mentions.includes.get('users', [])}

                for mention in mentions.data:
                    results.append({
                        'mention_id': mention.id,
                        'tweet_id': mention.id,
                        'author_id': mention.author_id,
                        'author_username': users.get(mention.author_id, 'unknown'),
                        'text': mention.text,
                        'created_at': mention.created_at.isoformat(),
                        'conversation_id': getattr(mention, 'conversation_id', None)
                    })

            # Cache results
            self._cache[cache_key] = {
                'data': results,
                'cached_at': datetime.utcnow().isoformat()
            }

            return results

        except tweepy.TweepyException as e:
            raise Exception(f"Failed to retrieve mentions: {e}")

    @with_retry(max_attempts=3, base_delay=1.0)
    def get_tweet_metrics(self, tweet_id: str) -> Dict[str, Any]:
        """
        Retrieve engagement metrics for a specific tweet.

        Args:
            tweet_id: Twitter tweet ID

        Returns:
            Dict with likes, retweets, replies, impressions, engagement_rate, cached_at
        """
        # Check cache
        cache_key = f"metrics_{tweet_id}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.fromisoformat(cached['cached_at']) + timedelta(seconds=self._cache_ttl) > datetime.utcnow():
                return cached['data']

        try:
            # Get tweet with metrics
            tweet = self.client_v2.get_tweet(
                id=tweet_id,
                tweet_fields=['public_metrics'],
            )

            if not tweet.data:
                raise Exception(f"Tweet not found: {tweet_id}")

            metrics = tweet.data.public_metrics

            # Calculate engagement rate
            impressions = metrics.get('impression_count', 0)
            engagement = metrics.get('like_count', 0) + metrics.get('retweet_count', 0) + metrics.get('reply_count', 0)
            engagement_rate = engagement / impressions if impressions > 0 else 0.0

            result = {
                'likes': metrics.get('like_count', 0),
                'retweets': metrics.get('retweet_count', 0),
                'replies': metrics.get('reply_count', 0),
                'impressions': impressions,
                'engagement_rate': round(engagement_rate, 4),
                'cached_at': datetime.utcnow().isoformat()
            }

            # Cache results
            self._cache[cache_key] = {
                'data': result,
                'cached_at': datetime.utcnow().isoformat()
            }

            return result

        except tweepy.TweepyException as e:
            raise Exception(f"Failed to retrieve tweet metrics: {e}")

    @with_retry(max_attempts=3, base_delay=1.0)
    def get_account_metrics(self) -> Dict[str, Any]:
        """
        Retrieve account-level metrics for the authenticated user.

        Returns:
            Dict with followers_count, tweet_count
        """
        try:
            # Get authenticated user with metrics
            me = self.client_v2.get_me(user_fields=['public_metrics'])

            metrics = me.data.public_metrics

            return {
                'followers_count': metrics.get('followers_count', 0),
                'tweet_count': metrics.get('tweet_count', 0)
            }

        except tweepy.TweepyException as e:
            raise Exception(f"Failed to retrieve account metrics: {e}")
