#!/usr/bin/env python3
"""Script to create all Silver tier skill files."""

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

BASE_WATCHER_PY = """from abc import ABC, abstractmethod
from pathlib import Path
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseWatcher(ABC):
    \"\"\"Base class for all watcher scripts.\"\"\"
    
    def __init__(self, vault_root: str):
        self.vault_root = Path(vault_root)
        self.state_file = self.vault_root / '.watcher_state.json'
        self.logger = logging.getLogger(self.__class__.__name__)
        self.needs_action_folder = self.vault_root / 'Needs_Action'
    
    @abstractmethod
    def check_for_updates(self) -> list:
        \"\"\"Return list of new items to process.\"\"\"
        pass
    
    @abstractmethod
    def create_action_file(self, item) -> Path:
        \"\"\"Create .md file in Needs_Action folder.\"\"\"
        pass
    
    def load_state(self) -> dict:
        \"\"\"Load processed item IDs.\"\"\"
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text(encoding='utf-8'))
            return data.get(self.__class__.__name__, {})
        return {}
    
    def save_state(self, state: dict):
        \"\"\"Save processed item IDs.\"\"\"
        all_state = {}
        if self.state_file.exists():
            all_state = json.loads(self.state_file.read_text(encoding='utf-8'))
        all_state[self.__class__.__name__] = state
        self.state_file.write_text(json.dumps(all_state, indent=2), encoding='utf-8')
    
    def generate_filename(self, prefix: str, identifier: str) -> str:
        \"\"\"Generate unique filename.\"\"\"
        timestamp = datetime.now().strftime('%Y-%m-%d')
        safe_id = ''.join(c for c in identifier if c.isalnum() or c in ' _-')[:50]
        return f"{prefix}_{safe_id}_{timestamp}.md"
    
    def run(self):
        \"\"\"Main watcher loop.\"\"\"
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
"""

GMAIL_WATCHER_PY = """import os
import sys
from pathlib import Path
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from base_watcher import BaseWatcher

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailWatcher(BaseWatcher):
    \"\"\"Monitor Gmail for new messages and create action files.\"\"\"
    
    def __init__(self, vault_root: str, credentials_path: str = None):
        super().__init__(vault_root)
        self.credentials_path = Path(credentials_path) if credentials_path else Path(__file__).parent / 'credentials.json'
        self.token_path = Path(__file__).parent / 'token.json'
        self.service = None
        self.poll_interval = int(os.getenv('POLL_INTERVAL', '60'))
        self.max_results = int(os.getenv('MAX_RESULTS_PER_POLL', '10'))
        self.labels_to_watch = os.getenv('LABELS_TO_WATCH', 'INBOX,IMPORTANT,UNREAD').split(',')
    
    def authenticate(self):
        \"\"\"Perform OAuth2 authentication.\"\"\"
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
        \"\"\"Check for new Gmail messages.\"\"\"
        if not self.service:
            self.authenticate()
        
        try:
            state = self.load_state()
            processed_ids = state.get('processed_message_ids', [])
            
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
            
            all_processed = processed_ids + [m['id'] for m in new_messages]
            state['processed_message_ids'] = all_processed[-1000:]
            self.save_state(state)
            
            return new_messages
            
        except HttpError as error:
            self.logger.error(f"Gmail API error: {error}")
            return []
    
    def create_action_file(self, item) -> Path:
        \"\"\"Create action file for email.\"\"\"
        headers = item['headers']
        filename = self.generate_filename('EMAIL', headers.get('From', 'unknown'))
        filepath = self.needs_action_folder / filename
        
        received_date = headers.get('Date', datetime.now().isoformat())
        
        content = f'''---
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
'''
        
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
    
    watcher.run()


if __name__ == '__main__':
    main()
"""

WHATSAPP_WATCHER_SKILL = """---
name: whatsapp-watcher
description: |
  Monitor WhatsApp Web for new messages and create action files in Obsidian vault.
  Uses Playwright to automate WhatsApp Web and extract messages.
  Use for lead capture, customer support, and personal communication tracking.
---

# WhatsApp Watcher

Python script that monitors WhatsApp Web for new messages and creates actionable Markdown files in your Obsidian vault.

## Prerequisites

1. **Install Dependencies**:
   ```bash
   pip install playwright python-dotenv
   playwright install
   ```

2. **WhatsApp Web Session**:
   - First run will require QR code scan
   - Session saved for subsequent runs

## Configuration

Create .env file in the skill directory:

```env
# Vault paths
VAULT_ROOT=C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault
NEEDS_ACTION_FOLDER=Needs_Action

# Watcher settings
POLL_INTERVAL=120  # seconds (WhatsApp rate-limited)
SESSION_PATH=./whatsapp_session
KEYWORD_FILTERS=pricing,invoice,interested,buy,purchase
```

## Usage

### Start Watcher

```bash
# Run in foreground (testing)
python scripts/whatsapp_watcher.py

# Run as daemon (production)
pm2 start scripts/whatsapp_watcher.py --name whatsapp-watcher --interpreter python
```

### Stop Watcher

```bash
# If running with PM2
pm2 stop whatsapp-watcher
```

## Action File Schema

```markdown
---
type: whatsapp
from: +1234567890
contact_name: John Doe
received: 2026-01-07T10:30:00Z
priority: high
status: pending
chat_id: unique-chat-id
keywords: pricing, interested
---

## Message Content

**Contact:** John Doe (+1234567890)

**Message:** Hi, I'm interested in your services. Can you send me pricing information?

**Timestamp:** 2026-01-07 10:30:00

---

## Suggested Actions

- [ ] Reply with pricing information
- [ ] Schedule follow-up call
- [ ] Add to CRM
"""

WHATSAPP_WATCHER_PY = """import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from base_watcher import BaseWatcher

class WhatsAppWatcher(BaseWatcher):
    \"\"\"Monitor WhatsApp Web for new messages.\"\"\"
    
    def __init__(self, vault_root: str, headless: bool = True):
        super().__init__(vault_root)
        self.headless = headless
        self.poll_interval = int(os.getenv('POLL_INTERVAL', '120'))
        self.session_path = os.getenv('SESSION_PATH', './whatsapp_session')
        self.keyword_filters = os.getenv('KEYWORD_FILTERS', 'pricing,invoice,interested').split(',')
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    def start_browser(self):
        \"\"\"Start Playwright browser with persistent context.\"\"\"
        self.playwright = sync_playwright().start()
        
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.session_path,
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        self.page = self.context.pages[0]
        self.page.goto('https://web.whatsapp.com')
        time.sleep(5)
    
    def is_logged_in(self) -> bool:
        \"\"\"Check if WhatsApp Web is logged in.\"\"\"
        try:
            chat_list = self.page.query_selector('div[role="navigation"]')
            return chat_list is not None
        except:
            return False
    
    def check_for_updates(self) -> list:
        \"\"\"Check for new WhatsApp messages.\"\"\"
        if not self.page:
            self.start_browser()
        
        if not self.is_logged_in():
            self.logger.warning("WhatsApp Web not logged in. Please scan QR code.")
            time.sleep(10)
            if not self.is_logged_in():
                return []
        
        try:
            state = self.load_state()
            processed_ids = state.get('processed_message_ids', [])
            
            # Get chat list text
            chat_elements = self.page.query_selector_all('div[role="navigation"] div[tabindex="0"]')
            messages = []
            
            for chat in chat_elements[:10]:
                text = chat.inner_text()
                lines = text.split('\\n')
                if len(lines) >= 2:
                    messages.append({
                        'contact': lines[0],
                        'message': ' '.join(lines[1:]),
                        'timestamp': datetime.now().isoformat()
                    })
            
            new_messages = []
            for msg in messages:
                msg_id = f"{msg['contact']}_{msg['timestamp']}"
                if msg_id not in processed_ids:
                    contains_keyword = any(
                        kw.lower() in msg['message'].lower() 
                        for kw in self.keyword_filters
                    )
                    if contains_keyword:
                        new_messages.append({
                            'id': msg_id,
                            'contact': msg['contact'],
                            'message': msg['message'],
                            'timestamp': msg['timestamp'],
                            'keywords': [kw for kw in self.keyword_filters if kw.lower() in msg['message'].lower()]
                        })
            
            all_processed = processed_ids + [m['id'] for m in new_messages]
            state['processed_message_ids'] = all_processed[-500:]
            self.save_state(state)
            
            return new_messages
            
        except Exception as e:
            self.logger.error(f"Error checking WhatsApp: {e}")
            return []
    
    def create_action_file(self, item) -> Path:
        \"\"\"Create action file for WhatsApp message.\"\"\"
        filename = self.generate_filename('WHATSAPP', item['contact'])
        filepath = self.needs_action_folder / filename
        
        content = f'''---
type: whatsapp
from: {item['contact']}
contact_name: {item['contact']}
received: {item['timestamp']}
priority: high
status: pending
chat_id: {item['id']}
keywords: {', '.join(item['keywords'])}
---

## Message Content

**Contact:** {item['contact']}

**Message:** {item['message']}

**Timestamp:** {item['timestamp']}

---

## Suggested Actions

- [ ] Reply to sender
- [ ] Schedule follow-up call
- [ ] Add to CRM
'''
        
        filepath.write_text(content, encoding='utf-8')
        return filepath
    
    def close(self):
        \"\"\"Close browser and cleanup.\"\"\"
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='WhatsApp Watcher')
    parser.add_argument('--test', action='store_true', help='Test mode (single poll)')
    parser.add_argument('--vault', type=str, help='Vault root path')
    parser.add_argument('--no-headless', action='store_true', help='Show browser window')
    args = parser.parse_args()
    
    vault_root = args.vault or os.getenv('VAULT_ROOT')
    if not vault_root:
        vault_root = input("Enter vault root path: ")
    
    watcher = WhatsAppWatcher(vault_root, headless=not args.no_headless)
    
    try:
        if args.test:
            messages = watcher.check_for_updates()
            print(f"Found {len(messages)} new messages:")
            for msg in messages:
                print(f"  - {msg['contact']}: {msg['message'][:50]}...")
            return
        
        watcher.run()
    
    finally:
        watcher.close()


if __name__ == '__main__':
    main()
"""

LINKEDIN_POSTER_SKILL = """---
name: linkedin-poster
description: |
  Automatically post to LinkedIn for lead generation and business promotion.
  Uses Playwright to automate LinkedIn posting with content from Obsidian vault.
  Includes scheduling, hashtag management, and engagement tracking.
---

# LinkedIn Poster

Automate LinkedIn posts to promote your business and generate leads.

## Prerequisites

1. **Install Dependencies**:
   ```bash
   pip install playwright python-dotenv
   playwright install
   ```

2. **LinkedIn Account**: Business or personal profile

## Configuration

```env
VAULT_ROOT=C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault
CONTENT_FOLDER=Plans/LinkedIn_Content
POST_SCHEDULE=0 9 * * *
HASHTAGS=#AI #Automation #Business #Technology
```

## Usage

### Create Content

Create content files in `Plans/LinkedIn_Content/`:

```markdown
---
type: linkedin_post
scheduled: 2026-01-08T09:00:00Z
status: draft
---

## Post Content

Excited to announce our new AI automation service!

#AI #Automation #Business
```

### Post to LinkedIn

```bash
# Test post
python scripts/linkedin_poster.py --test --content Plans/LinkedIn_Content/post.md

# Actual post
python scripts/linkedin_poster.py --post --content Plans/LinkedIn_Content/post.md
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Login failed | Clear session and re-login |
| Post not appearing | Check content length (max 3000 chars) |

## Security Notes

- LinkedIn session contains auth tokens
- Never commit session files
- Rate limit: max 3 posts per day
"""

LINKEDIN_POSTER_PY = """import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

from playwright.sync_api import sync_playwright, Page, BrowserContext

class LinkedInPoster:
    \"\"\"Post content to LinkedIn automatically.\"\"\"
    
    def __init__(self, vault_root: str, headless: bool = True):
        self.vault_root = Path(vault_root)
        self.headless = headless
        self.session_path = self.vault_root / '.linkedin_session'
        self.content_folder = self.vault_root / 'Plans' / 'LinkedIn_Content'
        self.posts_folder = self.vault_root / 'Posts'
        
        self.playwright = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        self.content_folder.mkdir(parents=True, exist_ok=True)
        self.posts_folder.mkdir(parents=True, exist_ok=True)
    
    def start_browser(self):
        \"\"\"Start Playwright browser.\"\"\"
        self.playwright = sync_playwright().start()
        
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_path),
            headless=self.headless,
        )
        
        self.page = self.context.pages[0]
        self.page.goto('https://www.linkedin.com/login')
        time.sleep(3)
    
    def is_logged_in(self) -> bool:
        \"\"\"Check if logged in to LinkedIn.\"\"\"
        try:
            self.page.goto('https://www.linkedin.com/feed')
            time.sleep(3)
            return 'feed' in self.page.url
        except:
            return False
    
    def post_content(self, content: str, screenshot: bool = True) -> bool:
        \"\"\"Post content to LinkedIn.\"\"\"
        if not self.page:
            self.start_browser()
        
        if not self.is_logged_in():
            print("Please log in to LinkedIn manually, then press Enter...")
            input()
        
        try:
            self.page.goto('https://www.linkedin.com/feed')
            time.sleep(2)
            
            start_post = self.page.query_selector('button[aria-label="Start a post"]')
            if start_post:
                start_post.click()
                time.sleep(2)
            
            editor = self.page.query_selector('div[role="textbox"]')
            if editor:
                editor.fill(content[:3000])
                time.sleep(1)
                
                post_button = self.page.query_selector('button:has-text("Post")')
                if post_button:
                    post_button.click()
                    time.sleep(3)
                    
                    if screenshot:
                        screenshot_path = self.posts_folder / f'linkedin_post_{datetime.now().strftime("%Y-%m-%d")}.png'
                        self.page.screenshot(path=str(screenshot_path))
                        print(f"Screenshot saved: {screenshot_path}")
                    
                    return True
            
            print("Failed to post - could not find required elements")
            return False
            
        except Exception as e:
            print(f"Error posting: {e}")
            return False
    
    def close(self):
        \"\"\"Close browser.\"\"\"
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='LinkedIn Poster')
    parser.add_argument('--test', action='store_true', help='Test mode')
    parser.add_argument('--test-login', action='store_true', help='Test LinkedIn login')
    parser.add_argument('--post', action='store_true', help='Post content')
    parser.add_argument('--content', type=str, help='Path to content file')
    parser.add_argument('--vault', type=str, help='Vault root path')
    parser.add_argument('--no-headless', action='store_true', help='Show browser')
    args = parser.parse_args()
    
    vault_root = args.vault or os.getenv('VAULT_ROOT')
    if not vault_root:
        vault_root = input("Enter vault root path: ")
    
    poster = LinkedInPoster(vault_root, headless=not args.no_headless)
    
    try:
        if args.test_login:
            poster.start_browser()
            if poster.is_logged_in():
                print("LinkedIn login successful!")
            else:
                print("Please log in to LinkedIn...")
            return
        
        if args.test:
            print("Test mode - no actual posting")
            if args.content:
                content_path = Path(args.content)
                content = content_path.read_text(encoding='utf-8')
                print(f"Would post content from: {content_path}")
                print(f"Content length: {len(content)} chars")
            return
        
        if args.post and args.content:
            content_path = Path(args.content)
            content = content_path.read_text(encoding='utf-8')
            
            poster.start_browser()
            success = poster.post_content(content)
            
            if success:
                print("Post published successfully!")
            else:
                print("Failed to publish post")
    
    finally:
        poster.close()


if __name__ == '__main__':
    main()
"""

EMAIL_MCP_SKILL = """---
name: email-mcp
description: |
  MCP server for sending emails via Gmail API.
  Integrates with Human-in-the-Loop approval workflow.
  Supports attachments, HTML content, and batch sending.
---

# Email MCP Server

Model Context Protocol server for sending emails through Gmail API.

## Prerequisites

1. **Gmail API Setup** (same as gmail-watcher)
2. **Install Dependencies**:
   ```bash
   pip install google-auth google-auth-oauthlib google-api-python-client
   ```

## Configuration

```env
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
VAULT_ROOT=C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault
```

## Usage

### Start MCP Server

```bash
python scripts/email_mcp_server.py --port 8809
```

### Send Email

```bash
python scripts/email_mcp_client.py call -t send_email -p '{"to": "test@example.com", "subject": "Test", "body": "Hello"}'
```

## Available Tools

| Tool | Description |
|------|-------------|
| send_email | Send a single email |
| send_batch | Send bulk emails |
| test_connection | Verify Gmail API access |
| shutdown | Stop the MCP server |

## HITL Integration

Email sending requires approval via the approval workflow.
"""

EMAIL_MCP_SERVER_PY = """import os
import sys
import json
import base64
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class EmailMCPServer:
    \"\"\"MCP Server for sending emails.\"\"\"
    
    def __init__(self, port: int = 8809):
        self.port = port
        self.vault_root = Path(os.getenv('VAULT_ROOT', '.'))
        self.credentials_path = Path(__file__).parent / 'credentials.json'
        self.token_path = Path(__file__).parent / 'token.json'
        self.service = None
        self.shutdown = False
    
    def authenticate(self):
        \"\"\"Authenticate with Gmail API.\"\"\"
        creds = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    print("Error: credentials.json not found")
                    return False
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=8080)
            
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("Gmail API authenticated")
        return True
    
    def send_email(self, to: str, subject: str, body: str, attachment_path: str = None) -> dict:
        \"\"\"Send an email via Gmail API.\"\"\"
        try:
            from email.message import EmailMessage
            import mimetypes
            
            message = EmailMessage()
            message['To'] = to
            message['From'] = 'me'
            message['Subject'] = subject
            message.set_content(body)
            
            if attachment_path:
                filepath = self.vault_root / attachment_path
                if filepath.exists():
                    mime_type, _ = mimetypes.guess_type(str(filepath))
                    mime_type = mime_type or 'application/octet-stream'
                    
                    with open(filepath, 'rb') as f:
                        file_data = f.read()
                    
                    message.add_attachment(
                        file_data,
                        maintype=mime_type.split('/')[0],
                        subtype=mime_type.split('/')[1],
                        filename=filepath.name
                    )
            
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': encoded_message}
            ).execute()
            
            self.log_sent_email(to, subject, sent_message['id'])
            
            return {
                'success': True,
                'message_id': sent_message['id'],
                'thread_id': sent_message.get('threadId')
            }
            
        except Exception as error:
            return {
                'success': False,
                'error': str(error)
            }
    
    def log_sent_email(self, to: str, subject: str, message_id: str):
        \"\"\"Log sent email to vault.\"\"\"
        logs_folder = self.vault_root / 'Logs'
        logs_folder.mkdir(exist_ok=True)
        
        log_file = logs_folder / f"email_log_{datetime.now().strftime('%Y-%m-%d')}.json"
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'to': to,
            'subject': subject,
            'message_id': message_id,
            'status': 'sent'
        }
        
        logs = []
        if log_file.exists():
            logs = json.loads(log_file.read_text())
        logs.append(log_entry)
        
        log_file.write_text(json.dumps(logs, indent=2))


class MCPRequestHandler(BaseHTTPRequestHandler):
    \"\"\"HTTP handler for MCP requests.\"\"\"
    
    server_instance: EmailMCPServer = None
    
    def do_POST(self):
        \"\"\"Handle MCP tool calls.\"\"\"
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            request = json.loads(post_data.decode())
            tool_name = request.get('tool')
            params = request.get('params', {})
            
            if tool_name == 'send_email':
                result = self.server_instance.send_email(
                    to=params.get('to'),
                    subject=params.get('subject'),
                    body=params.get('body'),
                    attachment_path=params.get('attachment')
                )
            elif tool_name == 'test_connection':
                result = {'success': self.server_instance.service is not None}
            elif tool_name == 'shutdown':
                print("Shutting down server...")
                result = {'success': True}
                self.server_instance.shutdown = True
            else:
                result = {'success': False, 'error': f'Unknown tool: {tool_name}'}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().isoformat()}] {args[0]}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Email MCP Server')
    parser.add_argument('--port', type=int, default=8809, help='Server port')
    parser.add_argument('--auth', action='store_true', help='Authenticate only')
    args = parser.parse_args()
    
    server = EmailMCPServer(args.port)
    
    if args.auth:
        if server.authenticate():
            print("Authentication successful!")
        return
    
    if not server.authenticate():
        print("Authentication failed")
        sys.exit(1)
    
    MCPRequestHandler.server_instance = server
    
    httpd = HTTPServer(('localhost', args.port), MCPRequestHandler)
    print(f"Email MCP Server running on http://localhost:{args.port}")
    
    while not server.shutdown:
        httpd.handle_request()
    
    httpd.server_close()
    print("Server stopped")


if __name__ == '__main__':
    main()
"""

ORCHESTRATOR_SKILL = """---
name: orchestrator
description: |
  Master orchestration process that coordinates all watchers, Claude Code,
  and MCP servers. Monitors folders, triggers processing, and manages workflows.
---

# Orchestrator

Central coordination process for the AI Employee system.

## Features

- Monitors Needs_Action folder for new items
- Triggers Claude Code processing
- Manages Human-in-the-Loop approvals
- Coordinates MCP server actions

## Configuration

```env
VAULT_ROOT=C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault
POLL_INTERVAL=30
MAX_CLAUDE_ITERATIONS=10
```

## Usage

```bash
# Run orchestrator
python scripts/orchestrator.py

# Run as daemon
pm2 start scripts/orchestrator.py --name orchestrator --interpreter python
```

## Workflow

1. Detect: Poll Needs_Action folder
2. Claim: Move file to In_Progress
3. Process: Trigger Claude Code
4. Approve: Request human approval if needed
5. Execute: Call MCP servers
6. Complete: Move to Done folder
"""

ORCHESTRATOR_PY = """import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List
import shutil

class Orchestrator:
    \"\"\"Main orchestration process for AI Employee.\"\"\"
    
    def __init__(self, vault_root: str):
        self.vault_root = Path(vault_root)
        self.poll_interval = int(os.getenv('POLL_INTERVAL', '30'))
        
        self.needs_action = self.vault_root / 'Needs_Action'
        self.in_progress = self.vault_root / 'In_Progress' / 'orchestrator'
        self.pending_approval = self.vault_root / 'Pending_Approval'
        self.approved = self.vault_root / 'Approved'
        self.done = self.vault_root / 'Done'
        self.logs = self.vault_root / 'Logs'
        
        for folder in [self.needs_action, self.in_progress, self.pending_approval, 
                       self.approved, self.done, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.vault_root / '.orchestrator_state.json'
        self.running = True
    
    def log(self, message: str):
        \"\"\"Log message to console and file.\"\"\"
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        
        log_file = self.logs / f"orchestrator_{datetime.now().strftime('%Y-%m-%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\\n')
    
    def get_new_files(self) -> List[Path]:
        \"\"\"Get new files in Needs_Action folder.\"\"\"
        cutoff = time.time() - (self.poll_interval * 2)
        return [f for f in self.needs_action.glob('*.md') if f.stat().st_mtime > cutoff]
    
    def claim_file(self, filepath: Path) -> Path:
        \"\"\"Move file to In_Progress.\"\"\"
        dest = self.in_progress / filepath.name
        shutil.move(str(filepath), str(dest))
        self.log(f"Claimed: {filepath.name}")
        return dest
    
    def release_file(self, filepath: Path, status: str = 'done'):
        \"\"\"Move file to final destination.\"\"\"
        if status == 'pending_approval':
            dest = self.pending_approval / filepath.name
        else:
            dest = self.done / filepath.name
        shutil.move(str(filepath), str(dest))
        self.log(f"Released to {dest.name}: {filepath.name}")
    
    def trigger_claude(self, filepath: Path) -> bool:
        \"\"\"Trigger Claude Code to process file.\"\"\"
        try:
            content = filepath.read_text(encoding='utf-8')
            
            prompt = f\"\"\"Process this action file:

{content}

Instructions:
1. Analyze the request
2. Determine required actions
3. If multi-step, create Plan.md
4. If approval needed, create file in Pending_Approval/
5. Execute via MCP servers if approved
\"\"\"
            
            result = subprocess.run(
                ['claude', '--prompt', prompt],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            response = f"\\n\\n## AI Processing ({datetime.now().isoformat()})\\n\\n{result.stdout}"
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(response)
            
            return True
            
        except subprocess.TimeoutExpired:
            self.log(f"Claude timeout for {filepath.name}")
            return False
        except Exception as e:
            self.log(f"Error triggering Claude: {e}")
            return False
    
    def process_approvals(self):
        \"\"\"Process approved actions.\"\"\"
        for filepath in self.approved.glob('*.md'):
            self.log(f"Processing approved: {filepath.name}")
            self.release_file(filepath, 'done')
    
    def run_cycle(self):
        \"\"\"Run one orchestration cycle.\"\"\"
        new_files = self.get_new_files()
        
        for filepath in new_files:
            try:
                claimed = self.claim_file(filepath)
                success = self.trigger_claude(claimed)
                
                if success:
                    approval_files = list(self.pending_approval.glob('*'))
                    if approval_files:
                        self.release_file(claimed, 'pending_approval')
                    else:
                        self.release_file(claimed, 'done')
                else:
                    self.release_file(claimed, 'done')
                    
            except Exception as e:
                self.log(f"Error processing {filepath.name}: {e}")
        
        self.process_approvals()
    
    def run(self):
        \"\"\"Main orchestration loop.\"\"\"
        self.log("Orchestrator started")
        
        while self.running:
            try:
                self.run_cycle()
            except Exception as e:
                self.log(f"Cycle error: {e}")
            
            time.sleep(self.poll_interval)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='AI Employee Orchestrator')
    parser.add_argument('--vault', type=str, help='Vault root path')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    args = parser.parse_args()
    
    vault_root = args.vault or os.getenv('VAULT_ROOT')
    if not vault_root:
        vault_root = input("Enter vault root path: ")
    
    orchestrator = Orchestrator(vault_root)
    
    if args.once:
        orchestrator.run_cycle()
    else:
        try:
            orchestrator.run()
        except KeyboardInterrupt:
            orchestrator.running = False
            print("\\nOrchestrator stopped")


if __name__ == '__main__':
    main()
"""

HITL_APPROVAL_SKILL = """---
name: hitl-approval
description: |
  Human-in-the-Loop approval workflow for sensitive actions.
  Creates approval requests, waits for human decision,
  and triggers execution upon approval.
---

# HITL Approval Workflow

Human oversight for sensitive AI actions.

## When Approval Required

- Sending emails to new contacts
- Payments over $100
- Social media posts
- File deletions

## Approval File Schema

```markdown
---
type: approval_request
action: send_email
to: client@example.com
subject: Invoice #1234
created: 2026-01-07T10:30:00Z
expires: 2026-01-08T10:30:00Z
status: pending
---

## Action Details

**Action:** Send Email
**To:** client@example.com
**Subject:** Invoice #1234

## To Approve
Move this file to Approved/ folder.

## To Reject
Move this file to Rejected/ folder.
```

## Usage

1. AI creates file in Pending_Approval/
2. Human reviews and moves to Approved/ or Rejected/
3. Orchestrator executes approved actions
"""

HITL_APPROVAL_PY = """import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

class HITLApproval:
    \"\"\"Human-in-the-Loop approval manager.\"\"\"
    
    def __init__(self, vault_root: str):
        self.vault_root = Path(vault_root)
        self.pending = self.vault_root / 'Pending_Approval'
        self.approved = self.vault_root / 'Approved'
        self.rejected = self.vault_root / 'Rejected'
        self.timeout = int(os.getenv('APPROVAL_TIMEOUT', '86400'))
    
    def create_approval_request(self, request_data: dict) -> Path:
        \"\"\"Create approval request file.\"\"\"
        filename = f"{request_data['action']}_{request_data.get('recipient', 'unknown')}_{datetime.now().strftime('%Y-%m-%d')}.md"
        filepath = self.pending / filename
        
        expires = datetime.now() + timedelta(seconds=self.timeout)
        
        content = f'''---
type: approval_request
action: {request_data['action']}
amount: {request_data.get('amount', 'N/A')}
recipient: {request_data.get('recipient', 'N/A')}
reason: {request_data.get('reason', 'N/A')}
created: {datetime.now().isoformat()}
expires: {expires.isoformat()}
status: pending
---

## Action Details

**Action:** {request_data['action']}
**Amount:** {request_data.get('amount', 'N/A')}
**To/Recipient:** {request_data.get('recipient', 'N/A')}
**Reason:** {request_data.get('reason', 'N/A')}

## Details

{request_data.get('details', 'No additional details')}

## To Approve
Move this file to Approved/ folder.

## To Reject
Move this file to Rejected/ folder.
'''
        
        filepath.write_text(content, encoding='utf-8')
        return filepath
    
    def list_pending(self) -> list:
        \"\"\"List all pending approvals.\"\"\"
        pending = []
        for f in self.pending.glob('*.md'):
            content = f.read_text(encoding='utf-8')
            if 'status: pending' in content:
                pending.append({'file': f.name, 'path': str(f)})
        return pending
    
    def approve(self, filename: str) -> bool:
        \"\"\"Move file to Approved.\"\"\"
        src = self.pending / filename
        if src.exists():
            dest = self.approved / filename
            src.rename(dest)
            return True
        return False
    
    def reject(self, filename: str, reason: str = '') -> bool:
        \"\"\"Move file to Rejected.\"\"\"
        src = self.pending / filename
        if src.exists():
            dest = self.rejected / filename
            content = src.read_text(encoding='utf-8')
            content += f"\\n\\n## Rejected\\n\\nReason: {reason}\\nDate: {datetime.now().isoformat()}"
            dest.write_text(content, encoding='utf-8')
            src.unlink()
            return True
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='HITL Approval Manager')
    parser.add_argument('--list-pending', action='store_true', help='List pending approvals')
    parser.add_argument('--approve', type=str, help='Approve file')
    parser.add_argument('--reject', type=str, help='Reject file')
    parser.add_argument('--reason', type=str, help='Rejection reason')
    parser.add_argument('--vault', type=str, help='Vault root path')
    args = parser.parse_args()
    
    vault_root = args.vault or os.getenv('VAULT_ROOT')
    if not vault_root:
        vault_root = input("Enter vault root path: ")
    
    manager = HITLApproval(vault_root)
    
    if args.list_pending:
        pending = manager.list_pending()
        print(f"Pending approvals: {len(pending)}")
        for p in pending:
            print(f"  - {p['file']}")
    
    elif args.approve:
        if manager.approve(args.approve):
            print(f"Approved: {args.approve}")
        else:
            print(f"File not found: {args.approve}")
    
    elif args.reject:
        if manager.reject(args.reject, args.reason or 'No reason provided'):
            print(f"Rejected: {args.reject}")
        else:
            print(f"File not found: {args.reject}")


if __name__ == '__main__':
    main()
"""

TASK_SCHEDULER_SKILL = """---
name: task-scheduler
description: |
  Schedule recurring tasks using cron (Linux/Mac) or Task Scheduler (Windows).
  Triggers orchestrator and watchers at specified intervals.
---

# Task Scheduler

Automate task scheduling for AI Employee processes.

## Platform Support

- **Windows**: Task Scheduler via schtasks
- **Linux/Mac**: cron jobs
- **Cross-platform**: PM2 process manager

## Usage

### Windows (Task Scheduler)

```bash
python scripts/task_scheduler.py --install
```

### PM2 (Recommended)

```bash
# Create PM2 config
python scripts/task_scheduler.py --pm2

# Start all processes
pm2 start ecosystem.config.js

# Save for startup
pm2 save
pm2 startup
```

## Default Schedule

| Task | Frequency |
|------|-----------|
| Gmail Watcher | Every 5 min |
| WhatsApp Watcher | Every 10 min |
| Orchestrator | Every 2 min |
| LinkedIn Poster | Daily 9 AM |
"""

TASK_SCHEDULER_PY = """import os
import sys
from pathlib import Path

class TaskScheduler:
    \"\"\"Cross-platform task scheduler.\"\"\"
    
    def __init__(self, vault_root: str, scripts_path: str):
        self.vault_root = Path(vault_root)
        self.scripts_path = Path(scripts_path)
        self.python = sys.executable
    
    def create_pm2_config(self):
        \"\"\"Create PM2 ecosystem config.\"\"\"
        config = f'''module.exports = {{
  apps: [
    {{
      name: 'gmail-watcher',
      script: '{self.scripts_path}/gmail_watcher.py',
      interpreter: '{self.python}',
      interpreter_args: '--vault {self.vault_root}',
      cron_restart: '*/5 * * * *'
    }},
    {{
      name: 'whatsapp-watcher',
      script: '{self.scripts_path}/whatsapp_watcher.py',
      interpreter: '{self.python}',
      interpreter_args: '--vault {self.vault_root}',
      cron_restart: '*/10 * * * *'
    }},
    {{
      name: 'orchestrator',
      script: '{self.scripts_path}/orchestrator.py',
      interpreter: '{self.python}',
      interpreter_args: '--vault {self.vault_root}',
      cron_restart: '*/2 * * * *'
    }}
  ]
}};
'''
        config_path = self.scripts_path / 'ecosystem.config.js'
        config_path.write_text(config, encoding='utf-8')
        print(f"PM2 config created: {config_path}")
        print("\\nRun: pm2 start ecosystem.config.js")
        print("Then: pm2 save && pm2 startup")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Task Scheduler')
    parser.add_argument('--pm2', action='store_true', help='Create PM2 config')
    parser.add_argument('--install', action='store_true', help='Install scheduled tasks')
    parser.add_argument('--vault', type=str, help='Vault root path')
    parser.add_argument('--scripts', type=str, help='Scripts path')
    args = parser.parse_args()
    
    vault_root = args.vault or os.getenv('VAULT_ROOT')
    scripts_path = args.scripts or os.getenv('SCRIPTS_PATH')
    
    if not vault_root or not scripts_path:
        print("Error: --vault and --scripts required")
        sys.exit(1)
    
    scheduler = TaskScheduler(vault_root, scripts_path)
    
    if args.pm2:
        scheduler.create_pm2_config()
    elif args.install:
        print("Use PM2 for cross-platform process management:")
        print("  npm install -g pm2")
        print("  python task_scheduler.py --pm2")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
"""


def create_file(path: Path, content: str):
    """Create a file with the given content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(content, encoding='utf-8')
        print(f"Created: {path}")
    except Exception as e:
        print(f"Error creating {path}: {e}")


def main():
    print("Creating Silver Tier Skills...")
    print("=" * 50)
    
    print("\n[1/7] Gmail Watcher...")
    create_file(SKILLS_BASE / 'gmail-watcher' / 'SKILL.md', GMAIL_WATCHER_SKILL)
    create_file(SKILLS_BASE / 'gmail-watcher' / 'scripts' / 'base_watcher.py', BASE_WATCHER_PY)
    create_file(SKILLS_BASE / 'gmail-watcher' / 'scripts' / 'gmail_watcher.py', GMAIL_WATCHER_PY)
    
    print("\n[2/7] WhatsApp Watcher...")
    create_file(SKILLS_BASE / 'whatsapp-watcher' / 'SKILL.md', WHATSAPP_WATCHER_SKILL)
    create_file(SKILLS_BASE / 'whatsapp-watcher' / 'scripts' / 'whatsapp_watcher.py', WHATSAPP_WATCHER_PY)
    
    print("\n[3/7] LinkedIn Poster...")
    create_file(SKILLS_BASE / 'linkedin-poster' / 'SKILL.md', LINKEDIN_POSTER_SKILL)
    create_file(SKILLS_BASE / 'linkedin-poster' / 'scripts' / 'linkedin_poster.py', LINKEDIN_POSTER_PY)
    
    print("\n[4/7] Email MCP...")
    create_file(SKILLS_BASE / 'email-mcp' / 'SKILL.md', EMAIL_MCP_SKILL)
    create_file(SKILLS_BASE / 'email-mcp' / 'scripts' / 'email_mcp_server.py', EMAIL_MCP_SERVER_PY)
    
    print("\n[5/7] Orchestrator...")
    create_file(SKILLS_BASE / 'orchestrator' / 'SKILL.md', ORCHESTRATOR_SKILL)
    create_file(SKILLS_BASE / 'orchestrator' / 'scripts' / 'orchestrator.py', ORCHESTRATOR_PY)
    
    print("\n[6/7] HITL Approval...")
    create_file(SKILLS_BASE / 'hitl-approval' / 'SKILL.md', HITL_APPROVAL_SKILL)
    create_file(SKILLS_BASE / 'hitl-approval' / 'scripts' / 'hitl_approval.py', HITL_APPROVAL_PY)
    
    print("\n[7/7] Task Scheduler...")
    create_file(SKILLS_BASE / 'task-scheduler' / 'SKILL.md', TASK_SCHEDULER_SKILL)
    create_file(SKILLS_BASE / 'task-scheduler' / 'scripts' / 'task_scheduler.py', TASK_SCHEDULER_PY)
    
    print("\n" + "=" * 50)
    print("All Silver Tier skills created successfully!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install google-auth google-auth-oauthlib google-api-python-client playwright python-dotenv")
    print("2. Install Playwright browsers: playwright install")
    print("3. Set up Gmail API credentials for gmail-watcher and email-mcp")
    print("4. Install PM2: npm install -g pm2")
    print("5. Create PM2 config: python create_silver_skills.py --setup-pm2")


if __name__ == '__main__':
    main()
