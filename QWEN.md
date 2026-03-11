# Personal AI Employee Hackathon Project

## Project Overview

This repository contains a hackathon project for building a **"Digital FTE" (Full-Time Equivalent)** — an autonomous AI employee that manages personal and business affairs 24/7. The system uses a local-first, agent-driven architecture with human-in-the-loop oversight.

**Tagline:** *Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.*

### Core Architecture

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Brain** | Claude Code | Reasoning engine for decision-making |
| **Memory/GUI** | Obsidian (Markdown vault) | Dashboard and long-term memory |
| **Senses** | Python Watcher scripts | Monitor Gmail, WhatsApp, filesystem |
| **Hands** | MCP Servers | External actions (email, browser, payments) |
| **Persistence** | Ralph Wiggum Loop | Keep agent working until task complete |

### Key Features

- **Autonomous Business Audit**: "Monday Morning CEO Briefing" generated weekly
- **Watcher Pattern**: Lightweight Python scripts monitor inputs and create actionable files
- **Human-in-the-Loop**: Sensitive actions require approval before execution
- **Local-First**: All data stored locally in Obsidian vault for privacy

---

## Directory Structure

```
personal-ai-employee-0-heck-2026/
├── Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md  # Main blueprint
├── README.md                      # Project identifier
├── skills-lock.json               # Installed skill versions
├── .qwen/
│   └── skills/
│       └── browsing-with-playwright/  # Browser automation skill
│           ├── SKILL.md           # Skill documentation
│           ├── references/
│           │   └── playwright-tools.md  # MCP tool reference
│           └── scripts/
│               ├── mcp-client.py  # Universal MCP client
│               ├── start-server.sh    # Start Playwright server
│               ├── stop-server.sh     # Stop Playwright server
│               └── verify.py      # Server verification
└── .git/
```

---

## Key Files

| File | Description |
|------|-------------|
| `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md` | Comprehensive architectural blueprint (1201 lines) with tiered deliverables (Bronze/Silver/Gold/Platinum) |
| `skills-lock.json` | Tracks installed Qwen skills and their versions |
| `.qwen/skills/browsing-with-playwright/SKILL.md` | Browser automation skill documentation |
| `.qwen/skills/browsing-with-playwright/scripts/mcp-client.py` | Universal MCP client supporting HTTP and stdio transports |

---

## Building and Running

### Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Claude Code | Active subscription | Primary reasoning engine |
| Obsidian | v1.10.6+ | Knowledge base & dashboard |
| Python | 3.13+ | Sentinel scripts & orchestration |
| Node.js | v24+ LTS | MCP servers & automation |
| GitHub Desktop | Latest | Version control |

### Hardware Requirements

- **Minimum**: 8GB RAM, 4-core CPU, 20GB free disk space
- **Recommended**: 16GB RAM, 8-core CPU, SSD storage
- **For always-on**: Dedicated mini-PC or cloud VM

### Setup Checklist

```bash
# 1. Create Obsidian vault
mkdir AI_Employee_Vault
cd AI_Employee_Vault
mkdir Inbox Needs_Action Done Plans Pending_Approved

# 2. Verify Claude Code
claude --version

# 3. Install Playwright browsers (for browsing skill)
npx playwright install

# 4. Start Playwright MCP server
bash .qwen/skills/browsing-with-playwright/scripts/start-server.sh

# 5. Verify server
python3 .qwen/skills/browsing-with-playwright/scripts/verify.py
```

### Running Browser Automation

```bash
# Navigate to URL
python3 scripts/mcp-client.py call -u http://localhost:8808 \
  -t browser_navigate -p '{"url": "https://example.com"}'

# Get page snapshot (accessibility tree)
python3 scripts/mcp-client.py call -u http://localhost:8808 \
  -t browser_snapshot -p '{}'

# Click element
python3 scripts/mcp-client.py call -u http://localhost:8808 \
  -t browser_click -p '{"element": "Submit", "ref": "e42"}'

# Stop server when done
bash scripts/stop-server.sh
```

### Watcher Pattern (Python)

All watchers follow this base pattern:

```python
from base_watcher import BaseWatcher

class GmailWatcher(BaseWatcher):
    def check_for_updates(self) -> list:
        # Return list of new items to process
        pass
    
    def create_action_file(self, item) -> Path:
        # Create .md file in Needs_Action folder
        pass
```

---

## Development Conventions

### Folder Structure (Obsidian Vault)

```
Vault/
├── Inbox/                 # Raw incoming items
├── Needs_Action/          # Items requiring processing
├── In_Progress/<agent>/   # Claimed by specific agent
├── Pending_Approval/      # Awaiting human approval
├── Approved/              # Approved actions (triggers execution)
├── Rejected/              # Rejected actions
├── Done/                  # Completed tasks
├── Plans/                 # Multi-step plans (Plan.md)
├── Briefings/             # CEO briefings
├── Accounting/            # Bank transactions
└── Business_Goals.md      # Q1 2026 objectives
```

### Action File Schema

```markdown
---
type: email
from: sender@example.com
subject: Invoice Request
received: 2026-01-07T10:30:00Z
priority: high
status: pending
---

## Email Content
{message snippet}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
```

### Approval Request Schema

```markdown
---
type: approval_request
action: payment
amount: 500.00
recipient: Client A
reason: Invoice #1234 payment
created: 2026-01-07T10:30:00Z
expires: 2026-01-08T10:30:00Z
status: pending
---

## Payment Details
- Amount: $500.00
- To: Client A (Bank: XXXX1234)
- Reference: Invoice #1234

## To Approve
Move this file to /Approved folder.
```

### Coding Style

- **Python**: Type hints required, ABC for base classes
- **Markdown**: YAML frontmatter for all action files
- **Error Handling**: Log errors, graceful degradation
- **Security**: Secrets never sync (`.env`, tokens, banking creds)

---

## Hackathon Tiers

| Tier | Time | Deliverables |
|------|------|--------------|
| **Bronze** | 8-12 hours | Obsidian dashboard, 1 watcher, Claude Code integration |
| **Silver** | 20-30 hours | 2+ watchers, MCP server, HITL workflow, scheduling |
| **Gold** | 40+ hours | Full integration, Odoo accounting, Ralph Wiggum loop |
| **Platinum** | 60+ hours | Cloud deployment, domain specialization, A2A upgrade |

---

## Available MCP Tools (Playwright)

The `browsing-with-playwright` skill provides 22 tools:

| Category | Tools |
|----------|-------|
| **Navigation** | `browser_navigate`, `browser_navigate_back`, `browser_tabs` |
| **Snapshot** | `browser_snapshot`, `browser_take_screenshot` |
| **Interaction** | `browser_click`, `browser_type`, `browser_fill_form`, `browser_hover`, `browser_drag` |
| **Forms** | `browser_select_option`, `browser_file_upload`, `browser_press_key` |
| **Advanced** | `browser_evaluate`, `browser_run_code`, `browser_wait_for` |
| **Utility** | `browser_close`, `browser_resize`, `browser_install`, `browser_console_messages`, `browser_network_requests`, `browser_handle_dialog` |

---

## Research Meetings

**Weekly**: Wednesday 10:00 PM PKT on Zoom  
**First Meeting**: January 7th, 2026

- **Zoom**: [Join Meeting](https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1)
- **Meeting ID**: 871 8870 7642
- **Passcode**: 744832
- **YouTube**: [Panaversity Channel](https://www.youtube.com/@panaversity)

---

## References

- [Claude Code Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Ralph Wiggum Stop Hook](https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum)
- [MCP Server Protocol](https://modelcontextprotocol.io/)
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)
