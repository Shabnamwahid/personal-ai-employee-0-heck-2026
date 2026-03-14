#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email MCP Server - Send emails via Gmail API.

This MCP server provides email capabilities to the AI Employee:
- Send emails
- Draft emails
- Search emails
- Mark emails as read

For Silver Tier, this is a simplified implementation.
Gold Tier would include full MCP protocol support.

Usage:
    python email_mcp_server.py --send-to recipient@example.com --subject "Test" --body "Hello"

Credentials:
    Requires credentials.json in the same directory
    First run will require OAuth authorization
"""

import os
import sys
import json
import base64
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Google API imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Gmail API Scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

CREDENTIALS_FILE = Path('credentials.json')
TOKEN_FILE = Path('token_email.json')


class EmailMCPServer:
    """
    Email MCP Server - Provides email capabilities via Gmail API.

    Methods:
    - send_email(to, subject, body, cc=None, bcc=None)
    - draft_email(to, subject, body)
    - search_emails(query, max_results=10)
    - mark_read(message_id)
    - mark_unread(message_id)
    """

    def __init__(self, credentials_path: Path = None):
        """
        Initialize the Email MCP Server.

        Args:
            credentials_path: Path to credentials.json (default: ./credentials.json)
        """
        self.credentials_path = credentials_path or CREDENTIALS_FILE
        self.service = None
        self._connect()

    def _connect(self):
        """Establish connection to Gmail API."""
        try:
            creds = None

            # Load existing token
            if TOKEN_FILE.exists():
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                print(f"Loaded existing OAuth token")

            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    print("Refreshing expired token")
                    creds.refresh(Request())
                else:
                    if not self.credentials_path.exists():
                        raise FileNotFoundError(
                            f"Credentials file not found: {self.credentials_path}\n"
                            "Please download credentials.json from Google Cloud Console"
                        )

                    print("Starting OAuth flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0, open_browser=False)
                    print("OAuth flow complete")

                # Save token
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                print("Token saved")

            # Build service
            self.service = build('gmail', 'v1', credentials=creds)

            # Test connection
            profile = self.service.users().getProfile(userId='me').execute()
            print(f"Connected to Gmail: {profile['emailAddress']}")

        except Exception as e:
            print(f"Failed to connect to Gmail: {e}")
            raise

    def send_email(self, to: str, subject: str, body: str,
                   cc: str = None, bcc: str = None,
                   html: bool = False) -> Dict[str, Any]:
        """
        Send an email via Gmail.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            html: Whether body is HTML

        Returns:
            Dict with message_id and status
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["to"] = to
            message["subject"] = subject

            if cc:
                message["cc"] = cc
            if bcc:
                message["bcc"] = bcc

            # Add body
            if html:
                message.attach(MIMEText(body, "html"))
            else:
                message.attach(MIMEText(body, "plain"))

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            result = {
                'status': 'success',
                'message_id': sent_message['id'],
                'thread_id': sent_message['threadId'],
                'timestamp': datetime.now().isoformat()
            }

            print(f"Email sent successfully! Message ID: {sent_message['id']}")
            return result

        except HttpError as error:
            print(f"Gmail API error: {error}")
            return {
                'status': 'error',
                'error': str(error)
            }
        except Exception as e:
            print(f"Failed to send email: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def draft_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Create a draft email (don't send).

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text

        Returns:
            Dict with draft_id and status
        """
        try:
            # Create message
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Create draft
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw_message}}
            ).execute()

            result = {
                'status': 'success',
                'draft_id': draft['id'],
                'message_id': draft['message']['id'],
                'timestamp': datetime.now().isoformat()
            }

            print(f"Draft created successfully! Draft ID: {draft['id']}")
            return result

        except Exception as e:
            print(f"Failed to create draft: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def search_emails(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search emails.

        Args:
            query: Gmail search query
            max_results: Maximum results to return

        Returns:
            List of email dicts
        """
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            emails = []

            for msg in messages:
                detail = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'To', 'Subject', 'Date']
                ).execute()

                headers = {h['name']: h['value'] for h in detail['payload']['headers']}
                emails.append({
                    'id': msg['id'],
                    'thread_id': msg['threadId'],
                    'from': headers.get('From', ''),
                    'to': headers.get('To', ''),
                    'subject': headers.get('Subject', ''),
                    'date': headers.get('Date', '')
                })

            return emails

        except Exception as e:
            print(f"Search failed: {e}")
            return []

    def mark_read(self, message_id: str) -> bool:
        """Mark an email as read."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            print(f"Marked message {message_id} as read")
            return True
        except Exception as e:
            print(f"Failed to mark as read: {e}")
            return False

    def mark_unread(self, message_id: str) -> bool:
        """Mark an email as unread."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()
            print(f"Marked message {message_id} as unread")
            return True
        except Exception as e:
            print(f"Failed to mark as unread: {e}")
            return False


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(description='Email MCP Server - Gmail Integration')
    parser.add_argument('--send-to', type=str, help='Recipient email address')
    parser.add_argument('--subject', type=str, help='Email subject')
    parser.add_argument('--body', type=str, help='Email body')
    parser.add_argument('--cc', type=str, help='CC recipients')
    parser.add_argument('--html', action='store_true', help='Body is HTML')
    parser.add_argument('--draft', action='store_true', help='Create draft instead of sending')
    parser.add_argument('--search', type=str, help='Search emails with query')
    parser.add_argument('--mark-read', type=str, help='Mark message as read')

    args = parser.parse_args()

    # Initialize server
    try:
        server = EmailMCPServer()
    except Exception as e:
        print(f"Failed to initialize: {e}")
        sys.exit(1)

    # Send email
    if args.send_to and args.subject and args.body:
        if args.draft:
            result = server.draft_email(args.send_to, args.subject, args.body)
        else:
            result = server.send_email(
                args.send_to, args.subject, args.body,
                cc=args.cc, html=args.html
            )
        print(json.dumps(result, indent=2))

    # Search emails
    elif args.search:
        emails = server.search_emails(args.search)
        print(json.dumps(emails, indent=2))

    # Mark as read
    elif args.mark_read:
        success = server.mark_read(args.mark_read)
        print(json.dumps({'success': success}))

    else:
        parser.print_help()
        print("\nExamples:")
        print("  python email_mcp_server.py --send-to user@example.com --subject 'Hello' --body 'Test message'")
        print("  python email_mcp_server.py --draft --send-to user@example.com --subject 'Hello' --body 'Draft'")
        print("  python email_mcp_server.py --search 'is:unread'")
        print("  python email_mcp_server.py --mark-read MESSAGE_ID")


if __name__ == "__main__":
    main()
