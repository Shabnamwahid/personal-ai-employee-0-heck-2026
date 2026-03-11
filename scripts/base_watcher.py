#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Watcher - Abstract base class for all watcher scripts.

Watchers are lightweight Python scripts that run continuously in the background,
monitoring various inputs (Gmail, WhatsApp, filesystem) and creating actionable
files for Claude Code to process.

All watchers follow this pattern:
1. Poll for new items at regular intervals
2. Create .md files in the Needs_Action folder
3. Track processed items to avoid duplicates
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class BaseWatcher(ABC):
    """
    Abstract base class for all watcher implementations.
    
    Subclasses must implement:
    - check_for_updates(): Return list of new items to process
    - create_action_file(item): Create .md file in Needs_Action folder
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path).resolve()
        self.needs_action = self.vault_path / 'Needs_Action'
        self.inbox = self.vault_path / 'Inbox'
        self.logs = self.vault_path / 'Logs'
        self.check_interval = check_interval
        
        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Track processed items (in-memory for now)
        self.processed_ids: set = set()
        
        # State file for persistence across restarts
        self.state_file = self.vault_path / '.watcher_state.json'
        self._load_state()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging to both file and console."""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        
        # File handler
        log_file = self.logs / f'watcher_{datetime.now().strftime("%Y-%m-%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def _load_state(self):
        """Load processed IDs from state file."""
        import json
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.processed_ids = set(state.get('processed_ids', []))
                self.logger.info(f"Loaded {len(self.processed_ids)} processed IDs from state")
            except Exception as e:
                self.logger.warning(f"Failed to load state: {e}")
    
    def _save_state(self):
        """Save processed IDs to state file."""
        import json
        try:
            # Only keep last 1000 IDs to prevent unbounded growth
            recent_ids = list(self.processed_ids)[-1000:]
            with open(self.state_file, 'w') as f:
                json.dump({'processed_ids': recent_ids}, f)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
    
    @abstractmethod
    def check_for_updates(self) -> list:
        """
        Check for new items to process.
        
        Returns:
            List of items (dicts or objects) that need processing
        """
        pass
    
    @abstractmethod
    def create_action_file(self, item) -> Path:
        """
        Create an action file for the given item.
        
        Args:
            item: The item to create an action file for
            
        Returns:
            Path to the created file
        """
        pass
    
    def run(self):
        """
        Main run loop. Continuously checks for updates and creates action files.
        
        This method runs indefinitely until interrupted (Ctrl+C).
        """
        self.logger.info(f"Starting {self.__class__.__name__}")
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Check interval: {self.check_interval}s")
        
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
                    
                except Exception as e:
                    self.logger.error(f"Error in check loop: {e}")
                
                # Save state periodically
                self._save_state()
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Watcher stopped by user")
        finally:
            # Final state save
            self._save_state()
            self.logger.info("Watcher shutdown complete")
    
    def get_timestamp(self) -> str:
        """Get current ISO format timestamp."""
        return datetime.now().isoformat()
    
    def sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string for use as a filename.
        
        Args:
            name: The original name
            
        Returns:
            Sanitized filename-safe string
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()
