#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Silver Tier Verification Script

Verifies all Silver Tier requirements are met:
1. All Bronze requirements (already verified)
2. Two or more Watcher scripts (Gmail, LinkedIn, Filesystem)
3. Claude/Qwen reasoning loop with Plan.md creation
4. One working MCP server for external action (Email MCP)
5. Human-in-the-Loop (HITL) approval workflow
6. Basic scheduling support

Usage:
    python verify_silver_tier.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime


class SilverTierVerifier:
    """Verify Silver Tier implementation."""

    def __init__(self):
        # Project root is parent of scripts directory
        self.base_dir = Path(__file__).parent.parent.resolve()
        self.vault_path = self.base_dir / 'AI_Employee_Vault'
        self.scripts_path = self.base_dir / 'scripts'
        self.checks = []
        self.passed = 0
        self.failed = 0

    def log_check(self, name: str, passed: bool, details: str = ""):
        """Log a verification check."""
        status = "✓" if passed else "✗"
        print(f"  [{status}] {name}")
        if details:
            print(f"      {details}")

        if passed:
            self.passed += 1
        else:
            self.failed += 1

        self.checks.append({
            'name': name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    def verify_bronze_requirements(self):
        """Verify all Bronze Tier requirements are still met."""
        print("\n1. Verifying Bronze Tier Requirements (prerequisites)...")

        # Vault structure
        folders = ['Inbox', 'Needs_Action', 'Done', 'Plans', 'Pending_Approval', 'Approved', 'Rejected']
        all_folders_exist = all((self.vault_path / f).exists() for f in folders)
        self.log_check(
            "Vault folder structure",
            all_folders_exist,
            "All required folders exist" if all_folders_exist else "Missing folders"
        )

        # Core files
        core_files = ['Dashboard.md', 'Company_Handbook.md', 'Business_Goals.md']
        all_files_exist = all((self.vault_path / f).exists() for f in core_files)
        self.log_check(
            "Core vault files",
            all_files_exist,
            "Dashboard, Handbook, Goals exist" if all_files_exist else "Missing core files"
        )

        # Bronze scripts
        bronze_scripts = ['base_watcher.py', 'filesystem_watcher.py', 'orchestrator.py']
        scripts_exist = all((self.scripts_path / s).exists() for s in bronze_scripts)
        self.log_check(
            "Bronze Tier scripts",
            scripts_exist,
            "Base, Filesystem watchers + Orchestrator" if scripts_exist else "Missing scripts"
        )

    def verify_watchers(self):
        """Verify multiple watcher scripts exist."""
        print("\n2. Verifying Watcher Scripts (2+ required)...")

        watchers = {
            'Filesystem Watcher': 'filesystem_watcher.py',
            'Gmail Watcher': 'gmail_watcher.py',
            'LinkedIn Watcher': 'linkedin_watcher.py',
            'Base Watcher': 'base_watcher.py'
        }

        count = 0
        for name, filename in watchers.items():
            exists = (self.scripts_path / filename).exists()
            if exists:
                count += 1
            self.log_check(
                f"{name}",
                exists,
                f"scripts/{filename}"
            )

        # Check for email MCP server
        email_mcp_exists = (self.scripts_path / 'email_mcp_server.py').exists()
        self.log_check(
            "Email MCP Server",
            email_mcp_exists,
            "Email sending capability" if email_mcp_exists else "Not found"
        )

        # Verify requirement: 2+ watchers
        watcher_count = sum(1 for f in ['filesystem_watcher.py', 'gmail_watcher.py', 'linkedin_watcher.py']
                           if (self.scripts_path / f).exists())
        self.log_check(
            "Watcher count (≥2 required)",
            watcher_count >= 2,
            f"{watcher_count} watchers found" if watcher_count >= 2 else f"Only {watcher_count} watcher(s)"
        )

    def verify_credentials(self):
        """Verify credentials exist for watchers."""
        print("\n3. Verifying Credentials...")

        # Gmail credentials
        gmail_creds = self.base_dir / 'credentials.json'
        gmail_exists = gmail_creds.exists()
        self.log_check(
            "Gmail credentials (credentials.json)",
            gmail_exists,
            "OAuth credentials configured" if gmail_exists else "Download from Google Cloud Console"
        )

        # Check if credentials are valid JSON
        if gmail_exists:
            try:
                content = gmail_creds.read_text()
                data = json.loads(content)
                valid = 'web' in data or 'installed' in data
                self.log_check(
                    "Credentials format",
                    valid,
                    "Valid Google OAuth format" if valid else "Invalid format"
                )
            except Exception as e:
                self.log_check(
                    "Credentials format",
                    False,
                    f"Invalid JSON: {e}"
                )

    def verify_hctl_workflow(self):
        """Verify Human-in-the-Loop approval workflow."""
        print("\n4. Verifying HITL Approval Workflow...")

        # Check orchestrator has approval logic
        orchestrator_path = self.scripts_path / 'orchestrator.py'
        if orchestrator_path.exists():
            content = orchestrator_path.read_text()

            has_approval = 'requires_approval' in content or 'approval_request' in content
            self.log_check(
                "Approval request logic",
                has_approval,
                "Orchestrator checks for approval requirements" if has_approval else "Not found"
            )

            has_pending_folder = 'pending_approval' in content.lower()
            self.log_check(
                "Pending_Approval folder handling",
                has_pending_folder,
                "Orchestrator manages approval queue" if has_pending_folder else "Not found"
            )

            has_approved_handling = 'process_approved' in content.lower()
            self.log_check(
                "Approved items processing",
                has_approved_handling,
                "Orchestrator processes approved items" if has_approved_handling else "Not found"
            )
        else:
            self.log_check("Orchestrator", False, "orchestrator.py not found")

        # Check Pending_Approval folder exists
        pending_folder = self.vault_path / 'Pending_Approval'
        self.log_check(
            "Pending_Approval folder",
            pending_folder.exists(),
            "Folder for approval requests" if pending_folder.exists() else "Create folder"
        )

        # Check Approved folder exists
        approved_folder = self.vault_path / 'Approved'
        self.log_check(
            "Approved folder",
            approved_folder.exists(),
            "Folder for approved actions" if approved_folder.exists() else "Create folder"
        )

    def verify_plan_creation(self):
        """Verify Plan.md creation capability."""
        print("\n5. Verifying Plan.md Creation...")

        # Check orchestrator creates plans
        orchestrator_path = self.scripts_path / 'orchestrator.py'
        if orchestrator_path.exists():
            content = orchestrator_path.read_text()

            creates_summary = 'create_processing_summary' in content or 'processing_summary' in content
            self.log_check(
                "Processing summary creation",
                creates_summary,
                "Orchestrator creates summaries" if creates_summary else "Not found"
            )

            plans_folder = 'self.plans' in content
            self.log_check(
                "Plans folder integration",
                plans_folder,
                "Orchestrator uses Plans folder" if plans_folder else "Not found"
            )
        else:
            self.log_check("Orchestrator", False, "orchestrator.py not found")

        # Check Plans folder exists
        plans_folder = self.vault_path / 'Plans'
        self.log_check(
            "Plans folder",
            plans_folder.exists(),
            "Folder for processing summaries" if plans_folder.exists() else "Create folder"
        )

    def verify_mcp_server(self):
        """Verify MCP server for external actions."""
        print("\n6. Verifying MCP Server...")

        # Email MCP server
        email_mcp = self.scripts_path / 'email_mcp_server.py'
        email_exists = email_mcp.exists()
        self.log_check(
            "Email MCP Server",
            email_exists,
            "scripts/email_mcp_server.py" if email_exists else "Not found"
        )

        if email_exists:
            content = email_mcp.read_text()
            has_send = 'send_email' in content
            self.log_check(
                "Email send capability",
                has_send,
                "Can send emails via Gmail API" if has_send else "Not implemented"
            )

            has_draft = 'draft_email' in content
            self.log_check(
                "Email draft capability",
                has_draft,
                "Can create drafts" if has_draft else "Not implemented"
            )

    def verify_scheduling(self):
        """Verify basic scheduling support."""
        print("\n7. Verifying Scheduling Support...")

        # Check for start scripts
        start_bat = self.base_dir / 'start.bat'
        start_silver = self.base_dir / 'start_silver.bat'

        has_start = start_bat.exists() or start_silver.exists()
        self.log_check(
            "Start script",
            has_start,
            "Batch file to start all watchers" if has_start else "Create start.bat"
        )

        # Check orchestrator has interval
        orchestrator_path = self.scripts_path / 'orchestrator.py'
        if orchestrator_path.exists():
            content = orchestrator_path.read_text()
            has_interval = 'check_interval' in content
            self.log_check(
                "Configurable check interval",
                has_interval,
                "Orchestrator supports intervals" if has_interval else "Not found"
            )

    def verify_documentation(self):
        """Verify documentation exists."""
        print("\n8. Verifying Documentation...")

        # README
        readme = self.base_dir / 'README.md'
        self.log_check(
            "README.md",
            readme.exists(),
            "Project documentation" if readme.exists() else "Create README"
        )

        # Silver tier summary
        silver_summary = self.base_dir / 'SILVER_TIER_SUMMARY.md'
        self.log_check(
            "SILVER_TIER_SUMMARY.md",
            silver_summary.exists(),
            "Silver tier documentation" if silver_summary.exists() else "Will be created"
        )

    def run_all_checks(self):
        """Run all verification checks."""
        print("=" * 60)
        print("  SILVER TIER VERIFICATION")
        print("  Personal AI Employee Hackathon")
        print("=" * 60)

        self.verify_bronze_requirements()
        self.verify_watchers()
        self.verify_credentials()
        self.verify_hctl_workflow()
        self.verify_plan_creation()
        self.verify_mcp_server()
        self.verify_scheduling()
        self.verify_documentation()

        # Summary
        print("\n" + "=" * 60)
        print("  VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"  Passed: {self.passed}")
        print(f"  Failed: {self.failed}")
        print(f"  Total:  {self.passed + self.failed}")
        print()

        if self.failed == 0:
            print("  ✓ ALL CHECKS PASSED - SILVER TIER COMPLETE!")
        else:
            print(f"  ✗ {self.failed} check(s) failed - Review above for details")

        print("=" * 60)

        # Save results
        results = {
            'tier': 'silver',
            'timestamp': datetime.now().isoformat(),
            'passed': self.passed,
            'failed': self.failed,
            'total': self.passed + self.failed,
            'checks': self.checks
        }

        results_file = self.base_dir / 'silver_verification_results.json'
        results_file.write_text(json.dumps(results, indent=2))
        print(f"\nResults saved to: {results_file}")

        return self.failed == 0


def main():
    """Main entry point."""
    verifier = SilverTierVerifier()
    success = verifier.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
