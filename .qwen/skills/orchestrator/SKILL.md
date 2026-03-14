---
name: orchestrator
description: |
  Master orchestration process that coordinates all watchers, Claude Code,
  and MCP servers. Monitors folders, triggers processing, and manages workflows.
---

# Orchestrator

Central coordination process for the AI Employee system.

## Features

- Monitors Needs_Action folder for new items
- Triggers Claude Code processing
- Manages Human-in-the-Loop approvals
- Coordinates MCP server actions

## Configuration

```env
VAULT_ROOT=C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault
POLL_INTERVAL=30
MAX_CLAUDE_ITERATIONS=10
```

## Usage

```bash
# Run orchestrator
python scripts/orchestrator.py

# Run as daemon
pm2 start scripts/orchestrator.py --name orchestrator --interpreter python
```

## Workflow

1. Detect: Poll Needs_Action folder
2. Claim: Move file to In_Progress
3. Process: Trigger Claude Code
4. Approve: Request human approval if needed
5. Execute: Call MCP servers
6. Complete: Move to Done folder
