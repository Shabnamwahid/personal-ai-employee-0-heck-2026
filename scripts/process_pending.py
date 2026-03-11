#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test - process all pending items now.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import Orchestrator

if __name__ == "__main__":
    vault_path = Path(__file__).parent.parent / "AI_Employee_Vault"
    
    print(f"Processing pending items in: {vault_path}")
    orch = Orchestrator(vault_path, check_interval=10, auto_process=True)
    orch.run_once()
    print("\nProcessing complete! Check AI_Employee_Vault/Done/ for results.")
