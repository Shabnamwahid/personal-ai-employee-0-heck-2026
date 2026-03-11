---
name: process-files
description: |
  Process files in the AI Employee vault's Needs_Action folder.
  Reads pending action files, analyzes content, creates plans,
  and moves completed items to Done folder. Use when you need to
  process incoming files, emails, or tasks in the AI Employee system.
---

# Process Files Agent Skill

This skill enables Claude Code to process files in the AI Employee vault,
following the Bronze Tier architecture for the Personal AI Employee Hackathon.

## Usage

When files appear in `/Needs_Action/`, Claude Code should:

1. **Read** all `.md` files in the Needs_Action folder
2. **Analyze** each file's content and metadata
3. **Create** a plan in `/Plans/` for multi-step tasks
4. **Execute** simple actions directly
5. **Request approval** for sensitive actions (see Company_Handbook.md)
6. **Move** completed items to `/Done/`

## Workflow

### Step 1: Check for Pending Items

```bash
# List files in Needs_Action
ls AI_Employee_Vault/Needs_Action/
```

### Step 2: Read Action Files

```bash
# Read each .md file to understand what needs processing
cat AI_Employee_Vault/Needs_Action/FILE_example.md
```

### Step 3: Analyze and Plan

For each file:
1. Read the frontmatter to understand type and priority
2. Read the content to understand the request
3. Check Company_Handbook.md for approval thresholds
4. Create a plan if multi-step action required

### Step 4: Execute or Request Approval

**Auto-approve actions** (per Company_Handbook.md):
- File operations within vault
- Reply to known contacts
- Recurring payments < $50
- Invoice generation

**Require approval**:
- New payees
- Payments > $100
- External forwards
- New contact replies

### Step 5: Update Dashboard

After processing, update Dashboard.md with:
- Items processed
- Actions taken
- Pending approvals

## Action File Schema

```markdown
---
type: file_drop | email | whatsapp | task
original_name: example.pdf
size: 1024 bytes
received: 2026-02-26T10:30:00Z
status: pending | in_progress | completed
priority: low | normal | high | urgent
---

# Content

## Suggested Actions
- [ ] Action item 1
- [ ] Action item 2
```

## Plan File Template

```markdown
---
created: 2026-02-26T10:30:00Z
status: pending | in_progress | completed
source_file: FILE_example.md
---

# Plan: [Objective]

## Steps
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Approval Required
[ ] Yes - See /Pending_Approval/
[x] No - Auto-approved per Company_Handbook.md

## Notes
[Any relevant context]
```

## Approval Request Template

```markdown
---
type: approval_request
action: [action_type]
created: 2026-02-26T10:30:00Z
status: pending
---

# Approval Required

## Action Details
- **What**: [Description of action]
- **Why**: [Reason for action]
- **When**: [Timing/urgency]

## To Approve
Move this file to `/Approved/` folder

## To Reject
Move this file to `/Rejected/` folder

---
*Created by AI Employee - requires human decision*
```

## Example Processing Flow

### Input: File Dropped

```markdown
---
type: file_drop
original_name: invoice_template.pdf
size: 256 KB
received: 2026-02-26T10:30:00Z
status: pending
---

# File Dropped for Processing

**Original Name:** invoice_template.pdf
**Size:** 256 KB

## Suggested Actions
- [ ] Review document content
- [ ] Extract key information
- [ ] File appropriately
```

### Claude Code Processing

1. Read the file
2. Determine it's an invoice template
3. Create plan: "Process invoice template"
4. Extract key fields from PDF
5. Save extracted data to /Accounting/Templates.md
6. Move original to /Done/
7. Update Dashboard.md

### Output: Plan Created

```markdown
---
created: 2026-02-26T10:31:00Z
status: completed
source_file: FILE_invoice-template.pdf.md
---

# Plan: Process Invoice Template

## Steps
- [x] Read PDF content
- [x] Extract template fields
- [x] Save to /Accounting/Templates.md
- [x] Move to /Done/

## Approval Required
[ ] No - Auto-approved (file operation)

## Notes
Template saved for future invoice generation
```

## Integration with Claude Code

To use this skill with Claude Code:

```bash
# Point Claude Code at the vault
cd AI_Employee_Vault

# Prompt Claude to process files
"Check the Needs_Action folder and process any pending items.
Follow the Company_Handbook.md rules for approval thresholds.
Update the Dashboard.md when complete."
```

## Error Handling

If processing fails:
1. Log the error in the file's frontmatter
2. Move to /Needs_Action/ (keep for manual review)
3. Add `error: true` to frontmatter
4. Update Dashboard with error notice

## Best Practices

1. **Always read Company_Handbook.md** before taking action
2. **Log everything** - add entries to /Logs/
3. **Be conservative** - when in doubt, request approval
4. **Update Dashboard** after each processing cycle
5. **Preserve original files** - copy, don't move

## Related Files

- `../AI_Employee_Vault/Company_Handbook.md` - Rules of Engagement
- `../AI_Employee_Vault/Dashboard.md` - Status overview
- `../AI_Employee_Vault/Business_Goals.md` - Objectives
- `../scripts/orchestrator.py` - Automation script
