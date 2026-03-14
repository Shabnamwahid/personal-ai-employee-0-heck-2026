#!/usr/bin/env python3
"""Script to create Silver tier skill files."""

import os
from pathlib import Path

SKILLS_BASE = Path(r"C:\Users\abRahman\Desktop\personal-ai-employee-0-heck-2026\.qwen\skills")

# Gmail Watcher SKILL.md
GMAIL_WATCHER_SKILL = """---
name: gmail-watcher
description: |
  Monitor Gmail for new emails and create action files in Obsidian vault.
  Watches specified labels/folders and triggers Claude Code processing for new messages.
  Use for email triage, lead capture, invoice requests, and client communication.
---

# Gmail Watcher

Lightweight Python script that monitors Gmail for new messages and creates actionable Markdown files in your Obsidian vault.

## Prerequisites

1. **Gmail API Setup**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download credentials.json

2. **Install Dependencies**:
   ```bash
   pip install google-auth google-auth-oauthlib google-api-python-client python-dotenv
   ```

3. **Initial Authentication**:
   ```bash
   python scripts/gmail_watcher.py --auth
   ```
   This creates token.json for subsequent API calls.

## Configuration

Create .env file in the skill directory:

```env
# Gmail API credentials
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REDIRECT_URI=http://localhost:8080

# Vault paths
VAULT_ROOT=C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault
INBOX_FOLDER=Inbox
NEEDS_ACTION_FOLDER=Needs_Action

# Watcher settings
POLL_INTERVAL=60  # seconds
LABELS_TO_WATCH=INBOX,IMPORTANT,UNREAD
MAX_RESULTS_PER_POLL=10
```

## Usage

### Start Watcher

```bash
# Run in foreground (testing)
python scripts/gmail_watcher.py

# Run as daemon (production)
pm2 start scripts/gmail_watcher.py --name gmail-watcher --interpreter python
```

### Stop Watcher

```bash
# If running with PM2
pm2 stop gmail-watcher

# If running in foreground
Ctrl+C
```

## Action File Schema

Generated files follow this schema:

```markdown
---
type: email
from: sender@example.com
subject: Invoice Request
received: 2026-01-07T10:30:00Z
priority: high
status: pending
message_id: unique-gmail-id
labels: INBOX, IMPORTANT
---

## Email Content

{full message body}

## Attachments
- invoice.pdf (if any)

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
```

## Verification

```bash
# Check watcher is running
pm2 status gmail-watcher

# View logs
pm2 logs gmail-watcher

# Test Gmail API connection
python scripts/gmail_watcher.py --test
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| token.json not created | Run --auth flag to re-authenticate |
| No emails detected | Check LABELS_TO_WATCH configuration |
| API quota exceeded | Increase POLL_INTERVAL to 300+ seconds |
| Permission denied | Ensure vault folder has write permissions |
| OAuth error | Revoke access and re-authenticate |

## Security Notes

- **Never commit** credentials.json or token.json to version control
- Store secrets in .env file (add to .gitignore)
- Rotate credentials monthly
- Use app-specific passwords if 2FA enabled

## Example Output

```
[2026-01-07 10:30:15] Checking Gmail...
[2026-01-07 10:30:16] Found 2 new messages
[2026-01-07 10:30:17] Created: Needs_Action/EMAIL_invoice_request_2026-01-07.md
[2026-01-07 10:30:18] Created: Needs_Action/EMAIL_client_question_2026-01-07.md
[2026-01-07 10:30:19] State saved. Next poll in 60s.
```
"""

# Base Watcher Python Script
BASE_WATCHER_PY = '''from abc import ABC, abstractmethod
from pathlib import Path
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseWatcher(ABC):
    """Base class for all watcher scripts."""
    
    def __init__(self, vault_root: str):
        self.vault_root = Path(vault_root)
        self.state_file = self.vault_root / '.watcher_state.json'
        self.logger = logging.getLogger(self.__class__.__name__)
        self.needs_action_folder = self.vault_root / 'Needs_Action'
    
    @abstractmethod
    def check_for_updates(self) -> list:
        """Return list of new items to process."""
        pass
    
    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Create .md file in Needs_Action folder."""
        pass
    
    def load_state(self) -> dict:
        """Load processed item IDs."""
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text(encoding='utf-8'))
            return data.get(self.__class__.__name__, {})
        return {}
    
    def save_state(self, state: dict):
        """Save processed item IDs."""
        all_state = {}
        if self.state_file.exists():
            all_state = json.loads(self.state_file.read_text(encoding='utf-8'))
        all_state[self.__class__.__name__] = state
        self.state_file.write_text(json.dumps(all_state, indent=2), encoding='utf-8')
    
    def generate_filename(self, prefix: str, identifier: str) -> str:
        """Generate unique filename."""
        timestamp = datetime.now().strftime('%Y-%m-%d')
        safe_id = ''.join(c for c in identifier if c.isalnum() or c in ' _-')[:50]
        return f"{prefix}_{safe_id}_{timestamp}.md"
    
    def run(self):
        """Main watcher loop."""
        self.logger.info(f"Starting {self.__class__.__name__}...")
        self.logger.info(f"Vault root: {self.vault_root}")
        
        try:
            new_items = self.check_for_updates()
            self.logger.info(f"Found {len(new_items)} new items")
            
            for item in new_items:
                filepath = self.create_action_file(item)
                self.logger.info(f"Created: {filepath.relative_to(self.vault_root)}")
            
            self.logger.info("Watcher cycle complete")
            
        except Exception as e:
            self.logger.error(f"Error in watcher: {e}", exc_info=True)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        vault_root = sys.argv[1]
    else:
        vault_root = input("Enter vault root path: ")
    
    # Subclass should instantiate here
    print(f"Base watcher initialized with vault: {vault_root}")
'''

# Gmail Watcher Python Script
GMAIL_WATCHER_PY = '''import os
import sys
from pathlib import Path
from datetime import datetime
import base64
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from base_watcher import BaseWatcher

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailWatcher(BaseWatcher):
    """Monitor Gmail for new messages and create action files."""
    
    def __init__(self, vault_root: str, credentials_path: str = None):
        super().__init__(vault_root)
        self.credentials_path = Path(credentials_path) if credentials_path else Path(__file__).parent / 'credentials.json'
        self.token_path = Path(__file__).parent / 'token.json'
        self.service = None
        self.poll_interval = int(os.getenv('POLL_INTERVAL', '60'))
        self.max_results = int(os.getenv('MAX_RESULTS_PER_POLL', '10'))
        self.labels_to_watch = os.getenv('LABELS_TO_WATCH', 'INBOX,IMPORTANT,UNREAD').split(',')
    
    def authenticate(self):
        """Perform OAuth2 authentication."""
        creds = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=8080)
            
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        self.logger.info("Gmail API authenticated successfully")
        return self.service
    
    def check_for_updates(self) -> list:
        """Check for new Gmail messages."""
        if not self.service:
            self.authenticate()
        
        try:
            state = self.load_state()
            processed_ids = state.get('processed_message_ids', [])
            
            # List messages
            query = ' '.join([f'label:{label}' for label in self.labels_to_watch])
            results = self.service.users().messages().list(
                userId='me',
                maxResults=self.max_results,
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            new_messages = []
            
            for msg in messages:
                msg_id = msg['id']
                if msg_id not in processed_ids:
                    # Get full message
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg_id,
                        format='metadata',
                        metadataHeaders=['From', 'To', 'Subject', 'Date']
                    ).execute()
                    
                    new_messages.append({
                        'id': msg_id,
                        'headers': {h['name']: h['value'] for h in message['payload']['headers']}
                    })
            
            # Update state
            all_processed = processed_ids + [m['id'] for m in new_messages]
            state['processed_message_ids'] = all_processed[-1000:]  # Keep last 1000
            self.save_state(state)
            
            return new_messages
            
        except HttpError as error:
            self.logger.error(f"Gmail API error: {error}")
            return []
    
    def create_action_file(self, item) -> Path:
        """Create action file for email."""
        headers = item['headers']
        filename = self.generate_filename('EMAIL', headers.get('From', 'unknown'))
        filepath = self.needs_action_folder / filename
        
        received_date = headers.get('Date', datetime.now().isoformat())
        
        content = f"""---
type: email
from: {headers.get('From', 'Unknown')}
to: {headers.get('To', 'Unknown')}
subject: {headers.get('Subject', 'No Subject')}
received: {received_date}
priority: normal
status: pending
message_id: {item['id']}
labels: {', '.join(self.labels_to_watch)}
---

## Email Content

**From:** {headers.get('From', 'Unknown')}

**To:** {headers.get('To', 'Unknown')}

**Subject:** {headers.get('Subject', 'No Subject')}

**Date:** {received_date}

---

## Suggested Actions

- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
- [ ] Create follow-up task
"""
        
        filepath.write_text(content, encoding='utf-8')
        return filepath


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Gmail Watcher')
    parser.add_argument('--auth', action='store_true', help='Authenticate with Gmail API')
    parser.add_argument('--test', action='store_true', help='Test mode (single poll)')
    parser.add_argument('--vault', type=str, help='Vault root path')
    parser.add_argument('--credentials', type=str, help='Path to credentials.json')
    args = parser.parse_args()
    
    vault_root = args.vault or os.getenv('VAULT_ROOT')
    if not vault_root:
        vault_root = input("Enter vault root path: ")
    
    watcher = GmailWatcher(vault_root, args.credentials)
    
    if args.auth:
        watcher.authenticate()
        print("Authentication complete. token.json created.")
        return
    
    if args.test:
        messages = watcher.check_for_updates()
        print(f"Found {len(messages)} new messages:")
        for msg in messages:
            print(f"  - {msg['headers'].get('Subject', 'No Subject')}")
        return
    
    # Run single cycle (for PM2/process manager)
    watcher.run()


if __name__ == '__main__':
    main()
'''


def create_file(path: Path, content: str):
    """Create a file with the given content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f"Created: {path}")


def main():
    # Create Gmail Watcher files
    create_file(SKILLS_BASE / 'gmail-watcher' / 'SKILL.md', GMAIL_WATCHER_SKILL)
    create_file(SKILLS_BASE / 'gmail-watcher' / 'scripts' / 'base_watcher.py', BASE_WATCHER_PY)
    create_file(SKILLS_BASE / 'gmail-watcher' / 'scripts' / 'gmail_watcher.py', GMAIL_WATCHER_PY)
    
    print("\n✓ Gmail Watcher skill created successfully!")
    print("\nNext steps:")
    print("1. Set up Gmail API credentials at https://console.cloud.google.com/")
    print("2. Download credentials.json to skills/gmail-watcher/scripts/")
    print("3. Run: python scripts/gmail_watcher.py --auth")
    print("4. Run: python scripts/gmail_watcher.py --vault <path_to_vault>")


if __name__ == '__main__':
    main()
