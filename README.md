# Personal AI Employee - Silver Tier

> **Tagline:** Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

**Silver Tier Implementation** - Gmail, LinkedIn, and Email MCP integration with HITL approval workflow.

---

## Quick Start (Silver Tier)

### Step 1: Verify Setup

```bash
cd C:\Users\abRahman\Desktop\personal-ai-employee-0-heck-2026
python scripts\verify_silver_tier.py
```

**Expected output:** `✓ ALL CHECKS PASSED - SILVER TIER COMPLETE!`

---

### Step 2: Start All Services

**Option A: Use Start Script (Recommended)**

Double-click `start_silver.bat` or run:
```bash
start_silver.bat
```

This opens 4 terminals automatically:
- Filesystem Watcher (5s interval)
- Gmail Watcher (2m interval)
- LinkedIn Watcher (5m interval)
- Orchestrator (10s interval)

**Option B: Manual Start (4 Terminals)**

**Terminal 1 - Filesystem Watcher:**
```bash
cd C:\Users\abRahman\Desktop\personal-ai-employee-0-heck-2026
python scripts\filesystem_watcher.py AI_Employee_Vault
```

**Terminal 2 - Gmail Watcher:**
```bash
cd C:\Users\abRahman\Desktop\personal-ai-employee-0-heck-2026
python scripts\gmail_watcher.py AI_Employee_Vault 120
```

**Terminal 3 - LinkedIn Watcher:**
```bash
cd C:\Users\abRahman\Desktop\personal-ai-employee-0-heck-2026
python scripts\linkedin_watcher.py AI_Employee_Vault 300
```

**Terminal 4 - Orchestrator:**
```bash
cd C:\Users\abRahman\Desktop\personal-ai-employee-0-heck-2026
python scripts\orchestrator.py AI_Employee_Vault
```

---

### Step 3: Test the System

**Test 1: File Drop**
```bash
echo "Test document for processing" > AI_Employee_Vault\Inbox\test.txt
```

**Test 2: Check Gmail** (First run requires OAuth)
```bash
python scripts\gmail_watcher.py AI_Employee_Vault 120
# Browser opens → Grant Gmail permissions → Token saved
```

**Test 3: Check LinkedIn** (First run requires login)
```bash
python scripts\linkedin_watcher.py AI_Employee_Vault 300
# First run: Set headless=False, login manually
# Session saved for subsequent runs
```

---

## Architecture (Silver Tier)

```
┌─────────────────────────────────────────────────────────────────┐
│                     SILVER TIER ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Gmail      │    │  LinkedIn    │    │  Filesystem  │
│   Watcher    │    │   Watcher    │    │   Watcher    │
│  (120s)      │    │   (300s)     │    │    (5s)      │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Needs_Action/  │
                  │  (Action Files) │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   Orchestrator  │
                  │   (Silver Tier) │
                  └────────┬────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
      ┌───────────┐ ┌───────────┐ ┌───────────┐
      │   Auto    │ │  Pending  │ │  Approved │
      │  Process  │ │ Approval  │ │  Folder   │
      └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
            │             │             │
            │             ▼             │
            │      ┌────────────┐      │
            │      │   Human    │      │
            │      │  Review    │      │
            │      └────────────┘      │
            │             │             │
            └─────────────┼─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  Done/      │
                   │  (Complete) │
                   └─────────────┘
```

---

## Features

### 1. Gmail Watcher ✉️

**What it does:**
- Monitors Gmail API for new unread emails
- Checks every 2 minutes
- Detects priority keywords (urgent, invoice, payment, etc.)
- Creates action files in `Needs_Action/`
- Tracks processed emails to avoid duplicates

**Priority Keywords:**
- urgent, asap, invoice, payment, due, overdue
- important, action required, immediate, deadline
- contract, agreement, legal, tax, irs
- interview, meeting, call, zoom, teams

**Setup:**
1. Download `credentials.json` from Google Cloud Console
2. Place in project root
3. First run opens browser for OAuth
4. Token saved as `token.json`

**Usage:**
```bash
python scripts\gmail_watcher.py AI_Employee_Vault 120
```

---

### 2. LinkedIn Watcher 💼

**What it does:**
- Monitors LinkedIn Web for notifications
- Checks every 5 minutes
- Detects connection requests, messages, job alerts
- Identifies business opportunities
- Uses Playwright for browser automation

**Notification Types:**
- Connection requests
- Direct messages
- Job alerts
- Post engagement (likes, comments)
- Business opportunities (hiring, projects, etc.)

**Setup:**
1. First run: Set `headless=False` in `linkedin_watcher.py`
2. Run watcher → Browser opens → Login to LinkedIn
3. Session saved to `linkedin_session/`
4. Subsequent runs: Automatic (headless)

**Usage:**
```bash
python scripts\linkedin_watcher.py AI_Employee_Vault 300
```

---

### 3. Email MCP Server 📧

**What it does:**
- Send emails via Gmail API
- Create drafts for review
- Search emails
- Mark as read/unread

**Usage:**
```bash
# Send email
python scripts\email_mcp_server.py ^
  --send-to recipient@example.com ^
  --subject "Hello" ^
  --body "Test message"

# Create draft
python scripts\email_mcp_server.py ^
  --draft ^
  --send-to recipient@example.com ^
  --subject "Hello" ^
  --body "Draft message"

# Search emails
python scripts\email_mcp_server.py ^
  --search "is:unread from:client@example.com"
```

---

### 4. HITL Approval Workflow ✅

**What requires approval:**
- Payments > $500 (configurable)
- Emails to unknown contacts
- LinkedIn business opportunities
- High-priority items

**Workflow:**
1. Watcher creates action file in `Needs_Action/`
2. Orchestrator evaluates against Company Handbook rules
3. If approval required → Creates request in `Pending_Approval/`
4. Human reviews and moves to `Approved/` or `Rejected/`
5. Orchestrator processes approved items automatically

**Approval Request Example:**
```markdown
---
type: approval_request
action: email_send
reason: Sending email to external contact
created: 2026-03-14T15:00:00Z
expires: 2026-03-15T15:00:00Z
status: pending
---

# Approval Required

## Instructions
- Move to `/Approved` to approve
- Move to `/Rejected` to decline
```

---

## Commands Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `python scripts\verify_silver_tier.py` | Verify Silver Tier setup | Before starting |
| `start_silver.bat` | Start all services | Daily use |
| `python scripts\gmail_watcher.py AI_Employee_Vault 120` | Gmail Watcher | Terminal 2 |
| `python scripts\linkedin_watcher.py AI_Employee_Vault 300` | LinkedIn Watcher | Terminal 3 |
| `python scripts\orchestrator.py AI_Employee_Vault` | Orchestrator | Terminal 4 |
| `python scripts\email_mcp_server.py --send-to ...` | Send email | Manual send |

---

## Monitoring

### Check Dashboard

Open in Obsidian:
```bash
start obsidian://open?vault=AI_Employee_Vault&file=Dashboard.md
```

Or manually:
1. Open Obsidian
2. Open folder as vault: `AI_Employee_Vault`
3. Open `Dashboard.md`

### Check Logs

```bash
# Orchestrator logs
notepad AI_Employee_Vault\Logs\orchestrator_2026-03-14.log

# Gmail Watcher logs
notepad AI_Employee_Vault\Logs\watcher_2026-03-14.log

# LinkedIn Watcher logs
notepad AI_Employee_Vault\Logs\watcher_2026-03-14.log
```

### Check Processed Items

```bash
# See what's been processed
dir AI_Employee_Vault\Done\

# See processing summaries
dir AI_Employee_Vault\Plans\

# See pending approvals
dir AI_Employee_Vault\Pending_Approval\
```

---

## Stopping the System

**If using start_silver.bat:**
- Close all 4 terminal windows

**Manual start:**
- Press `Ctrl+C` in each terminal

---

## Configuration

### Gmail OAuth Setup

1. **Go to Google Cloud Console:**
   https://console.cloud.google.com/

2. **Create/Select Project**

3. **Enable Gmail API**

4. **Create OAuth 2.0 Credentials:**
   - Application type: Desktop app
   - Download `credentials.json`

5. **Place in project root:**
   ```
   personal-ai-employee-0-heck-2026/
   └── credentials.json
   ```

6. **First Run Authorization:**
   ```bash
   python scripts\gmail_watcher.py AI_Employee_Vault 120
   # Browser opens → Grant permissions
   ```

### LinkedIn Session Setup

1. **First Run (Manual Login):**
   - Edit `linkedin_watcher.py`
   - Set `headless=False` (line ~85)
   - Run: `python scripts\linkedin_watcher.py AI_Employee_Vault 300`
   - Browser opens → Login to LinkedIn
   - Session saved to `linkedin_session/`

2. **Subsequent Runs:**
   - Set `headless=True` (default)
   - Runs automatically

### Approval Thresholds

Edit `Company_Handbook.md` to customize:

```markdown
## Approval Rules

- Payments over $500 require approval
- Emails to new contacts require approval
- LinkedIn opportunities require review
- File operations are auto-approved
```

---

## Troubleshooting

### Gmail Watcher Issues

**"Credentials not found"**
```bash
# Ensure credentials.json is in project root
dir credentials.json
```

**"Token expired"**
```bash
# Delete token.json and re-authorize
del token.json
python scripts\gmail_watcher.py AI_Employee_Vault 120
```

### LinkedIn Watcher Issues

**"Browser won't open"**
```bash
# Check Playwright installation
playwright install chromium
```

**"Not logged in"**
- First run requires manual login
- Set `headless=False` temporarily
- Session saved after first login

### Orchestrator Issues

**"Files not processing"**
- Check orchestrator is running
- Review logs: `AI_Employee_Vault\Logs\orchestrator_*.log`

**"Approval requests not created"**
- Check `Company_Handbook.md` exists
- Verify approval thresholds

---

## File Structure

```
personal-ai-employee-0-heck-2026/
├── AI_Employee_Vault/
│   ├── Inbox/                   # Drop files here
│   ├── Needs_Action/            # New items from watchers
│   ├── Pending_Approval/        # Awaiting human decision ⭐ NEW
│   ├── Approved/                # Approved actions ⭐ NEW
│   ├── Rejected/                # Rejected actions
│   ├── Plans/                   # Processing summaries
│   ├── Done/                    # Completed tasks
│   ├── Logs/                    # System logs
│   ├── Briefings/               # CEO briefings
│   ├── Accounting/              # Bank transactions
│   ├── Dashboard.md             # Real-time status
│   ├── Company_Handbook.md      # Rules of Engagement
│   └── Business_Goals.md        # Q1 2026 Objectives
│
├── scripts/
│   ├── base_watcher.py          # Base watcher class
│   ├── filesystem_watcher.py    # File monitoring (Bronze)
│   ├── gmail_watcher.py         # Gmail API ⭐ NEW
│   ├── linkedin_watcher.py      # LinkedIn Web ⭐ NEW
│   ├── email_mcp_server.py      # Email sending ⭐ NEW
│   ├── orchestrator.py          # Enhanced with HITL ⭐ NEW
│   ├── process_pending.py       # One-time processing
│   └── verify_silver_tier.py    # Verification ⭐ NEW
│
├── credentials.json             # Gmail OAuth ⭐ NEW
├── start.bat                    # Bronze start
├── start_silver.bat             # Silver start ⭐ NEW
├── README.md                    # This file
└── SILVER_TIER_SUMMARY.md       # Detailed docs ⭐ NEW
```

---

## What's New in Silver Tier?

| Feature | Bronze Tier | Silver Tier |
|---------|-------------|-------------|
| Watchers | Filesystem only | **Gmail + LinkedIn + Filesystem** |
| Email | None | **Send via MCP Server** |
| Approval Workflow | Basic | **Full HITL with Pending_Approval** |
| Processing | Auto-all | **Smart approval decisions** |
| LinkedIn | None | **Notification monitoring** |
| Start Script | Basic | **Multi-terminal launcher** |

---

## Next Steps (Gold Tier Upgrade)

To upgrade to Gold Tier, add:

1. **Odoo Accounting Integration**
   - Self-hosted Odoo Community on local/VM
   - MCP server for JSON-RPC APIs
   - Automated invoice/payment tracking

2. **Social Media MCP Servers**
   - Facebook/Instagram integration
   - Twitter (X) integration
   - Auto-posting with approval

3. **Weekly CEO Briefing**
   - Autonomous business audit
   - Revenue analysis from bank transactions
   - Bottleneck identification

4. **Ralph Wiggum Loop**
   - Stop hook for continuous operation
   - Multi-step task completion
   - Error recovery

5. **Cloud Deployment**
   - Deploy to Oracle/AWS VM
   - 24/7 always-on operation
   - Health monitoring & auto-restart

---

## Verification

Run this to verify Silver Tier:

```bash
python scripts\verify_silver_tier.py
```

**Expected output:**
```
============================================================
  SILVER TIER VERIFICATION
============================================================
  [✓] Vault folder structure
  [✓] Watcher scripts (3 found)
  [✓] Gmail credentials
  [✓] HITL Approval Workflow
  [✓] Email MCP Server
  [✓] Plans folder
  ...
  ✓ ALL CHECKS PASSED - SILVER TIER COMPLETE!
============================================================
```

---

## Hackathon Status

- **Tier**: Silver ✅
- **Status**: Complete
- **Verification**: All checks passed
- **Demo Ready**: Yes

### Silver Tier Checklist
- [x] All Bronze Tier requirements
- [x] 2+ Watcher scripts (Gmail, LinkedIn, Filesystem)
- [x] Email MCP Server
- [x] HITL Approval Workflow
- [x] Plan.md Creation
- [x] Scheduling Support
- [x] Verification Script
- [x] Documentation

---

*AI Employee v0.2 (Silver Tier)*
*Generated: 2026-03-14*
