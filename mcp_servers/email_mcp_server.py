"""Email MCP Server for Gmail integration.

This MCP server exposes email operations (send, draft, search) to Claude Code
using the existing Gmail OAuth credentials.
"""

import os
import sys
import base64
import json
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from mcp.server import Server
from mcp.types import Tool, TextContent

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.audit_logger import AuditLogger


# Initialize MCP server
app = Server("email-mcp-server")

# Gmail service (initialized on first use)
_gmail_service = None

# Audit logger (initialized on first use)
_audit_logger = None


def get_audit_logger():
    """Get or create AuditLogger instance."""
    global _audit_logger

    if _audit_logger is not None:
        return _audit_logger

    _audit_logger = AuditLogger()
    return _audit_logger


def get_gmail_service():
    """Get or create Gmail API service."""
    global _gmail_service

    if _gmail_service is not None:
        return _gmail_service

    # Load credentials from token.json
    token_path = Path(__file__).parent.parent / "token.json"

    if not token_path.exists():
        raise FileNotFoundError(
            f"Gmail token not found at {token_path}. "
            "Run the Gmail watcher first to authenticate."
        )

    creds = Credentials.from_authorized_user_file(str(token_path))
    _gmail_service = build('gmail', 'v1', credentials=creds)

    return _gmail_service


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available email tools."""
    return [
        Tool(
            name="send_email",
            description="Send an email via Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body (plain text or HTML)"
                    },
                    "cc": {
                        "type": "string",
                        "description": "CC recipients (comma-separated)",
                        "optional": True
                    },
                    "bcc": {
                        "type": "string",
                        "description": "BCC recipients (comma-separated)",
                        "optional": True
                    }
                },
                "required": ["to", "subject", "body"]
            }
        ),
        Tool(
            name="draft_email",
            description="Create a draft email in Gmail (does not send)",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body (plain text or HTML)"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        ),
        Tool(
            name="search_emails",
            description="Search Gmail messages using Gmail query syntax",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Gmail search query (e.g., 'from:user@example.com is:unread')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "optional": True
                    }
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    try:
        if name == "send_email":
            return await send_email(
                to=arguments["to"],
                subject=arguments["subject"],
                body=arguments["body"],
                cc=arguments.get("cc"),
                bcc=arguments.get("bcc")
            )

        elif name == "draft_email":
            return await draft_email(
                to=arguments["to"],
                subject=arguments["subject"],
                body=arguments["body"]
            )

        elif name == "search_emails":
            return await search_emails(
                query=arguments["query"],
                max_results=arguments.get("max_results", 10)
            )

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None
) -> list[TextContent]:
    """Send an email via Gmail API."""

    audit_logger = get_audit_logger()

    try:
        service = get_gmail_service()

        # Create message
        message = MIMEMultipart()
        message['To'] = to
        message['Subject'] = subject

        if cc:
            message['Cc'] = cc
        if bcc:
            message['Bcc'] = bcc

        # Attach body
        message.attach(MIMEText(body, 'plain'))

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        # Send via Gmail API
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        # Log successful email send
        audit_logger.log_action(
            action_type="email_send",
            actor="email_mcp",
            target=to,
            parameters={
                "subject": subject,
                "body_preview": body[:100] if len(body) > 100 else body,
                "cc": cc,
                "bcc": bcc,
                "message_id": result['id']
            },
            result="success",
            metadata={
                "gmail_message_id": result['id']
            }
        )
        audit_logger.flush()

        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "message_id": result['id'],
                "to": to,
                "subject": subject
            }, indent=2)
        )]

    except HttpError as e:
        # Log failed email send
        audit_logger.log_action(
            action_type="email_send",
            actor="email_mcp",
            target=to,
            parameters={
                "subject": subject,
                "body_preview": body[:100] if len(body) > 100 else body,
                "cc": cc,
                "bcc": bcc
            },
            result="failure",
            error=f"Gmail API error: {str(e)}"
        )
        audit_logger.flush()

        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "error": str(e),
                "details": "Gmail API error - check credentials and permissions"
            }, indent=2)
        )]


async def draft_email(
    to: str,
    subject: str,
    body: str
) -> list[TextContent]:
    """Create a draft email in Gmail."""

    audit_logger = get_audit_logger()

    try:
        service = get_gmail_service()

        # Create message
        message = MIMEText(body)
        message['To'] = to
        message['Subject'] = subject

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        # Create draft via Gmail API
        result = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw_message}}
        ).execute()

        # Log successful draft creation
        audit_logger.log_action(
            action_type="email_draft",
            actor="email_mcp",
            target=to,
            parameters={
                "subject": subject,
                "body_preview": body[:100] if len(body) > 100 else body,
                "draft_id": result['id']
            },
            result="success",
            metadata={
                "gmail_draft_id": result['id']
            }
        )
        audit_logger.flush()

        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "draft_id": result['id'],
                "to": to,
                "subject": subject,
                "message": "Draft created successfully"
            }, indent=2)
        )]

    except HttpError as e:
        # Log failed draft creation
        audit_logger.log_action(
            action_type="email_draft",
            actor="email_mcp",
            target=to,
            parameters={
                "subject": subject,
                "body_preview": body[:100] if len(body) > 100 else body
            },
            result="failure",
            error=f"Gmail API error: {str(e)}"
        )
        audit_logger.flush()

        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "error": str(e)
            }, indent=2)
        )]


async def search_emails(
    query: str,
    max_results: int = 10
) -> list[TextContent]:
    """Search Gmail messages."""

    audit_logger = get_audit_logger()

    try:
        service = get_gmail_service()

        # Search messages
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])

        if not messages:
            # Log successful search with no results
            audit_logger.log_action(
                action_type="email_search",
                actor="email_mcp",
                target="gmail",
                parameters={
                    "query": query,
                    "max_results": max_results,
                    "results_count": 0
                },
                result="success"
            )
            audit_logger.flush()

            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "count": 0,
                    "messages": []
                }, indent=2)
            )]

        # Get message details
        message_details = []
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()

            headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}

            message_details.append({
                "id": msg['id'],
                "from": headers.get('From', 'Unknown'),
                "subject": headers.get('Subject', 'No Subject'),
                "date": headers.get('Date', 'Unknown')
            })

        # Log successful search with results
        audit_logger.log_action(
            action_type="email_search",
            actor="email_mcp",
            target="gmail",
            parameters={
                "query": query,
                "max_results": max_results,
                "results_count": len(message_details)
            },
            result="success",
            metadata={
                "message_ids": [msg['id'] for msg in message_details]
            }
        )
        audit_logger.flush()

        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "count": len(message_details),
                "messages": message_details
            }, indent=2)
        )]

    except HttpError as e:
        # Log failed search
        audit_logger.log_action(
            action_type="email_search",
            actor="email_mcp",
            target="gmail",
            parameters={
                "query": query,
                "max_results": max_results
            },
            result="failure",
            error=f"Gmail API error: {str(e)}"
        )
        audit_logger.flush()

        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "error": str(e)
            }, indent=2)
        )]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
