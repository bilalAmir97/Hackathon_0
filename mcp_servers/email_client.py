"""MCP Client for Email operations.

This module provides a simple client interface for calling the Email MCP server
from the approval executor.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
import base64


class EmailMCPClient:
    """Client for Email MCP operations."""

    def __init__(self, token_path: str = "token.json"):
        """Initialize Email MCP client.

        Args:
            token_path: Path to Gmail OAuth token file
        """
        self.token_path = Path(token_path)
        self._service = None

    def _get_service(self):
        """Get or create Gmail API service."""
        if self._service is not None:
            return self._service

        if not self.token_path.exists():
            raise FileNotFoundError(
                f"Gmail token not found at {self.token_path}. "
                "Run reauth_gmail_mcp.py to authenticate."
            )

        creds = Credentials.from_authorized_user_file(str(self.token_path))
        self._service = build('gmail', 'v1', credentials=creds)
        return self._service

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an email via Gmail API.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)

        Returns:
            Dict with status and message_id or error
        """
        try:
            service = self._get_service()

            # Create message
            message = MIMEText(body)
            message['To'] = to
            message['Subject'] = subject

            if cc:
                message['Cc'] = cc
            if bcc:
                message['Bcc'] = bcc

            # Encode and send
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            return {
                "status": "success",
                "message_id": result['id'],
                "to": to,
                "subject": subject
            }

        except HttpError as e:
            return {
                "status": "error",
                "error": str(e),
                "details": "Gmail API error - check credentials and permissions"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def draft_email(
        self,
        to: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """Create a draft email in Gmail.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)

        Returns:
            Dict with status and draft_id or error
        """
        try:
            service = self._get_service()

            # Create message
            message = MIMEText(body)
            message['To'] = to
            message['Subject'] = subject

            # Encode
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Create draft
            result = service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw_message}}
            ).execute()

            return {
                "status": "success",
                "draft_id": result['id'],
                "to": to,
                "subject": subject,
                "message": "Draft created successfully"
            }

        except HttpError as e:
            return {
                "status": "error",
                "error": str(e)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# Singleton instance
_email_client = None


def get_email_client(token_path: str = "token.json") -> EmailMCPClient:
    """Get or create the global email client instance.

    Args:
        token_path: Path to Gmail OAuth token file

    Returns:
        EmailMCPClient instance
    """
    global _email_client
    if _email_client is None:
        _email_client = EmailMCPClient(token_path)
    return _email_client
