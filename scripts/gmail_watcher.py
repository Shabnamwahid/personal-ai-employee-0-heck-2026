#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Watcher - Monitor Gmail for new important emails.

This watcher connects to the Gmail API, checks for new unread emails,
and creates action files in the Needs_Action folder for Claude Code to process.

Features:
- Monitors unread emails with importance labels
- Filters by keywords (urgent, invoice, payment, etc.)
- Creates structured action files with email metadata
- Tracks processed emails to avoid duplicates
- Supports auto-approval for known contacts

Usage:
    python gmail_watcher.py AI_Employee_Vault

Credentials Setup:
1. Download credentials.json from Google Cloud Console
2. Place in project root directory
3. First run will open browser for OAuth authorization
4. Token will be saved as token.json
"""

import os
import sys
import json
import base64
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from email import message_from_bytes

# Google API imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import base watcher
from base_watcher import BaseWatcher


# Gmail API Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.labels']

# Keywords that indicate high-priority emails
PRIORITY_KEYWORDS = [
    'urgent', 'asap', 'invoice', 'payment', 'due', 'overdue',
    'important', 'action required', 'immediate', 'deadline',
    'contract', 'agreement', 'legal', 'tax', 'irs',
    'interview', 'meeting', 'call', 'zoom', 'teams'
]

# Known contacts (auto-approve these)
KNOWN_CONTACTS = [
    # Add your frequent contacts here
    # 'client@example.com',
    # 'partner@company.com',
]


class GmailWatcher(BaseWatcher):
    """
    Gmail Watcher - Monitors Gmail API for new emails.

    Creates action files for:
    - Unread emails from important contacts
    - Emails containing priority keywords
    - Emails with attachments
    """

    def __init__(self, vault_path: str, credentials_path: str = None, check_interval: int = 120):
        """
        Initialize the Gmail Watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            credentials_path: Path to credentials.json (default: ./credentials.json)
            check_interval: Seconds between checks (default: 120)
        """
        super().__init__(vault_path, check_interval)

        # Credentials path
        self.credentials_path = Path(credentials_path) if credentials_path else Path('credentials.json')
        self.token_path = Path('token.json')

        # Gmail service
        self.service = None
        self._connect_gmail()

        # Track processed email IDs
        self._load_processed_emails()

        self.logger.info(f"Gmail Watcher initialized")
        self.logger.info(f"Credentials: {self.credentials_path}")
        self.logger.info(f"Checking every {check_interval}s")

    def _connect_gmail(self):
        """Establish connection to Gmail API."""
        try:
            creds = None

            # Load existing token
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
                self.logger.info("Loaded existing OAuth token")

            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    self.logger.info("Refreshing expired token")
                    creds.refresh(Request())
                else:
                    self.logger.info("Starting OAuth flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    # Use fixed port 8080 to avoid redirect_uri_mismatch
                    creds = flow.run_local_server(host='127.0.0.1', port=8080, open_browser=False)
                    self.logger.info("OAuth flow complete")

                # Save token
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
                self.logger.info("Token saved")

            # Build service
            self.service = build('gmail', 'v1', credentials=creds)

            # Test connection
            profile = self.service.users().getProfile(userId='me').execute()
            self.logger.info(f"Connected to Gmail: {profile['emailAddress']}")

        except FileNotFoundError:
            self.logger.error(f"Credentials file not found: {self.credentials_path}")
            self.logger.error("Please download credentials.json from Google Cloud Console")
            raise
        except Exception as e:
            self.logger.error(f"Failed to connect to Gmail: {e}")
            raise

    def _load_processed_emails(self):
        """Load processed email IDs from state."""
        state_file = self.vault_path / '.gmail_processed.json'
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.processed_ids = set(state.get('processed_ids', []))
                self.logger.info(f"Loaded {len(self.processed_ids)} processed email IDs")
            except Exception as e:
                self.logger.warning(f"Failed to load Gmail state: {e}")

    def _save_processed_emails(self):
        """Save processed email IDs to state."""
        state_file = self.vault_path / '.gmail_processed.json'
        try:
            recent_ids = list(self.processed_ids)[-1000:]
            with open(state_file, 'w') as f:
                json.dump({'processed_ids': recent_ids}, f)
        except Exception as e:
            self.logger.error(f"Failed to save Gmail state: {e}")

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check for new unread emails.

        Returns:
            List of email message dicts to process
        """
        if not self.service:
            self.logger.error("Gmail service not connected")
            return []

        try:
            # Search for unread emails
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=20
            ).execute()

            messages = results.get('messages', [])
            self.logger.debug(f"Found {len(messages)} unread messages")

            # Filter out already processed
            new_messages = []
            for msg in messages:
                if msg['id'] not in self.processed_ids:
                    new_messages.append(msg)

            self.logger.info(f"{len(new_messages)} new messages to process")
            return new_messages

        except HttpError as error:
            self.logger.error(f"Gmail API error: {error}")
            return []
        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")
            return []

    def _get_email_details(self, message_id: str) -> Dict[str, Any]:
        """
        Fetch full email details.

        Args:
            message_id: Gmail message ID

        Returns:
            Dict with email metadata and content
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # Extract headers
            headers = message['payload']['headers']
            email_data = {
                'id': message_id,
                'thread_id': message['threadId'],
                'internal_date': datetime.fromtimestamp(
                    int(message['internalDate']) / 1000
                ).isoformat()
            }

            # Parse headers
            for header in headers:
                name = header['name'].lower()
                value = header['value']
                if name == 'from':
                    email_data['from'] = value
                    # Extract email address
                    if '<' in value:
                        email_data['from_email'] = value.split('<')[1].strip('>')
                    else:
                        email_data['from_email'] = value
                elif name == 'to':
                    email_data['to'] = value
                elif name == 'subject':
                    email_data['subject'] = value
                elif name == 'date':
                    email_data['date'] = value

            # Get email body
            email_data['body'] = self._extract_body(message)
            email_data['has_attachments'] = self._has_attachments(message)

            # Check priority
            email_data['is_priority'] = self._is_priority_email(email_data)
            email_data['is_known_contact'] = email_data['from_email'] in KNOWN_CONTACTS

            return email_data

        except Exception as e:
            self.logger.error(f"Failed to get email details: {e}")
            return None

    def _extract_body(self, message: Dict) -> str:
        """Extract plain text body from email."""
        try:
            parts = message['payload']['parts']
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    return decoded[:2000]  # Limit to 2000 chars
            # Fallback to body
            if 'body' in message['payload']:
                data = message['payload']['body'].get('data')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')[:2000]
        except Exception as e:
            self.logger.warning(f"Could not extract email body: {e}")
        return "[Could not extract body]"

    def _has_attachments(self, message: Dict) -> bool:
        """Check if email has attachments."""
        try:
            parts = message['payload'].get('parts', [])
            for part in parts:
                if 'attachmentId' in part.get('body', {}):
                    return True
        except Exception:
            pass
        return False

    def _is_priority_email(self, email_data: Dict) -> bool:
        """Check if email contains priority keywords."""
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()

        for keyword in PRIORITY_KEYWORDS:
            if keyword in subject or keyword in body:
                return True
        return False

    def create_action_file(self, message: Dict) -> Path:
        """
        Create an action file for the email.

        Args:
            message: Gmail message dict with id

        Returns:
            Path to created action file
        """
        # Get full email details
        email_data = self._get_email_details(message['id'])
        if not email_data:
            raise Exception("Failed to fetch email details")

        # Mark as processed
        self.processed_ids.add(message['id'])
        self._save_processed_emails()

        # Determine priority
        priority = 'high' if email_data['is_priority'] else 'normal'
        if email_data['is_known_contact']:
            priority = 'normal'

        # Create action file content
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Suggested actions based on content
        suggested_actions = ['- [ ] Read and respond to email']
        if email_data['has_attachments']:
            suggested_actions.append('- [ ] Review attachments')
        if email_data['is_priority']:
            suggested_actions.append('- [ ] Priority: Handle urgently')
        if 'invoice' in email_data.get('subject', '').lower():
            suggested_actions.append('- [ ] Process invoice/payment')
        if any(x in email_data.get('subject', '').lower() for x in ['meeting', 'call', 'zoom']):
            suggested_actions.append('- [ ] Check calendar/availability')

        content = f"""---
type: email
message_id: {email_data['id']}
thread_id: {email_data['thread_id']}
from: {email_data['from']}
from_email: {email_data['from_email']}
to: {email_data.get('to', 'N/A')}
subject: {email_data['subject']}
received: {email_data['internal_date']}
priority: {priority}
status: unread
has_attachments: {email_data['has_attachments']}
is_known_contact: {email_data['is_known_contact']}
processed: {timestamp}
---

# Email: {email_data['subject']}

## Sender
**From:** {email_data['from']}  
**Email:** `{email_data['from_email']}`  
**Received:** {email_data['internal_date']}

## Email Content

```
{email_data['body']}
```

## Suggested Actions
{chr(10).join(suggested_actions)}

## Notes
- Priority: {priority}
- Known Contact: {email_data['is_known_contact']}
- Has Attachments: {email_data['has_attachments']}

---
*Created by Gmail Watcher - AI Employee v0.2 (Silver Tier)*
"""

        # Create filename
        safe_subject = self.sanitize_filename(email_data['subject'][:50])
        filename = f"EMAIL_{email_data['from_email'].split('@')[0]}_{safe_subject}.md"
        filepath = self.needs_action / filename

        # Write file
        filepath.write_text(content)
        self.logger.info(f"Created action file: {filepath.name}")

        return filepath

    def run(self):
        """Main run loop with reconnection logic."""
        self.logger.info(f"Starting {self.__class__.__name__}")
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Check interval: {self.check_interval}s")

        try:
            while True:
                try:
                    # Check connection
                    if not self.service:
                        self.logger.info("Reconnecting to Gmail...")
                        self._connect_gmail()

                    items = self.check_for_updates()
                    if items:
                        self.logger.info(f"Found {len(items)} new item(s)")
                        for item in items:
                            try:
                                filepath = self.create_action_file(item)
                                self.logger.info(f"Created action file: {filepath.name}")
                            except Exception as e:
                                self.logger.error(f"Failed to create action file: {e}")

                except HttpError as error:
                    if error.resp.status == 401:
                        self.logger.warning("Authentication expired, reconnecting...")
                        self.service = None
                    else:
                        self.logger.error(f"Gmail API error: {error}")
                except Exception as e:
                    self.logger.error(f"Error in check loop: {e}")

                # Save state periodically
                self._save_processed_emails()

                # Wait before next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Watcher stopped by user")
        finally:
            self._save_processed_emails()
            self.logger.info("Watcher shutdown complete")


# Import time for the run loop
import time


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python gmail_watcher.py <vault_path> [check_interval]")
        print("Example: python gmail_watcher.py AI_Employee_Vault 120")
        sys.exit(1)

    vault_path = sys.argv[1]
    check_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 120

    if not Path(vault_path).exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    # Check for credentials
    if not Path('credentials.json').exists():
        print("Error: credentials.json not found in current directory")
        print("Please download from Google Cloud Console")
        sys.exit(1)

    watcher = GmailWatcher(vault_path, check_interval=check_interval)
    watcher.run()


if __name__ == "__main__":
    main()
