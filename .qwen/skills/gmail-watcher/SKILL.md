---
name: gmail-watcher
description: |
  Monitor Gmail for new emails and create action files in Obsidian vault.
  Watches specified labels/folders and triggers Claude Code processing for new messages.
  Use for email triage, lead capture, invoice requests, and client communication.
---

# Gmail Watcher

Lightweight Python script that monitors Gmail for new messages and creates actionable Markdown files in your Obsidian vault.

## Prerequisites

1. **Gmail API Setup**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download credentials.json

2. **Install Dependencies**:
   ```bash
   pip install google-auth google-auth-oauthlib google-api-python-client python-dotenv
   ```

3. **Initial Authentication**:
   ```bash
   python scripts/gmail_watcher.py --auth
   ```
   This creates token.json for subsequent API calls.

## Configuration

Create .env file in the skill directory:

```env
# Gmail API credentials
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REDIRECT_URI=http://localhost:8080

# Vault paths
VAULT_ROOT=C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault
INBOX_FOLDER=Inbox
NEEDS_ACTION_FOLDER=Needs_Action

# Watcher settings
POLL_INTERVAL=60  # seconds
LABELS_TO_WATCH=INBOX,IMPORTANT,UNREAD
MAX_RESULTS_PER_POLL=10
```

## Usage

### Start Watcher

```bash
# Run in foreground (testing)
python scripts/gmail_watcher.py

# Run as daemon (production)
pm2 start scripts/gmail_watcher.py --name gmail-watcher --interpreter python
```

### Stop Watcher

```bash
# If running with PM2
pm2 stop gmail-watcher

# If running in foreground
Ctrl+C
```

## Action File Schema

Generated files follow this schema:

```markdown
---
type: email
from: sender@example.com
subject: Invoice Request
received: 2026-01-07T10:30:00Z
priority: high
status: pending
message_id: unique-gmail-id
labels: INBOX, IMPORTANT
---

## Email Content

{full message body}

## Attachments
- invoice.pdf (if any)

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
```

## Verification

```bash
# Check watcher is running
pm2 status gmail-watcher

# View logs
pm2 logs gmail-watcher

# Test Gmail API connection
python scripts/gmail_watcher.py --test
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| token.json not created | Run --auth flag to re-authenticate |
| No emails detected | Check LABELS_TO_WATCH configuration |
| API quota exceeded | Increase POLL_INTERVAL to 300+ seconds |
| Permission denied | Ensure vault folder has write permissions |
| OAuth error | Revoke access and re-authenticate |

## Security Notes

- **Never commit** credentials.json or token.json to version control
- Store secrets in .env file (add to .gitignore)
- Rotate credentials monthly
- Use app-specific passwords if 2FA enabled

## Example Output

```
[2026-01-07 10:30:15] Checking Gmail...
[2026-01-07 10:30:16] Found 2 new messages
[2026-01-07 10:30:17] Created: Needs_Action/EMAIL_invoice_request_2026-01-07.md
[2026-01-07 10:30:18] Created: Needs_Action/EMAIL_client_question_2026-01-07.md
[2026-01-07 10:30:19] State saved. Next poll in 60s.
```
