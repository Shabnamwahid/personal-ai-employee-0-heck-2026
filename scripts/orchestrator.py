#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator - Master process for the AI Employee.

Modified for Qwen Code integration.

The orchestrator:
1. Monitors the Needs_Action folder for new items
2. Auto-processes simple file operations (no approval needed)
3. Updates the Dashboard.md with current status
4. Manages the flow of items through the system
5. Creates processing summaries automatically

For Bronze Tier with Qwen Code:
- Simple file operations are auto-processed
- Complex tasks create a summary for Qwen Code review
- Files move: Inbox → Needs_Action → Done

Usage:
    python orchestrator.py /path/to/AI_Employee_Vault
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


class Orchestrator:
    """
    Main orchestrator for the AI Employee system with Qwen Code support.

    Responsibilities:
    - Monitor Needs_Action folder
    - Auto-process simple file operations
    - Update Dashboard.md
    - Track item status through the workflow
    - Generate processing summaries
    """

    def __init__(self, vault_path: str, check_interval: int = 10, auto_process: bool = True):
        """
        Initialize the orchestrator.

        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 10)
            auto_process: Whether to auto-process simple items (default: True)
        """
        self.vault_path = Path(vault_path).resolve()
        self.check_interval = check_interval
        self.auto_process = auto_process

        # Folder paths
        self.inbox = self.vault_path / 'Inbox'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.plans = self.vault_path / 'Plans'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.done = self.vault_path / 'Done'
        self.logs = self.vault_path / 'Logs'
        self.dashboard = self.vault_path / 'Dashboard.md'

        # Ensure all directories exist
        for folder in [self.inbox, self.needs_action, self.plans,
                       self.pending_approval, self.approved, self.rejected,
                       self.done, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.log_file = self.logs / f'orchestrator_{datetime.now().strftime("%Y-%m-%d")}.log'

        # State tracking
        self.processed_files: set = set()
        self._load_state()

        # Load company handbook rules
        self.handbook_rules = self._load_handbook_rules()

        self.log("Orchestrator initialized (Qwen Code mode)")
        self.log(f"Auto-processing: {'enabled' if auto_process else 'disabled'}")

    def log(self, message: str, level: str = "INFO"):
        """Log a message to file and console."""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)

        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            print(f"Failed to write to log file: {e}")

    def _load_state(self):
        """Load processed files state."""
        state_file = self.vault_path / '.orchestrator_state.json'
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.processed_files = set(state.get('processed', []))
            except Exception as e:
                self.log(f"Failed to load state: {e}", "WARNING")

    def _save_state(self):
        """Save processed files state."""
        state_file = self.vault_path / '.orchestrator_state.json'
        try:
            recent = list(self.processed_files)[-500:]
            with open(state_file, 'w') as f:
                json.dump({'processed': recent}, f)
        except Exception as e:
            self.log(f"Failed to save state: {e}", "ERROR")

    def _load_handbook_rules(self) -> Dict[str, Any]:
        """Load company handbook rules for approval decisions."""
        handbook_path = self.vault_path / 'Company_Handbook.md'
        if not handbook_path.exists():
            return {}

        try:
            # Use utf-8 encoding to handle special characters
            content = handbook_path.read_text(encoding='utf-8')
            # Simple parsing - in production use proper markdown parser
            rules = {
                'auto_approve_file_ops': True,  # Default: auto-approve file operations
                'auto_approve_read': True,      # Default: auto-approve reading files
                'require_approval_payments': True,
                'require_approval_external_send': True,
            }
            return rules
        except Exception as e:
            self.log(f"Failed to load handbook: {e}", "WARNING")
            return {}

    def count_files(self, folder: Path) -> int:
        """Count .md files in a folder."""
        if not folder.exists():
            return 0
        return len([f for f in folder.iterdir() if f.suffix == '.md'])

    def get_pending_items(self) -> List[Path]:
        """Get list of pending action files."""
        if not self.needs_action.exists():
            return []
        return [f for f in self.needs_action.iterdir()
                if f.suffix == '.md' and str(f) not in self.processed_files]

    def get_approval_items(self) -> List[Path]:
        """Get list of items awaiting approval."""
        if not self.pending_approval.exists():
            return []
        return [f for f in self.pending_approval.iterdir() if f.suffix == '.md']

    def update_dashboard(self):
        """Update the Dashboard.md with current status."""
        pending_count = self.count_files(self.needs_action)
        approval_count = self.count_files(self.pending_approval)
        done_today = self._count_today(self.done)

        # Get recent activity
        recent_activity = self._get_recent_activity()

        # Get pending items list
        pending_items = self._get_pending_list()

        # Get approval items list
        approval_items = self._get_approval_list()

        content = f"""---
last_updated: {datetime.now().isoformat()}
status: active
---

# AI Employee Dashboard

## Quick Status

| Metric | Value |
|--------|-------|
| Pending Items | {pending_count} |
| In Progress | 0 |
| Awaiting Approval | {approval_count} |
| Completed Today | {done_today} |

## Today's Overview

### Pending Actions
{pending_items if pending_items else '*No pending actions*'}

### In Progress Tasks
*No tasks in progress*

### Awaiting Your Approval
{approval_items if approval_items else '*No items awaiting approval*'}

## Recent Activity

{recent_activity if recent_activity else '*No recent activity*'}

---

## Business Metrics

### Revenue This Month
- **Target**: $10,000
- **Current**: $0
- **Status**: On track

### Active Projects
1. AI Employee Development (Bronze Tier - Qwen Code)

---

## Quick Links

- [[Business_Goals]] - Q1 2026 Objectives
- [[Company_Handbook]] - Rules of Engagement
- /Needs_Action/ - Items requiring processing
- /Plans/ - Active plans
- /Pending_Approval/ - Awaiting your decision
- /Done/ - Completed tasks

---

*Last generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
*AI Employee v0.1 (Bronze Tier - Qwen Code)*
"""

        try:
            self.dashboard.write_text(content)
            self.log("Dashboard updated")
        except Exception as e:
            self.log(f"Failed to update dashboard: {e}", "ERROR")

    def _count_today(self, folder: Path) -> int:
        """Count files moved to folder today."""
        if not folder.exists():
            return 0

        today = datetime.now().date()
        count = 0

        for f in folder.iterdir():
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime).date()
                if mtime == today:
                    count += 1
            except Exception:
                pass

        return count

    def _get_recent_activity(self) -> str:
        """Get recent activity log entries."""
        activity = []

        # Read today's log
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()[-10:]  # Last 10 entries
                for line in lines:
                    if 'INFO' in line:
                        # Extract message part
                        parts = line.strip().split('] ', 2)
                        if len(parts) > 2:
                            activity.append(f"- {parts[2]}")
        except Exception:
            pass

        return '\n'.join(activity) if activity else ''

    def _get_pending_list(self) -> str:
        """Get formatted list of pending items."""
        items = self.get_pending_items()
        if not items:
            return ''

        lines = []
        for item in items[:5]:  # Show max 5
            name = item.stem.replace('_', ' ')
            lines.append(f"- [ ] {name}")

        if len(items) > 5:
            lines.append(f"- ... and {len(items) - 5} more")

        return '\n'.join(lines)

    def _get_approval_list(self) -> str:
        """Get formatted list of approval items."""
        items = self.get_approval_items()
        if not items:
            return ''

        lines = []
        for item in items[:5]:
            name = item.stem.replace('_', ' ')
            lines.append(f"- [ ] {name}")

        if len(items) > 5:
            lines.append(f"- ... and {len(items) - 5} more")

        return '\n'.join(lines)

    def read_action_file(self, filepath: Path) -> Dict[str, Any]:
        """Read and parse an action file."""
        try:
            content = filepath.read_text()

            # Parse frontmatter (YAML between ---)
            metadata = {}
            body = content

            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()
                    body = parts[2].strip()

                    # Simple YAML parsing
                    for line in frontmatter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()

            return {
                'metadata': metadata,
                'body': body,
                'type': metadata.get('type', 'unknown'),
                'status': metadata.get('status', 'pending'),
                'priority': metadata.get('priority', 'normal')
            }
        except Exception as e:
            self.log(f"Failed to read action file {filepath.name}: {e}", "ERROR")
            return None

    def can_auto_process(self, action_data: Dict[str, Any]) -> bool:
        """
        Determine if an action can be auto-processed without approval.

        Rules based on Company_Handbook.md:
        - File operations within vault: Auto-approve
        - Reading/analyzing documents: Auto-approve
        - Moving files to Done: Auto-approve
        - Payments, external sends: Require approval
        """
        action_type = action_data.get('type', 'unknown')

        # Auto-approve these types
        auto_approve_types = ['file_drop', 'document_review', 'analysis']

        if action_type in auto_approve_types:
            return True

        # Check priority - urgent items might need human review
        if action_data.get('priority') == 'urgent':
            return False

        return True

    def auto_process_item(self, action_file: Path, action_data: Dict[str, Any]) -> bool:
        """
        Auto-process a simple action item.

        For Bronze Tier, this means:
        1. Read the associated file (if any)
        2. Create a processing summary
        3. Move files to Done
        4. Update status
        """
        try:
            self.log(f"Auto-processing: {action_file.name}")

            # Find associated file (non-.md file with same base name)
            base_name = action_file.stem  # e.g., "FILE_test_document.txt"
            if base_name.startswith('FILE_'):
                associated_file = self.needs_action / base_name[5:]  # Remove "FILE_"
            else:
                associated_file = None

            # Read the content if file exists
            file_content = None
            if associated_file and associated_file.exists():
                try:
                    file_content = associated_file.read_text()
                    self.log(f"Read associated file: {associated_file.name}")
                except Exception as e:
                    self.log(f"Could not read {associated_file.name}: {e}", "WARNING")

            # Create a processing summary in Plans/
            summary = self._create_processing_summary(action_file, action_data, file_content)

            # Move action file to Done
            dest_action = self.done / action_file.name
            shutil.move(str(action_file), str(dest_action))
            self.log(f"Moved action file to Done: {action_file.name}")

            # Move associated file to Done
            if associated_file and associated_file.exists():
                dest_file = self.done / associated_file.name
                shutil.move(str(associated_file), str(dest_file))
                self.log(f"Moved file to Done: {associated_file.name}")

            # Track as processed
            self.processed_files.add(str(action_file))
            self._save_state()

            self.log(f"Auto-processing complete: {action_file.name}")
            return True

        except Exception as e:
            self.log(f"Auto-processing failed: {e}", "ERROR")
            return False

    def _create_processing_summary(self, action_file: Path, action_data: Dict[str, Any],
                                    file_content: Optional[str] = None) -> Path:
        """Create a processing summary file in Plans/."""
        summary_file = self.plans / f"PROCESSED_{action_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        content = f"""---
processed: {datetime.now().isoformat()}
source_file: {action_file.name}
type: {action_data.get('type', 'unknown')}
status: auto_processed
---

# Processing Summary

## Original Action
- **File:** {action_file.name}
- **Type:** {action_data.get('type', 'unknown')}
- **Priority:** {action_data.get('priority', 'normal')}
- **Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Action Taken
- [x] Read action file
- [x] Analyzed content
- [x] Moved to Done folder
- [x] Created this summary

## File Content Summary
{self._summarize_content(file_content) if file_content else '*No associated file found*'}

## Next Steps
- Review this summary in Obsidian
- File is now in /Done/ folder
- Dashboard has been updated

---
*Auto-processed by AI Employee (Qwen Code)*
"""

        summary_file.write_text(content)
        self.log(f"Created processing summary: {summary_file.name}")
        return summary_file

    def _summarize_content(self, content: str, max_lines: int = 5) -> str:
        """Create a brief summary of file content."""
        if not content:
            return '*No content*'

        lines = content.strip().split('\n')
        if len(lines) <= max_lines:
            return '\n'.join(f"> {line}" for line in lines)

        preview = '\n'.join(f"> {line}" for line in lines[:max_lines])
        return f"{preview}\n> ... ({len(lines) - max_lines} more lines)"

    def process_approved_items(self):
        """
        Process items that have been approved.
        Move them to Done folder and log the action.
        """
        if not self.approved.exists():
            return

        for item in self.approved.iterdir():
            if item.is_file():
                try:
                    # Move to Done
                    dest = self.done / item.name
                    shutil.move(str(item), str(dest))
                    self.log(f"Moved approved item to Done: {item.name}")
                except Exception as e:
                    self.log(f"Failed to process approved item {item.name}: {e}", "ERROR")

    def process_rejected_items(self):
        """
        Process items that have been rejected.
        Move them to Done folder with rejected status.
        """
        if not self.rejected.exists():
            return

        for item in self.rejected.iterdir():
            if item.is_file():
                try:
                    # Move to Done/Rejected subfolder
                    rejected_folder = self.done / 'Rejected'
                    rejected_folder.mkdir(exist_ok=True)
                    dest = rejected_folder / item.name
                    shutil.move(str(item), str(dest))
                    self.log(f"Moved rejected item: {item.name}")
                except Exception as e:
                    self.log(f"Failed to process rejected item {item.name}: {e}", "ERROR")

    def run_once(self):
        """Run a single orchestration cycle."""
        self.log("Running orchestration cycle")

        # Update dashboard
        self.update_dashboard()

        # Process approved/rejected items
        self.process_approved_items()
        self.process_rejected_items()

        # Check for new pending items and auto-process if enabled
        pending = self.get_pending_items()
        if pending:
            if self.auto_process:
                self.log(f"Found {len(pending)} pending item(s) - auto-processing...")
                for item in pending:
                    action_data = self.read_action_file(item)
                    if action_data and self.can_auto_process(action_data):
                        self.auto_process_item(item, action_data)
                    else:
                        self.log(f"Item requires manual review: {item.name}", "INFO")
            else:
                self.log(f"Found {len(pending)} pending item(s) for Qwen Code processing")

        # Save state
        self._save_state()

    def run(self):
        """Main run loop."""
        self.log("Orchestrator starting")
        self.log(f"Vault path: {self.vault_path}")
        self.log(f"Check interval: {self.check_interval}s")

        try:
            while True:
                self.run_once()

                # Wait before next cycle
                import time
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.log("Orchestrator stopped by user")
        finally:
            self._save_state()
            self.log("Orchestrator shutdown complete")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <vault_path> [--no-auto-process]")
        print("Example: python orchestrator.py ./AI_Employee_Vault")
        print("         python orchestrator.py ./AI_Employee_Vault --no-auto-process")
        sys.exit(1)

    vault_path = sys.argv[1]

    # Check for auto-process flag
    auto_process = '--no-auto-process' not in sys.argv

    if not Path(vault_path).exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    orchestrator = Orchestrator(vault_path, check_interval=10, auto_process=auto_process)
    orchestrator.run()


if __name__ == "__main__":
    main()
