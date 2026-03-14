import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

from playwright.sync_api import sync_playwright, Page, BrowserContext

class LinkedInPoster:
    """Post content to LinkedIn automatically."""
    
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
        """Start Playwright browser."""
        self.playwright = sync_playwright().start()
        
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_path),
            headless=self.headless,
        )
        
        self.page = self.context.pages[0]
        self.page.goto('https://www.linkedin.com/login')
        time.sleep(3)
    
    def is_logged_in(self) -> bool:
        """Check if logged in to LinkedIn."""
        try:
            self.page.goto('https://www.linkedin.com/feed')
            time.sleep(3)
            return 'feed' in self.page.url
        except:
            return False
    
    def post_content(self, content: str, screenshot: bool = True) -> bool:
        """Post content to LinkedIn."""
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
        """Close browser."""
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
