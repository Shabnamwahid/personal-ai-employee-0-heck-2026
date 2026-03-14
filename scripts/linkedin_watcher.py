#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Watcher - Monitor LinkedIn for notifications and messages.

This watcher uses Playwright to automate LinkedIn Web, checking for:
- New connection requests
- New messages
- Job alerts
- Post engagement (likes, comments)
- Business opportunities

Features:
- Monitors LinkedIn notifications
- Filters by keywords (opportunity, hiring, project, etc.)
- Creates structured action files
- Tracks processed notifications
- Session persistence (login once)

Usage:
    python linkedin_watcher.py AI_Employee_Vault

First Run:
- Browser will open for manual LinkedIn login
- Session will be saved for subsequent runs
- Keep browser window open during initial login

Note: Be aware of LinkedIn's Terms of Service when using automation.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Playwright imports
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from playwright._impl._errors import TargetClosedError

# Import base watcher
from base_watcher import BaseWatcher


# Keywords indicating business opportunities
OPPORTUNITY_KEYWORDS = [
    'hiring', 'job', 'opportunity', 'project', 'freelance',
    'contract', 'consulting', 'partnership', 'collaboration',
    'investment', 'funding', 'client', 'lead', 'prospect',
    'interview', 'position', 'role', 'opening'
]

# Notification types
NOTIFICATION_TYPES = {
    'connection': 'New connection request',
    'message': 'New message',
    'job': 'Job alert',
    'engagement': 'Post engagement',
    'opportunity': 'Business opportunity',
    'other': 'General notification'
}


class LinkedInWatcher(BaseWatcher):
    """
    LinkedIn Watcher - Monitors LinkedIn Web for notifications.

    Creates action files for:
    - New connection requests
    - Messages with opportunity keywords
    - Job alerts matching criteria
    - Business opportunities
    """

    def __init__(self, vault_path: str, session_path: str = None, check_interval: int = 300):
        """
        Initialize the LinkedIn Watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            session_path: Path to save browser session (default: ./linkedin_session)
            check_interval: Seconds between checks (default: 300 = 5 min)
        """
        super().__init__(vault_path, check_interval)

        # Session path for persistent login
        self.session_path = Path(session_path) if session_path else Path('linkedin_session')
        self.session_path.mkdir(parents=True, exist_ok=True)

        # Playwright objects
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # Track processed notifications
        self._load_linkedin_state()

        self.logger.info(f"LinkedIn Watcher initialized")
        self.logger.info(f"Session path: {self.session_path}")
        self.logger.info(f"Checking every {check_interval}s")

    def _start_browser(self):
        """Start Playwright browser with persistent context."""
        try:
            self.playwright = sync_playwright().start()

            # Launch browser with persistent context
            self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_path),
                headless=True,  # Set to False for debugging
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )

            # Get the first page or create new one
            if self.browser.pages:
                self.page = self.browser.pages[0]
            else:
                self.page = self.browser.new_page()

            # Set viewport
            self.page.set_viewport_size({'width': 1280, 'height': 720})

            self.logger.info("Browser started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start browser: {e}")
            raise

    def _stop_browser(self):
        """Stop the browser and cleanup resources."""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self.logger.info("Browser stopped")
        except Exception as e:
            self.logger.warning(f"Error stopping browser: {e}")

    def _navigate_to_linkedin(self):
        """Navigate to LinkedIn and ensure we're logged in."""
        try:
            self.page.goto('https://www.linkedin.com/feed/', wait_until='networkidle')

            # Check if we're on login page (not authenticated)
            if 'login' in self.page.url.lower():
                self.logger.warning("Not logged in. Please login manually in the browser.")
                # For headless mode, we can't do manual login
                # User needs to run with headless=False first
                return False

            # Wait for page to load
            self.page.wait_for_selector('[data-control-name="nav.home"]', timeout=10000)
            self.logger.info("Successfully navigated to LinkedIn feed")
            return True

        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return False

    def _get_notifications(self) -> List[Dict[str, Any]]:
        """
        Scrape LinkedIn notifications.

        Returns:
            List of notification dicts
        """
        notifications = []

        try:
            # Navigate to notifications page
            self.page.goto('https://www.linkedin.com/notifications/', wait_until='networkidle')
            time.sleep(3)  # Wait for content to load

            # Find notification containers
            # Note: These selectors may need updates as LinkedIn changes their UI
            notification_elements = self.page.query_selector_all(
                'div.notification-item, div.update-components-text, [class*="notification"]'
            )

            self.logger.info(f"Found {len(notification_elements)} notification elements")

            for i, element in enumerate(notification_elements[:20]):  # Limit to 20
                try:
                    notification = self._parse_notification(element, i)
                    if notification:
                        notifications.append(notification)
                except Exception as e:
                    self.logger.debug(f"Failed to parse notification {i}: {e}")

        except Exception as e:
            self.logger.error(f"Error getting notifications: {e}")

        return notifications

    def _parse_notification(self, element, index: int) -> Optional[Dict[str, Any]]:
        """Parse a single notification element."""
        try:
            # Extract text content
            text = element.inner_text()[:500]

            # Extract actor (who performed the action)
            actor = "Unknown"
            actor_element = element.query_selector('[class*="actor"]')
            if actor_element:
                actor = actor_element.inner_text()[:100]

            # Extract timestamp (relative time like "2h", "1d")
            timestamp_elem = element.query_selector('time, [class*="time"]')
            relative_time = "Unknown"
            if timestamp_elem:
                relative_time = timestamp_elem.get_attribute('datetime') or timestamp_elem.inner_text()

            # Determine notification type
            notif_type = self._classify_notification(text)

            # Check for opportunity keywords
            is_opportunity = any(
                kw.lower() in text.lower() for kw in OPPORTUNITY_KEYWORDS
            )

            return {
                'id': f"li_{index}_{int(time.time())}",
                'type': notif_type,
                'actor': actor,
                'text': text,
                'relative_time': relative_time,
                'is_opportunity': is_opportunity,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None

    def _classify_notification(self, text: str) -> str:
        """Classify notification type based on text."""
        text_lower = text.lower()

        if 'connection request' in text_lower or 'connect with' in text_lower:
            return 'connection'
        elif 'message' in text_lower or 'messaged you' in text_lower:
            return 'message'
        elif 'job' in text_lower or 'hiring' in text_lower:
            return 'job'
        elif 'liked' in text_lower or 'commented' in text_lower or 'congratulated' in text_lower:
            return 'engagement'
        elif any(kw in text_lower for kw in OPPORTUNITY_KEYWORDS):
            return 'opportunity'
        else:
            return 'other'

    def _load_linkedin_state(self):
        """Load processed notification IDs."""
        state_file = self.vault_path / '.linkedin_processed.json'
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.processed_ids = set(state.get('processed_ids', []))
                self.logger.info(f"Loaded {len(self.processed_ids)} processed LinkedIn IDs")
            except Exception as e:
                self.logger.warning(f"Failed to load LinkedIn state: {e}")

    def _save_linkedin_state(self):
        """Save processed notification IDs."""
        state_file = self.vault_path / '.linkedin_processed.json'
        try:
            recent_ids = list(self.processed_ids)[-1000:]
            with open(state_file, 'w') as f:
                json.dump({'processed_ids': recent_ids}, f)
        except Exception as e:
            self.logger.error(f"Failed to save LinkedIn state: {e}")

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check for new LinkedIn notifications.

        Returns:
            List of new notification dicts
        """
        try:
            # Ensure browser is running
            if not self.browser:
                self._start_browser()

            # Navigate to LinkedIn
            if not self._navigate_to_linkedin():
                self.logger.warning("Could not navigate to LinkedIn")
                return []

            # Get notifications
            notifications = self._get_notifications()

            # Filter out processed
            new_notifications = [
                n for n in notifications
                if n['id'] not in self.processed_ids
            ]

            self.logger.info(f"{len(new_notifications)} new notifications")
            return new_notifications

        except TargetClosedError:
            self.logger.warning("Browser closed, will restart")
            self._stop_browser()
            self.browser = None
            return []
        except Exception as e:
            self.logger.error(f"Error checking LinkedIn: {e}")
            return []

    def create_action_file(self, notification: Dict[str, Any]) -> Path:
        """
        Create an action file for the notification.

        Args:
            notification: LinkedIn notification dict

        Returns:
            Path to created action file
        """
        # Mark as processed
        self.processed_ids.add(notification['id'])
        self._save_linkedin_state()

        # Determine priority
        priority = 'high' if notification['is_opportunity'] else 'normal'
        if notification['type'] == 'connection':
            priority = 'normal'

        # Create suggested actions
        suggested_actions = ['- [ ] Review notification']
        if notification['type'] == 'connection':
            suggested_actions.append('- [ ] Accept/decline connection request')
            suggested_actions.append('- [ ] Send personalized welcome message')
        elif notification['type'] == 'message':
            suggested_actions.append('- [ ] Read and respond to message')
        elif notification['type'] == 'job':
            suggested_actions.append('- [ ] Review job opportunity')
            suggested_actions.append('- [ ] Apply if interested')
        elif notification['type'] == 'opportunity':
            suggested_actions.append('- [ ] HIGH PRIORITY: Business opportunity')
            suggested_actions.append('- [ ] Evaluate and respond')

        # Create content
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        content = f"""---
type: linkedin
notification_id: {notification['id']}
source: LinkedIn
from: {notification['actor']}
notification_type: {notification['type']}
received: {notification['timestamp']}
priority: {priority}
status: new
is_opportunity: {notification['is_opportunity']}
processed: {timestamp}
---

# LinkedIn Notification

## Details
**Type:** {NOTIFICATION_TYPES.get(notification['type'], notification['type'])}  
**From:** {notification['actor']}  
**Received:** {notification['relative_time']}  
**Opportunity:** {'Yes ⚠️' if notification['is_opportunity'] else 'No'}

## Notification Content

```
{notification['text']}
```

## Suggested Actions
{chr(10).join(suggested_actions)}

## Business Context
- **Priority Level:** {priority}
- **Notification Type:** {notification['type']}
- **Contains Opportunity Keywords:** {notification['is_opportunity']}

## Follow-up Notes
*Add your notes here after reviewing this notification*

---
*Created by LinkedIn Watcher - AI Employee v0.2 (Silver Tier)*
"""

        # Create filename
        safe_actor = self.sanitize_filename(notification['actor'][:30])
        notif_type = notification['type']
        filename = f"LINKEDIN_{notif_type.upper()}_{safe_actor}_{int(time.time())}.md"
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
        self.logger.info(f"Session path: {self.session_path}")

        try:
            while True:
                try:
                    items = self.check_for_updates()
                    if items:
                        self.logger.info(f"Found {len(items)} new item(s)")
                        for item in items:
                            try:
                                filepath = self.create_action_file(item)
                                self.logger.info(f"Created action file: {filepath.name}")
                            except Exception as e:
                                self.logger.error(f"Failed to create action file: {e}")

                except TargetClosedError:
                    self.logger.warning("Browser closed, restarting...")
                    self._stop_browser()
                    self.browser = None
                except Exception as e:
                    self.logger.error(f"Error in check loop: {e}")

                # Save state periodically
                self._save_linkedin_state()

                # Wait before next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Watcher stopped by user")
        finally:
            self._save_linkedin_state()
            self._stop_browser()
            self.logger.info("Watcher shutdown complete")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python linkedin_watcher.py <vault_path> [check_interval]")
        print("Example: python linkedin_watcher.py AI_Employee_Vault 300")
        sys.exit(1)

    vault_path = sys.argv[1]
    check_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300

    if not Path(vault_path).exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    watcher = LinkedInWatcher(vault_path, check_interval=check_interval)
    watcher.run()


if __name__ == "__main__":
    main()
