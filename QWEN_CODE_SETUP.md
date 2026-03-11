# AI Employee - Qwen Code Setup Guide

## Problem Fixed! ✅

The system was waiting for Claude Code, but now it's been modified to work with **auto-processing** for Qwen Code.

---

## What Changed?

### Before (Claude Code Version)
- ❌ Files stayed in `Needs_Action/` forever
- ❌ System waited for manual Claude Code intervention
- ❌ Nothing moved to `Done/` automatically

### After (Qwen Code Version)
- ✅ Files auto-processed by orchestrator
- ✅ Files automatically move: `Inbox` → `Needs_Action` → `Done`
- ✅ Dashboard updates automatically
- ✅ Processing summaries created automatically

---

## Quick Start (Easy Way)

### Option 1: Use the Start Script (Recommended)

**Double-click:**
```
start.bat
```

This opens both terminals automatically!

### Option 2: Manual Start (2 Terminals)

**Terminal 1:**
```bash
cd C:\Users\abRahman\Desktop\personal-ai-employee-0-heck-2026
python scripts\filesystem_watcher.py AI_Employee_Vault
```

**Terminal 2:**
```bash
cd C:\Users\abRahman\Desktop\personal-ai-employee-0-heck-2026
python scripts\orchestrator.py AI_Employee_Vault
```

---

## Test It Works

**Drop a test file:**
```bash
echo This is a test document > AI_Employee_Vault\Inbox\mydoc.txt
```

**You should see in Terminal 1 (Watcher):**
```
2026-02-27 01:20:00 - FilesystemWatcher - INFO - Found 1 new item(s)
2026-02-27 01:20:00 - FilesystemWatcher - INFO - Created action file: FILE_mydoc.txt.md
```

**You should see in Terminal 2 (Orchestrator):**
```
[2026-02-27T01:20:10] [INFO] Found 1 pending item(s) - auto-processing...
[2026-02-27T01:20:10] [INFO] Auto-processing: FILE_mydoc.txt.md
[2026-02-27T01:20:10] [INFO] Read associated file: mydoc.txt
[2026-02-27T01:20:10] [INFO] Moved action file to Done: FILE_mydoc.txt.md
[2026-02-27T01:20:10] [INFO] Auto-processing complete: FILE_mydoc.txt.md
[2026-02-27T01:20:10] [INFO] Dashboard updated
```

**Check the result:**
```bash
# File should be in Done/
dir AI_Employee_Vault\Done\

# Output should show:
# FILE_mydoc.txt.md
# mydoc.txt
```

---

## Commands You Need to Know

| Command | What It Does |
|---------|--------------|
| `start.bat` | Starts both Watcher and Orchestrator |
| `python scripts\verify_bronze_tier.py` | Checks everything is set up correctly |
| `python scripts\process_pending.py` | Processes all pending items now (one-time) |
| `dir AI_Employee_Vault\Done\` | See processed files |
| `dir AI_Employee_Vault\Plans\` | See processing summaries |

---

## How to Use Daily

### 1. Start the System

Double-click `start.bat` (keeps both processes running)

### 2. Drop Files to Process

Put any file in `AI_Employee_Vault\Inbox\`:
- Documents (`.txt`, `.doc`, `.docx`, `.pdf`)
- Notes (`.md`)
- Any other file type

### 3. Watch It Process Automatically

Within 10 seconds:
- File detected by Watcher
- Action file created in `Needs_Action/`
- Orchestrator auto-processes it
- Files moved to `Done/`
- Summary created in `Plans/`
- Dashboard updated

### 4. Check Results

Open Obsidian and view:
- `Dashboard.md` - See status
- `Plans/` folder - See processing summaries
- `Done/` folder - See completed files

---

## Processing Modes

### Auto-Process Mode (Default)
```bash
python scripts\orchestrator.py AI_Employee_Vault
```
- Automatically processes all simple files
- No manual intervention needed
- Best for daily use

### Manual Mode (For Qwen Code Review)
```bash
python scripts\orchestrator.py AI_Employee_Vault --no-auto-process
```
- Waits for Qwen Code to review items
- Use when you want AI to analyze before processing

---

## Troubleshooting

### "Files not processing"

**Check:** Is Orchestrator running?
```bash
python scripts\orchestrator.py AI_Employee_Vault
```

### "Watcher not detecting files"

**Check:** Is Watcher running?
```bash
python scripts\filesystem_watcher.py AI_Employee_Vault
```

### "Permission denied"

**Fix:** Close the file in any other program (Notepad, Word, etc.)

### Want to process files RIGHT NOW without waiting?

**Run:**
```bash
python scripts\process_pending.py
```

---

## What Gets Auto-Processed?

| ✅ Auto-Approved | ❌ Requires Review |
|------------------|-------------------|
| File drops | Urgent priority items |
| Document reading | Payment requests |
| Analysis tasks | External sends |
| Moving to Done | New contact communications |

---

## Verify Everything Works

```bash
python scripts\verify_bronze_tier.py
```

**Expected output:**
```
=== Personal AI Employee - Bronze Tier Verification ===

1. Vault Structure:
  [OK] AI_Employee_Vault exists
  [OK] Inbox/ folder exists
  [OK] Needs_Action/ folder exists
  ...

============================================================
[OK] All Bronze Tier checks passed!
```

---

## Architecture (How It Works)

```
User drops file in Inbox/
        ↓
Watcher detects (5 sec)
        ↓
Creates action file in Needs_Action/
        ↓
Orchestrator reads (10 sec)
        ↓
Auto-processes (reads file, creates summary)
        ↓
Moves to Done/ + Updates Dashboard
```

**Total time:** ~15 seconds from drop to completion!

---

## Files Modified for Qwen Code

| File | Change |
|------|--------|
| `scripts/orchestrator.py` | Added auto-processing logic |
| `README.md` | Updated for Qwen Code instructions |
| `start.bat` | New quick-start script |
| `scripts/process_pending.py` | New instant-process script |

---

## Next Steps

1. **Start the system:** Double-click `start.bat`
2. **Drop a test file:** `echo test > AI_Employee_Vault\Inbox\test.txt`
3. **Watch it process:** Check Terminal 2 output
4. **Verify:** `dir AI_Employee_Vault\Done\`

---

*AI Employee v0.1 (Bronze Tier - Qwen Code Edition)*
*Modified: 2026-02-27*
