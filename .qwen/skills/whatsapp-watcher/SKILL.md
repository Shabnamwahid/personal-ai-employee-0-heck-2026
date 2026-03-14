---
name: whatsapp-watcher
description: |
  Monitor WhatsApp Web for new messages and create action files in Obsidian vault.
  Uses Playwright to automate WhatsApp Web and extract messages.
  Use for lead capture, customer support, and personal communication tracking.
---

# WhatsApp Watcher

Python script that monitors WhatsApp Web for new messages and creates actionable Markdown files in your Obsidian vault.

## Prerequisites

1. **Install Dependencies**:
   ```bash
   pip install playwright python-dotenv
   playwright install
   ```

2. **WhatsApp Web Session**:
   - First run will require QR code scan
   - Session saved for subsequent runs

## Configuration

Create .env file in the skill directory:

```env
# Vault paths
VAULT_ROOT=C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault
NEEDS_ACTION_FOLDER=Needs_Action

# Watcher settings
POLL_INTERVAL=120  # seconds (WhatsApp rate-limited)
SESSION_PATH=./whatsapp_session
KEYWORD_FILTERS=pricing,invoice,interested,buy,purchase
```

## Usage

### Start Watcher

```bash
# Run in foreground (testing)
python scripts/whatsapp_watcher.py

# Run as daemon (production)
pm2 start scripts/whatsapp_watcher.py --name whatsapp-watcher --interpreter python
```

### Stop Watcher

```bash
# If running with PM2
pm2 stop whatsapp-watcher
```

## Action File Schema

```markdown
---
type: whatsapp
from: +1234567890
contact_name: John Doe
received: 2026-01-07T10:30:00Z
priority: high
status: pending
chat_id: unique-chat-id
keywords: pricing, interested
---

## Message Content

**Contact:** John Doe (+1234567890)

**Message:** Hi, I'm interested in your services. Can you send me pricing information?

**Timestamp:** 2026-01-07 10:30:00

---

## Suggested Actions

- [ ] Reply with pricing information
- [ ] Schedule follow-up call
- [ ] Add to CRM
