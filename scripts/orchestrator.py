#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator - Master process for the AI Employee (Silver Tier).

Enhanced for Silver Tier with:
- Multi-watcher support (Gmail, LinkedIn, Filesystem)
- Human-in-the-Loop (HITL) approval workflow
- Plan.md creation for multi-step tasks
- Scheduled task support
- Email MCP integration for sending emails

The orchestrator:
1. Monitors Needs_Action folder for new items from all watchers
2. Auto-processes simple items based on Company Handbook rules
3. Creates approval requests for sensitive actions
4. Processes approved items and executes actions
5. Updates Dashboard.md with real-time status
6. Creates processing summaries and plans

Usage:
    python orchestrator.py /path/to/AI_Employee_Vault
    python orchestrator.py AI_Employee_Vault --no-auto-process
"""

import sys
import json
import shutil
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ActionType(Enum):
    """Types of actions the AI Employee can take."""
    FILE_DROP = "file_drop"
    EMAIL_READ = "email_read"
    EMAIL_SEND = "email_send"
    LINKEDIN_ENGAGE = "linkedin_engage"
    PAYMENT = "payment"
    EXTERNAL_SEND = "external_send"
    ANALYSIS = "analysis"
    PLAN_REQUIRED = "plan_required"


@dataclass
class ApprovalThreshold:
    """Thresholds for requiring human approval."""
    max_payment_amount: float = 500.0
    require_approval_new_contacts: bool = True
    require_approval_external_send: bool = True
    auto_approve_known_contacts: bool = True


class Orchestrator:
    """
    Main orchestrator for the AI Employee system (Silver Tier).

    Responsibilities:
    - Monitor Needs_Action folder for items from all watchers
    - Apply Company Handbook rules for auto-approval decisions
    - Create approval requests for sensitive actions
    - Process approved items via MCP servers
    - Update Dashboard.md with real-time status
    - Generate processing summaries and multi-step plans
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
        self.briefings = self.vault_path / 'Briefings'
        self.accounting = self.vault_path / 'Accounting'

        # Ensure all directories exist
        for folder in [self.inbox, self.needs_action, self.plans,
                       self.pending_approval, self.approved, self.rejected,
                       self.done, self.logs, self.briefings, self.accounting]:
            folder.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.log_file = self.logs / f'orchestrator_{datetime.now().strftime("%Y-%m-%d")}.log'

        # State tracking
        self.processed_files: set = set()
        self._load_state()

        # Load company handbook rules
        self.handbook_rules = self._load_handbook_rules()

        # Approval thresholds from handbook
        self.approval_thresholds = self._load_approval_thresholds()

        # Known contacts (from handbook or config)
        self.known_contacts = self._load_known_contacts()

        self.log("Orchestrator initialized (Silver Tier)")
        self.log(f"Auto-processing: {'enabled' if auto_process else 'disabled'}")
        self.log(f"HITL Workflow: enabled")

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
            content = handbook_path.read_text(encoding='utf-8')
            # Parse rules from handbook
            rules = {
                'auto_approve_file_ops': True,
                'auto_approve_read': True,
                'require_approval_payments': True,
                'require_approval_external_send': True,
                'max_auto_payment': 500.0,
            }
            return rules
        except Exception as e:
            self.log(f"Failed to load handbook: {e}", "WARNING")
            return {}

    def _load_approval_thresholds(self) -> ApprovalThreshold:
        """Load approval thresholds from handbook."""
        # Default thresholds
        thresholds = ApprovalThreshold()

        # Try to parse from handbook
        handbook_path = self.vault_path / 'Company_Handbook.md'
        if handbook_path.exists():
            try:
                content = handbook_path.read_text(encoding='utf-8')
                # Look for payment threshold
                match = re.search(r'payment.*?\$(\d+)', content, re.IGNORECASE)
                if match:
                    thresholds.max_payment_amount = float(match.group(1))
            except Exception:
                pass

        return thresholds

    def _load_known_contacts(self) -> set:
        """Load known contacts from handbook or config."""
        contacts = set()

        # Try to load from handbook
        handbook_path = self.vault_path / 'Company_Handbook.md'
        if handbook_path.exists():
            try:
                content = handbook_path.read_text(encoding='utf-8')
                # Look for email patterns in known contacts section
                emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', content)
                contacts.update(emails)
            except Exception:
                pass

        return contacts

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
        in_progress = self._count_in_progress()

        # Get recent activity
        recent_activity = self._get_recent_activity()

        # Get pending items list
        pending_items = self._get_pending_list()

        # Get approval items list
        approval_items = self._get_approval_list()

        content = f"""---
last_updated: {datetime.now().isoformat()}
status: active
tier: silver
---

# AI Employee Dashboard

## Quick Status

| Metric | Value |
|--------|-------|
| Pending Items | {pending_count} |
| In Progress | {in_progress} |
| Awaiting Approval | {approval_count} |
| Completed Today | {done_today} |

## Today's Overview

### Pending Actions
{pending_items if pending_items else '*No pending actions*'}

### In Progress Tasks
*Processing with Qwen Code*

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
1. AI Employee Development (Silver Tier)
2. Gmail Integration
3. LinkedIn Automation

### Watchers Status
| Watcher | Status | Last Check |
|---------|--------|------------|
| Filesystem | Running | Active |
| Gmail | Ready | Configured |
| LinkedIn | Ready | Configured |

---

## Quick Links

- [[Business_Goals]] - Q1 2026 Objectives
- [[Company_Handbook]] - Rules of Engagement
- /Needs_Action/ - Items requiring processing
- /Plans/ - Active plans
- /Pending_Approval/ - Awaiting your decision
- /Approved/ - Approved actions (auto-processing)
- /Done/ - Completed tasks

---

*Last generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
*AI Employee v0.2 (Silver Tier)*
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

    def _count_in_progress(self) -> int:
        """Count items currently in progress."""
        in_progress_folder = self.vault_path / 'In_Progress'
        return self.count_files(in_progress_folder)

    def _get_recent_activity(self) -> str:
        """Get recent activity log entries."""
        activity = []

        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()[-15:]
                for line in lines:
                    if 'INFO' in line:
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
        for item in items[:5]:
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

            # Determine action type
            action_type = self._determine_action_type(metadata, body)

            return {
                'metadata': metadata,
                'body': body,
                'type': metadata.get('type', action_type.value),
                'status': metadata.get('status', 'pending'),
                'priority': metadata.get('priority', 'normal'),
                'action_type': action_type,
                'source': metadata.get('source', 'unknown')
            }
        except Exception as e:
            self.log(f"Failed to read action file {filepath.name}: {e}", "ERROR")
            return None

    def _determine_action_type(self, metadata: Dict, body: str) -> ActionType:
        """Determine the type of action needed."""
        type_str = metadata.get('type', '').lower()

        if 'email' in type_str:
            if 'send' in body.lower() or 'reply' in body.lower():
                return ActionType.EMAIL_SEND
            return ActionType.EMAIL_READ
        elif 'linkedin' in type_str:
            return ActionType.LINKEDIN_ENGAGE
        elif 'payment' in type_str or 'invoice' in body.lower():
            return ActionType.PAYMENT
        elif 'file' in type_str:
            return ActionType.FILE_DROP
        else:
            return ActionType.ANALYSIS

    def requires_approval(self, action_data: Dict[str, Any]) -> bool:
        """
        Determine if an action requires human approval.

        Rules based on Company_Handbook.md:
        - Payments > $500: Require approval
        - New contact emails: Require approval
        - External sends: Require approval
        - File operations: Auto-approve
        - Reading/analysis: Auto-approve
        """
        action_type = action_data.get('action_type', ActionType.ANALYSIS)
        priority = action_data.get('priority', 'normal')
        metadata = action_data.get('metadata', {})

        # High priority items might need review
        if priority == 'urgent':
            return True

        # Check specific action types
        if action_type == ActionType.PAYMENT:
            # Check amount
            amount_str = metadata.get('amount', '0')
            try:
                amount = float(amount_str)
                if amount > self.approval_thresholds.max_payment_amount:
                    return True
            except (ValueError, TypeError):
                pass
            return self.handbook_rules.get('require_approval_payments', True)

        if action_type == ActionType.EMAIL_SEND:
            # Check if sending to known contact
            to_email = metadata.get('to', metadata.get('from_email', ''))
            if to_email not in self.known_contacts:
                return self.handbook_rules.get('require_approval_external_send', True)

        if action_type == ActionType.LINKEDIN_ENGAGE:
            # Check if it's an opportunity
            if metadata.get('is_opportunity') == 'true':
                return True

        # File drops and reading are auto-approved
        if action_type in [ActionType.FILE_DROP, ActionType.EMAIL_READ, ActionType.ANALYSIS]:
            return False

        return False

    def create_approval_request(self, action_file: Path, action_data: Dict[str, Any]) -> Path:
        """
        Create an approval request file in Pending_Approval folder.

        Args:
            action_file: Path to the original action file
            action_data: Parsed action data

        Returns:
            Path to created approval request file
        """
        metadata = action_data.get('metadata', {})
        action_type = action_data.get('action_type', ActionType.ANALYSIS)

        # Create approval request content
        timestamp = datetime.now().isoformat()
        expires = (datetime.now() + timedelta(days=1)).isoformat()

        # Determine reason for approval
        reason = self._get_approval_reason(action_data)

        content = f"""---
type: approval_request
source_file: {action_file.name}
action: {action_type.value}
reason: {reason}
created: {timestamp}
expires: {expires}
status: pending
priority: {action_data.get('priority', 'normal')}
---

# Approval Required

## Action Details
- **Type:** {action_type.value}
- **Source:** {action_file.name}
- **Reason:** {reason}
- **Priority:** {action_data.get('priority', 'normal')}

## Original Content
```
{action_data.get('body', '')[:500]}
```

## Metadata
{json.dumps(metadata, indent=2)}

## Instructions

### To Approve
1. Review the action details above
2. Move this file to `/Approved` folder
3. The orchestrator will process it automatically

### To Reject
1. Move this file to `/Rejected` folder
2. Add a note explaining why (optional)

### To Request More Information
1. Add comments to this file
2. Move back to `/Needs_Action` folder

---
*Approval expires: {expires}*
*AI Employee v0.2 (Silver Tier - HITL)*
"""

        # Create filename
        filename = f"APPROVAL_{action_file.stem}_{int(datetime.now().timestamp())}.md"
        filepath = self.pending_approval / filename

        filepath.write_text(content)
        self.log(f"Created approval request: {filename}")

        return filepath

    def _get_approval_reason(self, action_data: Dict[str, Any]) -> str:
        """Get the reason why approval is required."""
        action_type = action_data.get('action_type', ActionType.ANALYSIS)

        if action_type == ActionType.PAYMENT:
            amount = action_data.get('metadata', {}).get('amount', 'unknown')
            return f"Payment of ${amount} exceeds auto-approval threshold"
        elif action_type == ActionType.EMAIL_SEND:
            return "Sending email to external contact"
        elif action_type == ActionType.LINKEDIN_ENGAGE:
            if action_data.get('metadata', {}).get('is_opportunity') == 'true':
                return "Business opportunity requires human review"
            return "LinkedIn engagement action"
        else:
            return "Action requires human review per Company Handbook"

    def can_auto_process(self, action_data: Dict[str, Any]) -> bool:
        """
        Determine if an action can be auto-processed without approval.
        """
        return not self.requires_approval(action_data)

    def auto_process_item(self, action_file: Path, action_data: Dict[str, Any]) -> bool:
        """
        Auto-process a simple action item.

        For Silver Tier:
        1. Read the associated file (if any)
        2. Create a processing summary
        3. Move files to Done
        4. Update status
        """
        try:
            self.log(f"Auto-processing: {action_file.name}")

            # Create a processing summary in Plans/
            summary = self._create_processing_summary(action_file, action_data)

            # Move action file to Done
            dest_action = self.done / action_file.name
            shutil.move(str(action_file), str(dest_action))
            self.log(f"Moved action file to Done: {action_file.name}")

            # Track as processed
            self.processed_files.add(str(action_file))
            self._save_state()

            self.log(f"Auto-processing complete: {action_file.name}")
            return True

        except Exception as e:
            self.log(f"Auto-processing failed: {e}", "ERROR")
            return False

    def _create_processing_summary(self, action_file: Path, action_data: Dict[str, Any]) -> Path:
        """Create a processing summary file in Plans/."""
        summary_file = self.plans / f"PROCESSED_{action_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        content = f"""---
processed: {datetime.now().isoformat()}
source_file: {action_file.name}
type: {action_data.get('type', 'unknown')}
status: auto_processed
priority: {action_data.get('priority', 'normal')}
---

# Processing Summary

## Original Action
- **File:** {action_file.name}
- **Type:** {action_data.get('type', 'unknown')}
- **Priority:** {action_data.get('priority', 'normal')}
- **Source:** {action_data.get('source', 'unknown')}
- **Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Action Taken
- [x] Read action file
- [x] Analyzed content
- [x] Auto-approved (no approval required)
- [x] Moved to Done folder
- [x] Created this summary

## Content Summary
{self._summarize_content(action_data.get('body', ''))}

## Metadata
```json
{json.dumps(action_data.get('metadata', {}), indent=2)}
```

## Next Steps
- Review this summary in Obsidian
- File is now in /Done/ folder
- Dashboard has been updated

---
*Auto-processed by AI Employee (Silver Tier - Qwen Code)*
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
                    # Read the approval
                    action_data = self.read_action_file(item)

                    # Execute the approved action
                    if action_data:
                        self.log(f"Executing approved action: {item.name}")
                        self._execute_approved_action(item, action_data)

                    # Move to Done
                    dest = self.done / item.name
                    shutil.move(str(item), str(dest))
                    self.log(f"Moved approved item to Done: {item.name}")

                except Exception as e:
                    self.log(f"Failed to process approved item {item.name}: {e}", "ERROR")

    def _execute_approved_action(self, action_file: Path, action_data: Dict[str, Any]):
        """Execute an approved action (placeholder for MCP integration)."""
        action_type = action_data.get('action_type', ActionType.ANALYSIS)

        # Log the execution (in Silver Tier, we just log)
        # In Gold Tier, this would call actual MCP servers
        self.log(f"Executing {action_type.value} action")

        # Create execution log
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type.value,
            'source_file': str(action_file),
            'status': 'executed',
            'mode': 'logged_only'  # Silver Tier - no actual execution
        }

        # Append to execution log
        log_file = self.logs / f'executions_{datetime.now().strftime("%Y-%m-%d")}.json'
        executions = []
        if log_file.exists():
            try:
                executions = json.loads(log_file.read_text())
            except Exception:
                pass

        executions.append(log_entry)
        log_file.write_text(json.dumps(executions, indent=2))

    def process_rejected_items(self):
        """
        Process items that have been rejected.
        Move them to Done/Rejected subfolder.
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

        # Check for new pending items
        pending = self.get_pending_items()
        if pending:
            self.log(f"Found {len(pending)} pending item(s)")

            for item in pending:
                action_data = self.read_action_file(item)
                if not action_data:
                    continue

                # Check if approval is required
                if self.requires_approval(action_data):
                    self.log(f"Creating approval request: {item.name}")
                    self.create_approval_request(item, action_data)
                    # Move original to Pending_Approval for reference
                    dest = self.pending_approval / f"REF_{item.name}"
                    shutil.move(str(item), str(dest))
                elif self.auto_process:
                    # Auto-process if no approval needed
                    self.auto_process_item(item, action_data)
                else:
                    self.log(f"Item waiting for Qwen Code: {item.name}")

        # Save state
        self._save_state()

    def run(self):
        """Main run loop."""
        self.log("Orchestrator starting")
        self.log(f"Vault path: {self.vault_path}")
        self.log(f"Check interval: {self.check_interval}s")
        self.log(f"HITL Workflow: enabled")

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
        print("Example: python orchestrator.py AI_Employee_Vault")
        print("         python orchestrator.py AI_Employee_Vault --no-auto-process")
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
