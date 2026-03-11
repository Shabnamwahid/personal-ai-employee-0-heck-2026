#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bronze Tier Verification Script

Verifies that all Bronze Tier components are properly set up and functional.

Usage:
    python verify_bronze_tier.py
"""

import sys
from pathlib import Path


def check(condition: bool, message: str) -> bool:
    """Print check result and return condition."""
    status = "[OK]" if condition else "[FAIL]"
    print(f"  {status} {message}")
    return condition


def main():
    # Get project root (parent of scripts directory)
    base_path = Path(__file__).parent.parent.resolve()
    vault_path = base_path / "AI_Employee_Vault"
    scripts_path = base_path / "scripts"
    skills_path = base_path / "skills"
    
    print("\n=== Personal AI Employee - Bronze Tier Verification ===\n")
    
    all_passed = True
    
    # 1. Check Vault Structure
    print("1. Vault Structure:")
    all_passed &= check(vault_path.exists(), "AI_Employee_Vault exists")
    all_passed &= check((vault_path / "Inbox").exists(), "Inbox/ folder exists")
    all_passed &= check((vault_path / "Needs_Action").exists(), "Needs_Action/ folder exists")
    all_passed &= check((vault_path / "Done").exists(), "Done/ folder exists")
    all_passed &= check((vault_path / "Plans").exists(), "Plans/ folder exists")
    all_passed &= check((vault_path / "Pending_Approval").exists(), "Pending_Approval/ folder exists")
    all_passed &= check((vault_path / "Approved").exists(), "Approved/ folder exists")
    all_passed &= check((vault_path / "Rejected").exists(), "Rejected/ folder exists")
    all_passed &= check((vault_path / "Logs").exists(), "Logs/ folder exists")
    print()
    
    # 2. Check Core Files
    print("2. Core Files:")
    all_passed &= check((vault_path / "Dashboard.md").exists(), "Dashboard.md exists")
    all_passed &= check((vault_path / "Company_Handbook.md").exists(), "Company_Handbook.md exists")
    all_passed &= check((vault_path / "Business_Goals.md").exists(), "Business_Goals.md exists")
    print()
    
    # 3. Check Scripts
    print("3. Python Scripts:")
    all_passed &= check((scripts_path / "base_watcher.py").exists(), "base_watcher.py exists")
    all_passed &= check((scripts_path / "filesystem_watcher.py").exists(), "filesystem_watcher.py exists")
    all_passed &= check((scripts_path / "orchestrator.py").exists(), "orchestrator.py exists")
    
    # Verify Python syntax
    import py_compile
    try:
        py_compile.compile(scripts_path / "base_watcher.py", doraise=True)
        all_passed &= check(True, "base_watcher.py syntax valid")
    except py_compile.PyCompileError:
        all_passed &= check(False, "base_watcher.py syntax valid")
    
    try:
        py_compile.compile(scripts_path / "filesystem_watcher.py", doraise=True)
        all_passed &= check(True, "filesystem_watcher.py syntax valid")
    except py_compile.PyCompileError:
        all_passed &= check(False, "filesystem_watcher.py syntax valid")
    
    try:
        py_compile.compile(scripts_path / "orchestrator.py", doraise=True)
        all_passed &= check(True, "orchestrator.py syntax valid")
    except py_compile.PyCompileError:
        all_passed &= check(False, "orchestrator.py syntax valid")
    print()
    
    # 4. Check Agent Skills
    print("4. Agent Skills:")
    all_passed &= check((skills_path / "process-files").exists(), "process-files skill folder exists")
    all_passed &= check((skills_path / "process-files" / "SKILL.md").exists(), "process-files SKILL.md exists")
    print()
    
    # 5. Check Documentation
    print("5. Documentation:")
    all_passed &= check((base_path / "README.md").exists(), "README.md exists")
    print()
    
    # 6. Check Test File
    print("6. Test Files:")
    test_file = vault_path / "Inbox" / "test_document.txt"
    all_passed &= check(test_file.exists(), "test_document.txt in Inbox/")
    print()
    
    # Summary
    print("=" * 60)
    if all_passed:
        print("[OK] All Bronze Tier checks passed!")
        print("\nNext steps:")
        print("  1. Start the watcher: python scripts/filesystem_watcher.py AI_Employee_Vault")
        print("  2. Start the orchestrator: python scripts/orchestrator.py AI_Employee_Vault")
        print("  3. Use Claude Code to process files in Needs_Action/")
        print("  4. Open Dashboard.md in Obsidian to monitor status")
    else:
        print("[FAIL] Some checks failed. Please review the output above.")
        sys.exit(1)
    
    print()


if __name__ == "__main__":
    main()
