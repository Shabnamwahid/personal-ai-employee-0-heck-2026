import os
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
        """Create action file for email."""
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
