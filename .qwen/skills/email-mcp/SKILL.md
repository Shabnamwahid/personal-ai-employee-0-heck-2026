---
name: email-mcp
description: |
  MCP server for sending emails via Gmail API.
  Integrates with Human-in-the-Loop approval workflow.
  Supports attachments, HTML content, and batch sending.
---

# Email MCP Server

Model Context Protocol server for sending emails through Gmail API.

## Prerequisites

1. **Gmail API Setup** (same as gmail-watcher)
2. **Install Dependencies**:
   ```bash
   pip install google-auth google-auth-oauthlib google-api-python-client
   ```

## Configuration

```env
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
VAULT_ROOT=C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault
```

## Usage

### Start MCP Server

```bash
python scripts/email_mcp_server.py --port 8809
```

### Send Email

```bash
python scripts/email_mcp_client.py call -t send_email -p '{"to": "test@example.com", "subject": "Test", "body": "Hello"}'
```

## Available Tools

| Tool | Description |
|------|-------------|
| send_email | Send a single email |
| send_batch | Send bulk emails |
| test_connection | Verify Gmail API access |
| shutdown | Stop the MCP server |

## HITL Integration

Email sending requires approval via the approval workflow.
