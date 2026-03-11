#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test script - runs orchestrator once and exits.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import Orchestrator

if __name__ == "__main__":
    if len(sys.argv) < 2:
        vault_path = Path(__file__).parent.parent / "AI_Employee_Vault"
    else:
        vault_path = sys.argv[1]
    
    print(f"Running orchestrator once for: {vault_path}")
    orch = Orchestrator(vault_path, check_interval=10)
    orch.run_once()
    print("Orchestrator cycle complete!")
