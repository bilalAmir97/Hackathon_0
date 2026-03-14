"""Mock Gmail API fixtures for testing.

This module provides mock objects and fixtures for testing Gmail API integration
without making actual API calls.
"""

from typing import Dict, List, Any
from unittest.mock import Mock, MagicMock


class MockGmailService:
    """Mock Gmail API service for testing."""

    def __init__(self, messages: List[Dict[str, Any]] = None):
        """Initialize mock service with optional message list.

        Args:
            messages: List of mock message dictionaries
        """
        self.messages = messages or []
        self._call_count = 0

    def users(self):
        """Return mock users resource."""
        return MockUsersResource(self.messages)


class MockUsersResource:
    """Mock users resource."""

    def __init__(self, messages: List[Dict[str, Any]]):
        self.messages = messages

    def messages(self):
        """Return mock messages resource."""
        return MockMessagesResource(self.messages)


class MockMessagesResource:
    """Mock messages resource."""

    def __init__(self, messages: List[Dict[str, Any]]):
        self.messages = messages

    def list(self, userId: str, q: str = None, maxResults: int = 20):
        """Mock messages.list() method.

        Args:
            userId: User ID (typically 'me')
            q: Query string (e.g., 'is:unread')
            maxResults: Maximum results to return

        Returns:
            Mock request object
        """
        return MockRequest(self.messages[:maxResults])

    def get(self, userId: str, id: str, format: str = 'full'):
        """Mock messages.get() method.

        Args:
            userId: User ID (typically 'me')
            id: Message ID
            format: Response format ('full', 'metadata', 'minimal')

        Returns:
            Mock request object with single message
        """
        message = next((m for m in self.messages if m.get('id') == id), None)
        return MockRequest(message)


class MockRequest:
    """Mock API request object."""

    def __init__(self, result: Any):
        self.result = result

    def execute(self):
        """Execute mock request and return result."""
        if isinstance(self.result, list):
            return {'messages': [{'id': msg['id'], 'threadId': msg.get('threadId', msg['id'])}
                                 for msg in self.result]}
        return self.result


def create_mock_email(
    email_id: str,
    from_addr: str,
    subject: str,
    snippet: str,
    labels: List[str] = None,
    is_unread: bool = True
) -> Dict[str, Any]:
    """Create a mock email message.

    Args:
        email_id: Unique message ID
        from_addr: Sender email address
        subject: Email subject
        snippet: Email preview text
        labels: Gmail labels (default: ['UNREAD', 'INBOX'])
        is_unread: Whether email is unread

    Returns:
        Mock email message dictionary
    """
    if labels is None:
        labels = ['UNREAD', 'INBOX'] if is_unread else ['INBOX']

    return {
        'id': email_id,
        'threadId': f'thread_{email_id}',
        'labelIds': labels,
        'snippet': snippet,
        'payload': {
            'headers': [
                {'name': 'From', 'value': from_addr},
                {'name': 'Subject', 'value': subject},
                {'name': 'Date', 'value': 'Mon, 25 Feb 2026 14:30:00 +0000'}
            ],
            'body': {
                'data': snippet  # Base64 encoded in real API
            }
        },
        'internalDate': '1740489000000'
    }


def create_mock_credentials(expired: bool = False, refresh_token: str = 'mock_refresh_token'):
    """Create mock OAuth credentials.

    Args:
        expired: Whether credentials are expired
        refresh_token: Mock refresh token

    Returns:
        Mock credentials object
    """
    creds = Mock()
    creds.expired = expired
    creds.refresh_token = refresh_token
    creds.valid = not expired
    creds.token = 'mock_access_token'
    creds.refresh = Mock()
    creds.to_json = Mock(return_value='{"token": "mock_access_token"}')
    return creds
