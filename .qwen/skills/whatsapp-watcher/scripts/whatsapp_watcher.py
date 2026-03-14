import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from base_watcher import BaseWatcher

class WhatsAppWatcher(BaseWatcher):
    """Monitor WhatsApp Web for new messages."""
    
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
        """Start Playwright browser with persistent context."""
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
        """Check if WhatsApp Web is logged in."""
        try:
            chat_list = self.page.query_selector('div[role="navigation"]')
            return chat_list is not None
        except:
            return False
    
    def check_for_updates(self) -> list:
        """Check for new WhatsApp messages."""
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
                lines = text.split('\n')
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
        """Create action file for WhatsApp message."""
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
        """Close browser and cleanup."""
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
