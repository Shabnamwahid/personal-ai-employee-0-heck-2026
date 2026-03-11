#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File System Watcher - Monitors a drop folder for new files.

This watcher monitors the Inbox folder for any new files dropped by the user
or other systems. When a new file is detected, it creates an action file
in the Needs_Action folder for Claude Code to process.

Usage:
    python filesystem_watcher.py /path/to/AI_Employee_Vault

For Bronze Tier: This is the simplest watcher to implement and test.
"""

import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from base_watcher import BaseWatcher


class FilesystemWatcher(BaseWatcher):
    """
    Watches the Inbox folder for new files.
    
    When a new file is detected:
    1. Copy it to Needs_Action folder
    2. Create a metadata .md file with file details
    3. Track the file hash to avoid reprocessing
    """
    
    def __init__(self, vault_path: str, check_interval: int = 5):
        """
        Initialize the filesystem watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 5 for responsive UI)
        """
        super().__init__(vault_path, check_interval)
        self.drop_folder = self.inbox  # Files dropped in Inbox
        self.processed_hashes: set = set()
        self._load_processed_hashes()
    
    def _load_processed_hashes(self):
        """Load file hashes from state."""
        hash_file = self.vault_path / '.processed_files.json'
        if hash_file.exists():
            import json
            try:
                with open(hash_file, 'r') as f:
                    state = json.load(f)
                    self.processed_hashes = set(state.get('hashes', []))
                self.logger.info(f"Loaded {len(self.processed_hashes)} file hashes")
            except Exception as e:
                self.logger.warning(f"Failed to load hashes: {e}")
    
    def _save_processed_hashes(self):
        """Save file hashes to state."""
        import json
        hash_file = self.vault_path / '.processed_files.json'
        try:
            # Keep last 500 hashes
            recent_hashes = list(self.processed_hashes)[-500:]
            with open(hash_file, 'w') as f:
                json.dump({'hashes': recent_hashes}, f)
        except Exception as e:
            self.logger.error(f"Failed to save hashes: {e}")
    
    def _calculate_hash(self, filepath: Path) -> str:
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to hash {filepath}: {e}")
            return ""
    
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check for new files in the drop folder.
        
        Returns:
            List of file info dicts for new files
        """
        new_files = []
        
        if not self.drop_folder.exists():
            return new_files
        
        # Scan for files (not directories, not .md files which are action files)
        for filepath in self.drop_folder.iterdir():
            if filepath.is_file() and not filepath.name.endswith('.md'):
                file_hash = self._calculate_hash(filepath)
                
                if file_hash and file_hash not in self.processed_hashes:
                    new_files.append({
                        'path': filepath,
                        'name': filepath.name,
                        'size': filepath.stat().st_size,
                        'hash': file_hash,
                        'modified': datetime.fromtimestamp(
                            filepath.stat().st_mtime
                        ).isoformat()
                    })
        
        return new_files
    
    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create an action file for the dropped file.
        
        Args:
            item: File info dict from check_for_updates
            
        Returns:
            Path to the created action file
        """
        # Copy the file to Needs_Action
        dest_path = self.needs_action / f"FILE_{item['name']}"
        shutil.copy2(item['path'], dest_path)
        
        # Create metadata file
        meta_path = self.needs_action / f"FILE_{self.sanitize_filename(item['name'])}.md"
        
        # Determine suggested action based on file type
        suggested_actions = self._get_suggested_actions(item['name'])
        
        content = f"""---
type: file_drop
original_name: {item['name']}
size: {item['size']} bytes
received: {self.get_timestamp()}
file_hash: {item['hash']}
status: pending
priority: normal
---

# File Dropped for Processing

**Original Name:** {item['name']}  
**Size:** {self._format_size(item['size'])}  
**Received:** {item['modified']}

## Content Preview

*Review the attached file and determine appropriate action*

## Suggested Actions

{suggested_actions}

## Notes

*Add any relevant notes or context here*

---
*Created by Filesystem Watcher*
"""
        
        meta_path.write_text(content)
        
        # Track this file
        self.processed_hashes.add(item['hash'])
        self._save_processed_hashes()
        
        # Remove original from inbox (it's now in Needs_Action)
        try:
            item['path'].unlink()
        except Exception as e:
            self.logger.warning(f"Could not remove original file: {e}")
        
        return meta_path
    
    def _get_suggested_actions(self, filename: str) -> str:
        """Get suggested actions based on file type."""
        ext = Path(filename).suffix.lower()
        
        actions = {
            '.pdf': '- [ ] Review document content\n- [ ] Extract key information\n- [ ] File appropriately',
            '.doc': '- [ ] Review document\n- [ ] Edit if needed\n- [ ] Save final version',
            '.docx': '- [ ] Review document\n- [ ] Edit if needed\n- [ ] Save final version',
            '.txt': '- [ ] Read content\n- [ ] Take action based on content',
            '.csv': '- [ ] Review data\n- [ ] Process or import as needed',
            '.xlsx': '- [ ] Review spreadsheet\n- [ ] Update or analyze data',
            '.xls': '- [ ] Review spreadsheet\n- [ ] Update or analyze data',
            '.jpg': '- [ ] Review image\n- [ ] Add to appropriate project',
            '.jpeg': '- [ ] Review image\n- [ ] Add to appropriate project',
            '.png': '- [ ] Review image\n- [ ] Add to appropriate project',
        }
        
        return actions.get(ext, '- [ ] Review file content\n- [ ] Determine appropriate action\n- [ ] Process and move to Done')
    
    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python filesystem_watcher.py <vault_path>")
        print("Example: python filesystem_watcher.py ./AI_Employee_Vault")
        sys.exit(1)
    
    vault_path = sys.argv[1]
    
    # Validate vault path
    if not Path(vault_path).exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)
    
    watcher = FilesystemWatcher(vault_path, check_interval=5)
    watcher.run()


if __name__ == "__main__":
    main()
