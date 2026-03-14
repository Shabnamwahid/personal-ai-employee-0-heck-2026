---
name: hitl-approval
description: |
  Human-in-the-Loop approval workflow for sensitive actions.
  Creates approval requests, waits for human decision,
  and triggers execution upon approval.
---

# HITL Approval Workflow

Human oversight for sensitive AI actions.

## When Approval Required

- Sending emails to new contacts
- Payments over $100
- Social media posts
- File deletions

## Approval File Schema

```markdown
---
type: approval_request
action: send_email
to: client@example.com
subject: Invoice #1234
created: 2026-01-07T10:30:00Z
expires: 2026-01-08T10:30:00Z
status: pending
---

## Action Details

**Action:** Send Email
**To:** client@example.com
**Subject:** Invoice #1234

## To Approve
Move this file to Approved/ folder.

## To Reject
Move this file to Rejected/ folder.
```

## Usage

1. AI creates file in Pending_Approval/
2. Human reviews and moves to Approved/ or Rejected/
3. Orchestrator executes approved actions
