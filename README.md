# Personal AI Employee - Bronze Tier (Qwen Code Edition)

> **Tagline:** Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

**Modified for Qwen Code** - This version auto-processes files without requiring Claude Code.

---

## Quick Start (3 Steps)

### Step 1: Verify Setup

```bash
cd C:\Users\abRahman\Desktop\personal-ai-employee-0-heck-2026
python scripts\verify_bronze_tier.py
```

**Expected output:** `[OK] All Bronze Tier checks passed!`

---

### Step 2: Start the System (2 Terminals)

**Terminal 1** - Start the File System Watcher:
```bash
cd C:\Users\abRahman\Desktop\personal-ai-employee-0-heck-2026
python scripts\filesystem_watcher.py AI_Employee_Vault
```

**Terminal 2** - Start the Orchestrator (with auto-process):
```bash
cd C:\Users\abRahman\Desktop\personal-ai-employee-0-heck-2026
python scripts\orchestrator.py AI_Employee_Vault
```

**What happens:**
- **Watcher** monitors `Inbox/` folder every 5 seconds
- **Orchestrator** auto-processes files every 10 seconds
- Files automatically move: `Inbox` → `Needs_Action` → `Done`

---

### Step 3: Test It!

**Drop a test file:**
```bash
echo "Hello AI Employee, please process this document" > AI_Employee_Vault\Inbox\test.txt
```

**Watch the magic:**

**Terminal 1 (Watcher):**
```
2026-02-26 23:00:00 - FilesystemWatcher - INFO - Found 1 new item(s)
2026-02-26 23:00:00 - FilesystemWatcher - INFO - Created action file: FILE_test.txt.md
```

**Terminal 2 (Orchestrator):**
```
[2026-02-26T23:00:10] [INFO] Found 1 pending item(s) - auto-processing...
[2026-02-26T23:00:10] [INFO] Auto-processing: FILE_test.txt.md
[2026-02-26T23:00:10] [INFO] Moved action file to Done: FILE_test.txt.md
[2026-02-26T23:00:10] [INFO] Auto-processing complete: FILE_test.txt.md
[2026-02-26T23:00:10] [INFO] Dashboard updated
```

**Check the result:**
```bash
# File should now be in Done/
dir AI_Employee_Vault\Done\
```

---

## How It Works (Qwen Code Mode)

### Automatic Workflow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│   Inbox/    │ ──▶ │ Needs_Action │ ──▶ │ Auto-Process│ ──▶ │   Done/  │
│ (drop here) │     │ (action file)│     │ (orchestrator)│   │ (completed)│
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
     │                    │                      │                  │
     │                    │                      │                  │
     ▼                    ▼                      ▼                  ▼
 User drops file    Watcher creates       Orchestrator       Files moved
                    action file +         reads, summarizes,  to Done/
                    copies file           creates summary     automatically
```

### What Gets Auto-Processed?

| File Type | Action | Auto-Approve? |
|-----------|--------|---------------|
| `.txt` documents | Read & summarize | ✅ Yes |
| `.pdf` files | Read content | ✅ Yes |
| `.doc`, `.docx` | Read document | ✅ Yes |
| `.md` notes | Process note | ✅ Yes |
| Any file drop | File operation | ✅ Yes |

### What Requires Manual Review?

| Type | Why |
|------|-----|
| Urgent priority items | Need human decision |
| Payment requests | Per Company_Handbook.md rules |
| External sends | Require approval |

---

## Commands Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `python scripts\verify_bronze_tier.py` | Verify setup | Before starting |
| `python scripts\filesystem_watcher.py AI_Employee_Vault` | Start watcher | Terminal 1 |
| `python scripts\orchestrator.py AI_Employee_Vault` | Start orchestrator (auto) | Terminal 2 |
| `python scripts\orchestrator.py AI_Employee_Vault --no-auto-process` | Manual mode | For Qwen Code review |
| `echo "test" > AI_Employee_Vault\Inbox\file.txt` | Drop a file | Test or real use |

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
notepad AI_Employee_Vault\Logs\orchestrator_2026-02-26.log

# Watcher logs
notepad AI_Employee_Vault\Logs\watcher_2026-02-26.log
```

### Check Processed Files

```bash
# See what's been processed
dir AI_Employee_Vault\Done\

# See processing summaries
dir AI_Employee_Vault\Plans\
```

---

## Stopping the System

Press `Ctrl+C` in both terminals to stop.

---

## Using with Qwen Code (Manual Review Mode)

If you want Qwen Code to review items before processing:

**Start orchestrator in manual mode:**
```bash
python scripts\orchestrator.py AI_Employee_Vault --no-auto-process
```

**Then use Qwen Code:**
```bash
cd AI_Employee_Vault

# Prompt Qwen Code:
"Check the Needs_Action folder for pending items.
Read each action file and the Company_Handbook.md for rules.
Process the items and move completed ones to Done/.
Update the Dashboard.md with what you did."
```

---

## Troubleshooting

### "File not processed"

**Check:** Is orchestrator running with auto-process enabled?

```bash
# Should show: Auto-processing: enabled
python scripts\orchestrator.py AI_Employee_Vault
```

### "Watcher not detecting files"

**Check:** Is watcher running?
```bash
# Should show log output every 5 seconds
python scripts\filesystem_watcher.py AI_Employee_Vault
```

### "Dashboard not updating"

**Check:** Is orchestrator running?
```bash
# Should update dashboard every 10 seconds
python scripts\orchestrator.py AI_Employee_Vault
```

### "Permission denied" errors

**Fix:** Close any files open in other programs (like Notepad) before processing.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT: File Drop                         │
│                    (Inbox/)                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Filesystem Watcher (Python)                    │
│   - Polls Inbox/ every 5 seconds                            │
│   - Detects new files                                       │
│   - Creates action files in Needs_Action/                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Needs_Action/                            │
│   - FILE_example.md (action file with metadata)             │
│   - FILE_example.pdf (copied file)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Orchestrator with Auto-Process                 │
│   - Reads action files                                      │
│   - Auto-processes simple items                             │
│   - Creates processing summaries                            │
│   - Moves files to Done/                                    │
│   - Updates Dashboard.md                                    │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Done/                                    │
│   - Completed action files                                  │
│   - Processed original files                                │
│   - Processing summaries in Plans/                          │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
personal-ai-employee-0-heck-2026/
├── AI_Employee_Vault/
│   ├── Inbox/                   # Drop files here
│   ├── Needs_Action/            # Auto-processed by orchestrator
│   ├── Plans/                   # Processing summaries
│   ├── Done/                    # Completed items
│   ├── Dashboard.md             # Real-time status
│   ├── Company_Handbook.md      # Rules
│   └── Business_Goals.md        # Objectives
│
├── scripts/
│   ├── base_watcher.py          # Base watcher class
│   ├── filesystem_watcher.py    # File monitor
│   ├── orchestrator.py          # Auto-processor (Qwen Code)
│   └── verify_bronze_tier.py    # Verification
│
└── README.md                    # This file
```

---

## What Changed from Claude Code Version?

| Feature | Claude Code Version | Qwen Code Version |
|---------|---------------------|-------------------|
| Processing | Manual (wait for Claude) | **Automatic** |
| Approval | File-based workflow | Auto-approve simple items |
| Dashboard | Updates on manual process | **Updates automatically** |
| File movement | Manual move to Done | **Auto-move to Done** |
| Summaries | Created by Claude | **Created by orchestrator** |

---

## Next Steps (Silver Tier)

To upgrade to Silver Tier:

1. **Gmail Watcher** - Monitor Gmail API
2. **WhatsApp Watcher** - Monitor WhatsApp Web
3. **Email MCP** - Send emails automatically
4. **Qwen Code Integration** - Direct API integration for complex decisions

---

## Verification

Run this to verify everything is working:

```bash
python scripts\verify_bronze_tier.py
```

**Expected output:**
```
=== Personal AI Employee - Bronze Tier Verification ===

1. Vault Structure:
  [OK] AI_Employee_Vault exists
  [OK] Inbox/ folder exists
  ...

============================================================
[OK] All Bronze Tier checks passed!
```

---

*AI Employee v0.1 (Bronze Tier - Qwen Code Edition)*
